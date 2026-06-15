from pathlib import Path

import pytest

from pdf2ppt.geometry import bbox_to_pixels, bbox_to_slide_units
from pdf2ppt.models import BoundingBox, ProviderOptions, ProviderResult, TextBlock
from pdf2ppt.providers.mock import MockProvider


def test_bounding_box_rejects_reversed_coordinates():
    with pytest.raises(ValueError):
        BoundingBox(y_min=500, x_min=10, y_max=100, x_max=900)


def test_text_block_accepts_legacy_box_2d_payload():
    block = TextBlock(id="a", text="Revenue", box_2d=[100, 200, 300, 800])

    assert block.bbox.y_min == 100
    assert block.bbox.x_min == 200
    assert block.box_2d == [100.0, 200.0, 300.0, 800.0]


def test_bbox_to_pixels_clamps_to_image_bounds():
    bbox = BoundingBox(y_min=-20, x_min=100, y_max=1100, x_max=1200)

    assert bbox_to_pixels(bbox, width=1920, height=1080) == (192, 0, 1920, 1080)


def test_bbox_to_slide_units_uses_normalized_coordinates():
    bbox = BoundingBox(y_min=250, x_min=250, y_max=750, x_max=750)

    assert bbox_to_slide_units(bbox, slide_width=1000, slide_height=500) == (
        250,
        125,
        500,
        250,
    )


def test_mock_provider_returns_valid_provider_result(tmp_path: Path):
    image_path = tmp_path / "page.png"
    image_path.write_bytes(b"not-a-real-image-for-mock-provider")
    provider = MockProvider()

    result = provider.extract_layout(
        image_path=image_path,
        page_number=1,
        image_size=(1600, 900),
        options=ProviderOptions(provider="mock", model="mock-layout-v1"),
    )

    assert isinstance(result, ProviderResult)
    assert result.provider == "mock"
    assert result.page_number == 1
    assert result.text_blocks
    assert result.text_blocks[0].style.font_size_pt > 0
