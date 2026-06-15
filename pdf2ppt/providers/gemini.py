from __future__ import annotations

from pathlib import Path
from typing import Any

from pdf2ppt.config import get_provider_api_key
from pdf2ppt.models import ProviderOptions, ProviderResult
from pdf2ppt.providers.base import LayoutProvider, ProviderError
from pdf2ppt.providers.common import (
    LAYOUT_PROMPT,
    coerce_provider_result,
    extract_json_payload,
    image_mime_type,
    image_to_base64,
    layout_json_schema,
    post_json,
)


class GeminiProvider(LayoutProvider):
    name = "gemini"
    default_model = "gemini-3.5-flash"

    def build_payload(self, image_path: Path, options: ProviderOptions) -> dict[str, Any]:
        return {
            "contents": [
                {
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": image_mime_type(image_path),
                                "data": image_to_base64(image_path),
                            }
                        },
                        {"text": LAYOUT_PROMPT},
                    ]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "response_schema": layout_json_schema(),
            },
        }

    def extract_layout(
        self,
        image_path: Path,
        page_number: int,
        image_size: tuple[int, int],
        options: ProviderOptions,
    ) -> ProviderResult:
        _ = image_size
        model = options.model or self.default_model
        api_key = get_provider_api_key(self.name, options.api_key)
        if not api_key:
            raise ProviderError("GEMINI_API_KEY is not configured")
        payload = self.build_payload(image_path, options)
        body, duration_ms, request_id = post_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            {"x-goog-api-key": api_key, "Content-Type": "application/json"},
            payload,
            options.timeout_seconds,
        )
        text = _extract_gemini_text(body)
        return coerce_provider_result(
            self.name,
            model,
            page_number,
            extract_json_payload(text),
            request_id=request_id,
            duration_ms=duration_ms,
        )


def _extract_gemini_text(body: dict[str, Any]) -> str:
    candidates = body.get("candidates") or []
    for candidate in candidates:
        parts = candidate.get("content", {}).get("parts", [])
        for part in parts:
            if isinstance(part.get("text"), str):
                return part["text"]
    raise ProviderError("Gemini response did not contain text")
