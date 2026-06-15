from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator


class ProviderName(str, Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"
    PROXY = "proxy"
    MOCK = "mock"


class AuthMode(str, Enum):
    BYOK = "byok"
    PROXY = "proxy"


class QualityMode(str, Enum):
    BALANCED = "balanced"
    PRECISE = "precise"
    FAST = "fast"


class BoundingBox(BaseModel):
    """Normalized 0-1000 coordinates in provider order: y_min, x_min, y_max, x_max."""

    model_config = ConfigDict(extra="forbid")

    y_min: float = Field(ge=-1000, le=2000)
    x_min: float = Field(ge=-1000, le=2000)
    y_max: float = Field(ge=-1000, le=2000)
    x_max: float = Field(ge=-1000, le=2000)

    @model_validator(mode="after")
    def validate_order(self) -> "BoundingBox":
        if self.y_max <= self.y_min:
            raise ValueError("y_max must be greater than y_min")
        if self.x_max <= self.x_min:
            raise ValueError("x_max must be greater than x_min")
        return self

    @classmethod
    def from_box_2d(cls, box_2d: list[float] | tuple[float, float, float, float]) -> "BoundingBox":
        if len(box_2d) != 4:
            raise ValueError("box_2d must contain [y_min, x_min, y_max, x_max]")
        return cls(y_min=box_2d[0], x_min=box_2d[1], y_max=box_2d[2], x_max=box_2d[3])

    def clamped(self) -> "BoundingBox":
        return BoundingBox(
            y_min=max(0.0, min(1000.0, self.y_min)),
            x_min=max(0.0, min(1000.0, self.x_min)),
            y_max=max(0.0, min(1000.0, self.y_max)),
            x_max=max(0.0, min(1000.0, self.x_max)),
        )

    @computed_field
    @property
    def box_2d(self) -> list[float]:
        return [self.y_min, self.x_min, self.y_max, self.x_max]


class TextStyle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    font_family: str = "Aptos"
    font_size_pt: float = Field(default=18.0, ge=4.0, le=160.0)
    color_hex: str = "#111827"
    bold: bool = False
    italic: bool = False
    alignment: Literal["left", "center", "right", "justify"] = "left"
    line_spacing: float = Field(default=1.0, ge=0.7, le=2.5)

    @field_validator("color_hex")
    @classmethod
    def validate_color(cls, value: str) -> str:
        if not value.startswith("#") or len(value) != 7:
            raise ValueError("color_hex must be in #RRGGBB format")
        int(value[1:], 16)
        return value.upper()


class TextBlock(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    id: str
    text: str
    bbox: BoundingBox
    style: TextStyle = Field(default_factory=TextStyle)
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    source: Literal["native_pdf", "vision", "ocr", "mock"] = "vision"

    @model_validator(mode="before")
    @classmethod
    def accept_legacy_box_2d(cls, data: Any) -> Any:
        if isinstance(data, dict) and "bbox" not in data and "box_2d" in data:
            data = dict(data)
            data["bbox"] = BoundingBox.from_box_2d(data["box_2d"])
        return data

    @computed_field
    @property
    def box_2d(self) -> list[float]:
        return self.bbox.box_2d


class PageAsset(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_number: int = Field(ge=1)
    image_path: Path
    width_px: int = Field(gt=0)
    height_px: int = Field(gt=0)
    page_width_pt: float = Field(gt=0)
    page_height_pt: float = Field(gt=0)
    clean_image_path: Path | None = None
    mask_path: Path | None = None
    overlay_path: Path | None = None


class ProviderOptions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider: ProviderName | str
    model: str | None = None
    api_key: str | None = None
    proxy_url: str | None = None
    proxy_token: str | None = None
    timeout_seconds: float = Field(default=120.0, gt=0)
    quality_mode: QualityMode = QualityMode.PRECISE


class ProviderResult(BaseModel):
    model_config = ConfigDict(extra="allow")

    provider: ProviderName | str
    model: str
    page_number: int = Field(ge=1)
    text_blocks: list[TextBlock] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    request_id: str | None = None
    duration_ms: int | None = Field(default=None, ge=0)


class SlideLayout(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_number: int = Field(ge=1)
    width_pt: float = Field(gt=0)
    height_pt: float = Field(gt=0)
    background_image_path: Path
    clean_background_path: Path | None = None
    mask_path: Path | None = None
    overlay_path: Path | None = None
    text_blocks: list[TextBlock] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DocumentJob(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pdf_path: Path
    output_ppt: Path
    start_page: int = Field(default=1, ge=1)
    end_page: int | None = None
    provider: ProviderName | str = ProviderName.GEMINI
    provider_model: str | None = None
    auth_mode: AuthMode = AuthMode.BYOK
    quality_mode: QualityMode = QualityMode.PRECISE
    keep_temp: bool = False

    @model_validator(mode="after")
    def validate_pages(self) -> "DocumentJob":
        if self.end_page is not None and self.end_page < self.start_page:
            raise ValueError("end_page must be greater than or equal to start_page")
        return self


class QualityReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_number: int = Field(ge=1)
    text_block_count: int = Field(ge=0)
    low_confidence_blocks: int = Field(ge=0)
    warnings: list[str] = Field(default_factory=list)
