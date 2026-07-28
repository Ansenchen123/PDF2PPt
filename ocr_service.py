from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

from PIL import Image

from pdf2ppt.models import ProviderOptions
from pdf2ppt.providers.gemini import GeminiProvider


def configure_gemini(api_key: str):
    os.environ["GEMINI_API_KEY"] = api_key


def extract_text_and_coords(image_path: str) -> List[Dict[str, Any]]:
    with Image.open(image_path) as image:
        image_size = image.size
    result = GeminiProvider().extract_layout(
        image_path=Path(image_path),
        page_number=1,
        image_size=image_size,
        options=ProviderOptions(provider="gemini"),
    )
    return [
        {
            "text": block.text,
            "box_2d": block.box_2d,
            "style": block.style.model_dump(),
            "confidence": block.confidence,
        }
        for block in result.text_blocks
    ]
