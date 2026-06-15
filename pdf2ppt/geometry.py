from __future__ import annotations

from pdf2ppt.models import BoundingBox


def bbox_to_pixels(bbox: BoundingBox, width: int, height: int) -> tuple[int, int, int, int]:
    """Convert a normalized bbox to pixel coordinates as x1, y1, x2, y2."""
    box = bbox.clamped()
    x1 = round((box.x_min / 1000.0) * width)
    y1 = round((box.y_min / 1000.0) * height)
    x2 = round((box.x_max / 1000.0) * width)
    y2 = round((box.y_max / 1000.0) * height)
    return (
        max(0, min(width, x1)),
        max(0, min(height, y1)),
        max(0, min(width, x2)),
        max(0, min(height, y2)),
    )


def bbox_to_slide_units(
    bbox: BoundingBox,
    slide_width: int | float,
    slide_height: int | float,
) -> tuple[int, int, int, int]:
    """Convert a normalized bbox to slide units as left, top, width, height."""
    box = bbox.clamped()
    left = round((box.x_min / 1000.0) * slide_width)
    top = round((box.y_min / 1000.0) * slide_height)
    width = round(((box.x_max - box.x_min) / 1000.0) * slide_width)
    height = round(((box.y_max - box.y_min) / 1000.0) * slide_height)
    return int(left), int(top), max(1, int(width)), max(1, int(height))
