from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from PIL import Image

from pdf2ppt.models import SlideLayout, TextBlock
from pdf2ppt.pptx_export import create_pptx


def create_ppt(slides_data: List[Dict[str, Any]], output_ppt_path: str):
    layouts: list[SlideLayout] = []
    for index, slide_info in enumerate(slides_data, start=1):
        background = Path(slide_info["clean_image_path"])
        with Image.open(background) as image:
            width_px, height_px = image.size
        width_pt = 800.0
        height_pt = width_pt * (height_px / width_px)
        blocks = [
            TextBlock.model_validate({**block, "id": str(i), "source": block.get("source", "vision")})
            for i, block in enumerate(slide_info.get("text_blocks", []))
            if block.get("text") and (block.get("bbox") or block.get("box_2d"))
        ]
        layouts.append(
            SlideLayout(
                page_number=index,
                width_pt=width_pt,
                height_pt=height_pt,
                background_image_path=background,
                clean_background_path=background,
                text_blocks=blocks,
            )
        )
    create_pptx(layouts, output_ppt_path)
