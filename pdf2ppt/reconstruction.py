from __future__ import annotations

from pathlib import Path

from pdf2ppt.models import SlideLayout, TextBlock


def build_slide_layout(
    page_number: int,
    width_pt: float,
    height_pt: float,
    image_path: str | Path,
    provider_blocks: list[TextBlock],
    native_blocks: list[TextBlock],
    warnings: list[str] | None = None,
) -> SlideLayout:
    chosen_blocks = native_blocks if native_blocks else provider_blocks
    layout_warnings = list(warnings or [])
    if native_blocks:
        layout_warnings.append("Used native PDF text spans.")
    elif provider_blocks:
        layout_warnings.append("Used multimodal provider layout extraction.")
    else:
        layout_warnings.append("No text blocks found for this page.")

    return SlideLayout(
        page_number=page_number,
        width_pt=width_pt,
        height_pt=height_pt,
        background_image_path=Path(image_path),
        text_blocks=chosen_blocks,
        warnings=layout_warnings,
    )
