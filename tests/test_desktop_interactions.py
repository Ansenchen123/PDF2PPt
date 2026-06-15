import os
from pathlib import Path

import fitz
import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication

from pdf2ppt.desktop import controller as controller_module
from pdf2ppt.desktop.controller import AppController


@pytest.fixture(scope="module")
def qapp():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance() or QApplication([])
    return app


def _make_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=320, height=180)
    page.insert_text((40, 80), "Button test", fontsize=20)
    doc.save(path)
    doc.close()


def test_select_pdf_button_slot_loads_pdf_without_crashing(tmp_path: Path, monkeypatch, qapp):
    pdf_path = tmp_path / "button.pdf"
    _make_pdf(pdf_path)
    app = AppController()
    monkeypatch.setattr(
        controller_module.QFileDialog,
        "getOpenFileName",
        lambda *_args, **_kwargs: (str(pdf_path), "PDF files (*.pdf)"),
    )

    app.selectPdf()

    assert app.pdfPath == str(pdf_path)
    assert app.outputPath.endswith("button.pptx")
    assert app.totalPages == 1
    assert "Loaded 1 pages" in app.status


def test_start_conversion_button_slot_reports_missing_pdf_without_crashing(qapp):
    app = AppController()

    app.startConversion("mock", "byok", 1, 1, "", "")

    assert app.status == "Select a valid PDF first"


def test_start_conversion_button_slot_runs_mock_conversion(tmp_path: Path, monkeypatch, qapp, qtbot):
    pdf_path = tmp_path / "convert.pdf"
    output_path = tmp_path / "convert.pptx"
    _make_pdf(pdf_path)
    app = AppController()
    monkeypatch.setattr(
        controller_module.QFileDialog,
        "getOpenFileName",
        lambda *_args, **_kwargs: (str(pdf_path), "PDF files (*.pdf)"),
    )

    app.selectPdf()
    app.startConversion("mock", "byok", 1, 1, "", str(output_path))

    qtbot.waitUntil(lambda: not app.busy, timeout=30000)
    assert output_path.exists()
    assert app.lastOutput == str(output_path)
    assert app.status.startswith("Completed:")
