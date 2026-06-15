from __future__ import annotations

import base64
import json
import mimetypes
import re
import time
from pathlib import Path
from typing import Any

import requests
from pydantic import ValidationError

from pdf2ppt.models import ProviderResult, TextBlock
from pdf2ppt.providers.base import ProviderError


LAYOUT_PROMPT = """Extract every visible text block from this slide image.
Return strict JSON matching the provided schema.
Use normalized 0-1000 coordinates in [y_min, x_min, y_max, x_max] order.
Estimate font_size_pt, color_hex, bold, italic, alignment, and line_spacing.
Do not invent text. Preserve line breaks only when they are visually meaningful.
"""


def layout_json_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["text_blocks", "warnings"],
        "properties": {
            "text_blocks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["id", "text", "box_2d", "style", "confidence"],
                    "properties": {
                        "id": {"type": "string"},
                        "text": {"type": "string"},
                        "box_2d": {
                            "type": "array",
                            "minItems": 4,
                            "maxItems": 4,
                            "items": {"type": "number"},
                        },
                        "style": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": [
                                "font_family",
                                "font_size_pt",
                                "color_hex",
                                "bold",
                                "italic",
                                "alignment",
                                "line_spacing",
                            ],
                            "properties": {
                                "font_family": {"type": "string"},
                                "font_size_pt": {"type": "number"},
                                "color_hex": {"type": "string"},
                                "bold": {"type": "boolean"},
                                "italic": {"type": "boolean"},
                                "alignment": {
                                    "type": "string",
                                    "enum": ["left", "center", "right", "justify"],
                                },
                                "line_spacing": {"type": "number"},
                            },
                        },
                        "confidence": {"type": "number"},
                    },
                },
            },
            "warnings": {"type": "array", "items": {"type": "string"}},
        },
    }


def image_to_base64(path: str | Path) -> str:
    return base64.b64encode(Path(path).read_bytes()).decode("ascii")


def image_to_data_url(path: str | Path) -> str:
    path = Path(path)
    mime_type = mimetypes.guess_type(path.name)[0] or "image/png"
    return f"data:{mime_type};base64,{image_to_base64(path)}"


def image_mime_type(path: str | Path) -> str:
    return mimetypes.guess_type(str(path))[0] or "image/png"


def extract_json_payload(text: str) -> dict[str, Any]:
    text = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", text, flags=re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start : end + 1])
        raise


def coerce_provider_result(
    provider: str,
    model: str,
    page_number: int,
    payload: dict[str, Any],
    *,
    request_id: str | None = None,
    duration_ms: int | None = None,
) -> ProviderResult:
    if "text_blocks" not in payload:
        raise ValueError("Provider payload must include text_blocks")
    warnings = payload.get("warnings") or []
    blocks = [
        TextBlock.model_validate({**block, "source": block.get("source", "vision")})
        for block in payload["text_blocks"]
    ]
    try:
        return ProviderResult(
            provider=provider,
            model=model,
            page_number=page_number,
            text_blocks=blocks,
            warnings=warnings,
            request_id=request_id,
            duration_ms=duration_ms,
        )
    except ValidationError as exc:
        raise ValueError(str(exc)) from exc


def post_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_seconds: float,
) -> tuple[dict[str, Any], int, str | None]:
    started = time.perf_counter()
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout_seconds)
    except requests.RequestException as exc:
        raise ProviderError(f"Provider request failed: {exc.__class__.__name__}") from exc
    duration_ms = round((time.perf_counter() - started) * 1000)
    request_id = response.headers.get("x-request-id") or response.headers.get("request-id")
    if response.status_code >= 400:
        raise ProviderError(f"Provider returned HTTP {response.status_code}")
    try:
        return response.json(), duration_ms, request_id
    except ValueError as exc:
        raise ProviderError("Provider returned non-JSON response") from exc
