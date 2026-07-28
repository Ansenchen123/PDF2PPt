from __future__ import annotations

from pathlib import Path

from pdf2ppt.models import BoundingBox, ProviderOptions, ProviderResult, TextBlock, TextStyle
from pdf2ppt.providers.base import LayoutProvider


class MockProvider(LayoutProvider):
    name = "mock"

    def extract_layout(
        self,
        image_path: Path,
        page_number: int,
        image_size: tuple[int, int],
        options: ProviderOptions,
    ) -> ProviderResult:
        _ = image_path, image_size
        model = options.model or "mock-layout-v1"
        return ProviderResult(
            provider=self.name,
            model=model,
            page_number=page_number,
            text_blocks=[
                TextBlock(
                    id=f"p{page_number}-title",
                    text=f"Slide {page_number}",
                    bbox=BoundingBox(y_min=70, x_min=80, y_max=160, x_max=920),
                    style=TextStyle(font_size_pt=34, bold=True, alignment="center"),
                    confidence=0.99,
                    source="mock",
                ),
                TextBlock(
                    id=f"p{page_number}-body",
                    text="Editable reconstruction preview",
                    bbox=BoundingBox(y_min=710, x_min=110, y_max=790, x_max=890),
                    style=TextStyle(font_size_pt=18, color_hex="#374151", alignment="center"),
                    confidence=0.95,
                    source="mock",
                ),
            ],
        )
