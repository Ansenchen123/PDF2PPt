from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from pdf2ppt.models import ProviderOptions, ProviderResult


class ProviderError(RuntimeError):
    """Raised when a provider cannot return a valid layout result."""

    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class LayoutProvider(ABC):
    name: str

    @abstractmethod
    def extract_layout(
        self,
        image_path: Path,
        page_number: int,
        image_size: tuple[int, int],
        options: ProviderOptions,
    ) -> ProviderResult:
        """Extract text and style layout for a rendered page image."""
