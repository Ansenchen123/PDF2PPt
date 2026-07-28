import os
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from pdf2ppt.config import load_environment
from pdf2ppt.models import ProviderOptions
from pdf2ppt.providers.base import ProviderError
from pdf2ppt.providers.gemini import GeminiProvider


def _live_tests_enabled() -> bool:
    load_environment()
    return os.getenv("PDF2PPT_LIVE_TESTS") == "1"


@pytest.mark.skipif(not _live_tests_enabled(), reason="Set PDF2PPT_LIVE_TESTS=1 to run paid live provider tests")
def test_gemini_live_smoke_extracts_layout(tmp_path: Path):
    if not os.getenv("GEMINI_API_KEY"):
        pytest.skip("GEMINI_API_KEY is not configured")
    image_path = tmp_path / "slide.png"
    image = Image.new("RGB", (640, 360), "#ffffff")
    draw = ImageDraw.Draw(image)
    draw.text((80, 120), "Live Smoke Test", fill="#111111")
    image.save(image_path)

    try:
        result = GeminiProvider().extract_layout(
            image_path=image_path,
            page_number=1,
            image_size=(640, 360),
            options=ProviderOptions(provider="gemini"),
        )
    except ProviderError as exc:
        if exc.status_code == 429:
            pytest.skip("Gemini live smoke was rate limited by the provider")
        pytest.fail(f"Gemini live smoke failed with sanitized provider error: {exc}")

    assert result.text_blocks
