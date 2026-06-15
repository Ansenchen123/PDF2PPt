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


class MistralProvider(LayoutProvider):
    name = "mistral"
    default_model = "mistral-large-2512"

    def build_payload(self, image_path: Path, options: ProviderOptions) -> dict[str, Any]:
        model = options.model or self.default_model
        return {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": LAYOUT_PROMPT},
                        {"type": "image_url", "image_url": image_to_data_url(image_path)},
                    ],
                }
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "slide_layout",
                    "schema": layout_json_schema(),
                    "strict": True,
                },
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
            raise ProviderError("MISTRAL_API_KEY is not configured")
        payload = self.build_payload(image_path, options)
        body, duration_ms, request_id = post_json(
            "https://api.mistral.ai/v1/chat/completions",
            {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            payload,
            options.timeout_seconds,
        )
        text = _extract_mistral_text(body)
        return coerce_provider_result(
            self.name,
            payload["model"],
            page_number,
            extract_json_payload(text),
            request_id=request_id,
            duration_ms=duration_ms,
        )


def _extract_mistral_text(body: dict[str, Any]) -> str:
    choices = body.get("choices") or []
    for choice in choices:
        message = choice.get("message", {})
        if isinstance(message.get("content"), str):
            return message["content"]
    raise ProviderError("Mistral response did not contain message content")
