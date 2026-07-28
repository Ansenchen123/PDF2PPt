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
    image_to_data_url,
    layout_json_schema,
    post_json,
)


class OpenAIProvider(LayoutProvider):
    name = "openai"
    default_model = "gpt-5.5"

    def build_payload(self, image_path: Path, options: ProviderOptions) -> dict[str, Any]:
        model = options.model or self.default_model
        return {
            "model": model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": "You reconstruct editable slide layouts."}],
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "input_image", "image_url": image_to_data_url(image_path), "detail": "high"},
                        {"type": "input_text", "text": LAYOUT_PROMPT},
                    ],
                },
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "slide_layout",
                    "strict": True,
                    "schema": layout_json_schema(),
                }
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
        api_key = get_provider_api_key(self.name, options.api_key)
        if not api_key:
            raise ProviderError("OPENAI_API_KEY is not configured")
        payload = self.build_payload(image_path, options)
        body, duration_ms, request_id = post_json(
            "https://api.openai.com/v1/responses",
            {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            payload,
            options.timeout_seconds,
        )
        text = _extract_openai_text(body)
        return coerce_provider_result(
            self.name,
            payload["model"],
            page_number,
            extract_json_payload(text),
            request_id=request_id,
            duration_ms=duration_ms,
        )


def _extract_openai_text(body: dict[str, Any]) -> str:
    if isinstance(body.get("output_text"), str):
        return body["output_text"]
    for item in body.get("output", []):
        for content in item.get("content", []):
            if isinstance(content.get("text"), str):
                return content["text"]
    raise ProviderError("OpenAI response did not contain output text")
