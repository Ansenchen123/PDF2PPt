from __future__ import annotations

from pathlib import Path
from typing import List

import fitz

from pdf2ppt.pdf import get_page_count, render_pdf_pages


def pdf_to_images(
    pdf_path: str,
    output_folder: str = "output_images",
    zoom: int = 2,
    start_page: int = 1,
    end_page: int | None = None,
) -> List[str]:
    pages = render_pdf_pages(
        Path(pdf_path),
        Path(output_folder),
        zoom=zoom,
        start_page=start_page,
        end_page=end_page,
    )
    return [str(page.image_path) for page in pages]


def get_pdf_dims(pdf_path: str) -> tuple[float, float]:
    doc = fitz.open(pdf_path)
    try:
        page = doc.load_page(0)
        rect = page.rect
        return rect.width, rect.height
    finally:
        doc.close()
