from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from pdf2ppt.models import QualityReport, SlideLayout


def compute_image_similarity(image_a: str | Path, image_b: str | Path) -> float:
    first = _load_grayscale(image_a)
    second = _load_grayscale(image_b)
    if first.shape != second.shape:
        second = np.array(Image.fromarray(second).resize((first.shape[1], first.shape[0])))
    if np.array_equal(first, second):
        return 1.0
    try:
        from skimage.metrics import structural_similarity

        score = structural_similarity(first, second, data_range=255)
        return float(max(0.0, min(1.0, score)))
    except Exception:
        diff = np.mean(np.abs(first.astype(np.float32) - second.astype(np.float32))) / 255.0
        return float(max(0.0, min(1.0, 1.0 - diff)))


def summarize_layout_quality(layout: SlideLayout) -> QualityReport:
    return QualityReport(
        page_number=layout.page_number,
        text_block_count=len(layout.text_blocks),
        low_confidence_blocks=sum(1 for block in layout.text_blocks if block.confidence < 0.65),
        warnings=layout.warnings,
    )


def _load_grayscale(path: str | Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.array(image.convert("L"))
