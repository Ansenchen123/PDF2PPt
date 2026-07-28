from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Callable

from pdf2ppt.background import clean_background
from pdf2ppt.models import ConversionResult, ProviderOptions, SlideLayout
from pdf2ppt.pdf import extract_native_text_blocks, render_pdf_pages
from pdf2ppt.pptx_export import create_pptx
from pdf2ppt.providers import get_provider
from pdf2ppt.quality import summarize_layout_quality
from pdf2ppt.reconstruction import build_slide_layout

ProgressCallback = Callable[[int, int, str], None]


def convert_pdf_to_ppt(
    pdf_path: str | Path,
    output_ppt: str | Path,
    provider_name: str = "gemini",
    target_provider: str | None = None,
    provider_model: str | None = None,
    api_key: str | None = None,
    proxy_url: str | None = None,
    proxy_token: str | None = None,
    start_page: int = 1,
    end_page: int | None = None,
    callback: ProgressCallback | None = None,
    keep_temp: bool = False,
) -> ConversionResult:
    pdf_path = Path(pdf_path).expanduser().resolve()
    output_ppt = Path(output_ppt).expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    output_ppt.parent.mkdir(parents=True, exist_ok=True)
    temp_root = Path(tempfile.mkdtemp(prefix="pdf2ppt_", dir=output_ppt.parent))
    image_dir = temp_root / "pages"
    clean_dir = temp_root / "clean"
    mask_dir = temp_root / "masks"
    overlay_dir = temp_root / "overlays"

    try:
        _emit(callback, 0, 0, "Rendering PDF pages")
        pages = render_pdf_pages(pdf_path, image_dir, start_page=start_page, end_page=end_page)
        provider = get_provider(provider_name)
        options = ProviderOptions(
            provider=target_provider or provider_name,
            model=provider_model,
            api_key=api_key,
            proxy_url=proxy_url,
            proxy_token=proxy_token,
        )
        layouts: list[SlideLayout] = []
        reports: list[QualityReport] = []

        for index, page in enumerate(pages, start=1):
            _emit(callback, index, len(pages), f"Analyzing page {page.page_number}")
            native_blocks = extract_native_text_blocks(pdf_path, page.page_number)
            provider_blocks = []
            provider_warnings: list[str] = []
            if not native_blocks:
                provider_result = provider.extract_layout(
                    image_path=page.image_path,
                    page_number=page.page_number,
                    image_size=(page.width_px, page.height_px),
                    options=options,
                )
                provider_blocks = provider_result.text_blocks
                provider_warnings = provider_result.warnings

            layout = build_slide_layout(
                page_number=page.page_number,
                width_pt=page.page_width_pt,
                height_pt=page.page_height_pt,
                image_path=page.image_path,
                provider_blocks=provider_blocks,
                native_blocks=native_blocks,
                warnings=provider_warnings,
            )
            cleanup = clean_background(
                page.image_path,
                layout.text_blocks,
                clean_dir / f"clean_page_{page.page_number}.png",
                mask_dir / f"mask_page_{page.page_number}.png",
                overlay_dir / f"overlay_page_{page.page_number}.png",
            )
            layout.clean_background_path = cleanup.clean_image_path
            layout.mask_path = cleanup.mask_path
            layout.overlay_path = cleanup.overlay_path
            layouts.append(layout)
            reports.append(summarize_layout_quality(layout))

        _emit(callback, len(layouts), len(layouts), "Writing PowerPoint")
        create_pptx(layouts, output_ppt)
        return ConversionResult(output_ppt=output_ppt, layouts=layouts, quality_reports=reports)
    finally:
        if not keep_temp:
            shutil.rmtree(temp_root, ignore_errors=True)


def _emit(callback: ProgressCallback | None, current: int, total: int, message: str) -> None:
    if callback:
        callback(current, total, message)
