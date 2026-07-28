from __future__ import annotations

from pathlib import Path

import fitz

from pdf2ppt.models import BoundingBox, PageAsset, TextBlock, TextStyle


def get_page_count(pdf_path: str | Path) -> int:
    doc = fitz.open(str(pdf_path))
    try:
        return doc.page_count
    finally:
        doc.close()


def render_pdf_pages(
    pdf_path: str | Path,
    output_folder: str | Path,
    zoom: float = 2.0,
    start_page: int = 1,
    end_page: int | None = None,
) -> list[PageAsset]:
    pdf_path = Path(pdf_path)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(str(pdf_path))
    try:
        if start_page < 1:
            raise ValueError("start_page must be 1 or greater")
        if end_page is None or end_page > doc.page_count:
            end_page = doc.page_count
        if end_page < start_page:
            raise ValueError("end_page must be greater than or equal to start_page")

        matrix = fitz.Matrix(zoom, zoom)
        pages: list[PageAsset] = []
        for page_index in range(start_page - 1, end_page):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            image_path = output_folder / f"page_{page_index + 1}.png"
            pix.save(str(image_path))
            rect = page.rect
            pages.append(
                PageAsset(
                    page_number=page_index + 1,
                    image_path=image_path,
                    width_px=pix.width,
                    height_px=pix.height,
                    page_width_pt=float(rect.width),
                    page_height_pt=float(rect.height),
                )
            )
        return pages
    finally:
        doc.close()


def extract_native_text_blocks(pdf_path: str | Path, page_number: int) -> list[TextBlock]:
    doc = fitz.open(str(pdf_path))
    try:
        page = doc.load_page(page_number - 1)
        rect = page.rect
        data = page.get_text("dict")
        blocks: list[TextBlock] = []
        span_index = 0
        for block in data.get("blocks", []):
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = str(span.get("text", "")).strip()
                    if not text:
                        continue
                    x1, y1, x2, y2 = span["bbox"]
                    bbox = BoundingBox(
                        y_min=(y1 / rect.height) * 1000,
                        x_min=(x1 / rect.width) * 1000,
                        y_max=(y2 / rect.height) * 1000,
                        x_max=(x2 / rect.width) * 1000,
                    )
                    color = _fitz_color_to_hex(int(span.get("color", 0)))
                    blocks.append(
                        TextBlock(
                            id=f"p{page_number}-native-{span_index}",
                            text=text,
                            bbox=bbox,
                            style=TextStyle(
                                font_family=str(span.get("font") or "Aptos"),
                                font_size_pt=float(span.get("size") or 12.0),
                                color_hex=color,
                                bold="bold" in str(span.get("font", "")).lower(),
                                italic="italic" in str(span.get("font", "")).lower(),
                            ),
                            confidence=1.0,
                            source="native_pdf",
                        )
                    )
                    span_index += 1
        return blocks
    finally:
        doc.close()


def _fitz_color_to_hex(color: int) -> str:
    red = (color >> 16) & 255
    green = (color >> 8) & 255
    blue = color & 255
    return f"#{red:02X}{green:02X}{blue:02X}"
