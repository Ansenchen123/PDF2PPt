from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from pdf2ppt.geometry import bbox_to_pixels
from pdf2ppt.models import TextBlock


@dataclass(frozen=True)
class BackgroundCleanupResult:
    clean_image_path: Path
    mask_path: Path
    overlay_path: Path | None
    mask_pixels: int
    fallback_blocks: int


def clean_background(
    image_path: str | Path,
    text_blocks: list[TextBlock],
    clean_image_path: str | Path,
    mask_path: str | Path,
    overlay_path: str | Path | None = None,
) -> BackgroundCleanupResult:
    image_path = Path(image_path)
    clean_image_path = Path(clean_image_path)
    mask_path = Path(mask_path)
    overlay = Path(overlay_path) if overlay_path else None
    clean_image_path.parent.mkdir(parents=True, exist_ok=True)
    mask_path.parent.mkdir(parents=True, exist_ok=True)
    if overlay:
        overlay.parent.mkdir(parents=True, exist_ok=True)

    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    height, width = image.shape[:2]
    mask = np.zeros((height, width), dtype=np.uint8)
    fallback_blocks = 0

    for block in text_blocks:
        block_mask, used_fallback = _build_block_mask(image, block)
        mask = cv2.bitwise_or(mask, block_mask)
        if used_fallback:
            fallback_blocks += 1

    if int(mask.sum()) > 0:
        radius = 3
        clean = cv2.inpaint(image, mask, radius, cv2.INPAINT_TELEA)
    else:
        clean = image.copy()

    cv2.imwrite(str(clean_image_path), clean)
    cv2.imwrite(str(mask_path), mask)

    if overlay:
        overlay_img = image.copy()
        overlay_img[mask > 0] = (0, 0, 255)
        blended = cv2.addWeighted(image, 0.72, overlay_img, 0.28, 0)
        cv2.imwrite(str(overlay), blended)

    return BackgroundCleanupResult(
        clean_image_path=clean_image_path,
        mask_path=mask_path,
        overlay_path=overlay,
        mask_pixels=int(np.count_nonzero(mask)),
        fallback_blocks=fallback_blocks,
    )


def _build_block_mask(image: np.ndarray, block: TextBlock) -> tuple[np.ndarray, bool]:
    height, width = image.shape[:2]
    x1, y1, x2, y2 = bbox_to_pixels(block.bbox, width=width, height=height)
    pad = max(2, round(block.style.font_size_pt / 6))
    x1 = max(0, x1 - pad)
    y1 = max(0, y1 - pad)
    x2 = min(width, x2 + pad)
    y2 = min(height, y2 + pad)
    block_mask = np.zeros((height, width), dtype=np.uint8)
    if x2 <= x1 or y2 <= y1:
        return block_mask, True

    roi = image[y1:y2, x1:x2]
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    edges = cv2.Canny(blurred, 40, 120)
    _, dark = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    _, light = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    dark_ratio = np.count_nonzero(dark) / dark.size
    light_ratio = np.count_nonzero(light) / light.size
    text_candidate = dark if dark_ratio <= light_ratio else light
    roi_mask = cv2.bitwise_or(text_candidate, edges)

    min_pixels = max(8, int(roi_mask.size * 0.003))
    used_fallback = np.count_nonzero(roi_mask) < min_pixels
    if used_fallback:
        roi_mask[:, :] = 255

    kernel_size = max(2, min(9, round(block.style.font_size_pt / 12)))
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    roi_mask = cv2.dilate(roi_mask, kernel, iterations=1)
    block_mask[y1:y2, x1:x2] = roi_mask
    return block_mask, used_fallback
