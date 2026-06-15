from pathlib import Path

from PIL import Image

from pdf2ppt.models import BoundingBox, SlideLayout, TextBlock
from pdf2ppt.quality import compute_image_similarity, summarize_layout_quality


def _write_image(path: Path, color: str) -> None:
    Image.new("RGB", (120, 80), color).save(path)


def test_compute_image_similarity_identical_images(tmp_path: Path):
    image_a = tmp_path / "a.png"
    image_b = tmp_path / "b.png"
    _write_image(image_a, "#ffffff")
    _write_image(image_b, "#ffffff")

    assert compute_image_similarity(image_a, image_b) == 1.0


def test_compute_image_similarity_detects_difference(tmp_path: Path):
    image_a = tmp_path / "a.png"
    image_b = tmp_path / "b.png"
    _write_image(image_a, "#ffffff")
    _write_image(image_b, "#000000")

    assert compute_image_similarity(image_a, image_b) < 0.2


def test_summarize_layout_quality_counts_low_confidence_blocks(tmp_path: Path):
    bg = tmp_path / "bg.png"
    _write_image(bg, "#ffffff")
    layout = SlideLayout(
        page_number=1,
        width_pt=800,
        height_pt=450,
        background_image_path=bg,
        text_blocks=[
            TextBlock(id="a", text="A", bbox=BoundingBox(y_min=0, x_min=0, y_max=100, x_max=100), confidence=0.4),
            TextBlock(id="b", text="B", bbox=BoundingBox(y_min=100, x_min=0, y_max=200, x_max=100), confidence=0.9),
        ],
    )

    report = summarize_layout_quality(layout)

    assert report.text_block_count == 2
    assert report.low_confidence_blocks == 1
