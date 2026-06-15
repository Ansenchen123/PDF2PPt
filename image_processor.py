from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from pdf2ppt.background import clean_background
from pdf2ppt.models import TextBlock


def remove_text_from_image(image_path: str, text_blocks: List[Dict[str, Any]], output_path: str):
    blocks = [
        TextBlock.model_validate({**block, "id": str(index), "source": block.get("source", "vision")})
        for index, block in enumerate(text_blocks)
        if block.get("text") and (block.get("bbox") or block.get("box_2d"))
    ]
    output = Path(output_path)
    return clean_background(
        image_path,
        blocks,
        output,
        output.with_name(output.stem + "_mask.png"),
        output.with_name(output.stem + "_overlay.png"),
    )
