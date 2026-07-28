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


class AnthropicProvider(LayoutProvider):
    name = "anthropic"
    default_model = "claude-sonnet-4-6"

    def build_payload(self, image_path: Path, options: ProviderOptions) -> dict[str, Any]:
        model = options.model or self.default_model
        return {
            "model": model,
            "max_tokens": 4096,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": image_mime_type(image_path),
                                "data": image_to_base64(image_path),
                            },
                        },
                        {"type": "text", "text": LAYOUT_PROMPT},
                    ],
                }
            ],
            "output_config": {
                "format": {
                    "type": "json_schema",
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
            raise ProviderError("ANTHROPIC_API_KEY is not configured")
        payload = self.build_payload(image_path, options)
        body, duration_ms, request_id = post_json(
            "https://api.anthropic.com/v1/messages",
            {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            payload,
            options.timeout_seconds,
        )
        text = _extract_anthropic_text(body)
        return coerce_provider_result(
            self.name,
            payload["model"],
            page_number,
            extract_json_payload(text),
            request_id=request_id,
            duration_ms=duration_ms,
        )


def _extract_anthropic_text(body: dict[str, Any]) -> str:
    for content in body.get("content", []):
        if content.get("type") == "text" and isinstance(content.get("text"), str):
            return content["text"]
    raise ProviderError("Anthropic response did not contain text")
