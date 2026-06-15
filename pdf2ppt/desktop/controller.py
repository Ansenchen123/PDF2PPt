from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QObject, Property, QThread, Signal, Slot
from PySide6.QtWidgets import QFileDialog

from pdf2ppt.config import get_provider_api_key, get_proxy_config, set_provider_api_key
from pdf2ppt.pdf import get_page_count
from pdf2ppt.pipeline import convert_pdf_to_ppt


class ConversionWorker(QObject):
    progressChanged = Signal(int, int, str)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(
        self,
        *,
        pdf_path: str,
        output_path: str,
        provider: str,
        auth_mode: str,
        api_key: str,
        proxy_url: str,
        proxy_token: str,
        start_page: int,
        end_page: int,
    ):
        super().__init__()
        self.pdf_path = pdf_path
        self.output_path = output_path
        self.provider = provider
        self.auth_mode = auth_mode
        self.api_key = api_key
        self.proxy_url = proxy_url
        self.proxy_token = proxy_token
        self.start_page = start_page
        self.end_page = end_page

    @Slot()
    def run(self) -> None:
        try:
            provider_name = "proxy" if self.auth_mode == "proxy" else self.provider
            result = convert_pdf_to_ppt(
                pdf_path=self.pdf_path,
                output_ppt=self.output_path,
                provider_name=provider_name,
                target_provider=self.provider,
                api_key=self.api_key or None,
                proxy_url=self.proxy_url or None,
                proxy_token=self.proxy_token or None,
                start_page=self.start_page,
                end_page=self.end_page,
                callback=self.progressChanged.emit,
                keep_temp=True,
            )
            self.finished.emit(str(result.output_ppt))
        except Exception as exc:
            self.failed.emit(str(exc))


class AppController(QObject):
    pdfPathChanged = Signal()
    outputPathChanged = Signal()
    statusChanged = Signal()
    progressChanged = Signal()
    totalPagesChanged = Signal()
    busyChanged = Signal()
    lastOutputChanged = Signal()
    credentialsChanged = Signal()

    def __init__(self):
        super().__init__()
        self._pdf_path = ""
        self._output_path = ""
        self._status = "Ready"
        self._progress = 0
        self._total_pages = 0
        self._busy = False
        self._last_output = ""
        self._thread: QThread | None = None
        self._worker: ConversionWorker | None = None
        proxy_url, proxy_token = get_proxy_config()
        self._proxy_url = proxy_url or ""
        self._proxy_token = proxy_token or ""

    @Property(str, notify=pdfPathChanged)
    def pdfPath(self) -> str:
        return self._pdf_path

    @Property(str, notify=outputPathChanged)
    def outputPath(self) -> str:
        return self._output_path

    @Property(str, notify=statusChanged)
    def status(self) -> str:
        return self._status

    @Property(int, notify=progressChanged)
    def progress(self) -> int:
        return self._progress

    @Property(int, notify=totalPagesChanged)
    def totalPages(self) -> int:
        return self._total_pages

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=lastOutputChanged)
    def lastOutput(self) -> str:
        return self._last_output

    @Property(str, notify=credentialsChanged)
    def proxyUrl(self) -> str:
        return self._proxy_url

    @Property(str, notify=credentialsChanged)
    def proxyToken(self) -> str:
        return self._proxy_token

    @Slot()
    def selectPdf(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(None, "Select PDF", "", "PDF files (*.pdf)")
        if not filename:
            return
        self._pdf_path = filename
        self.pdfPathChanged.emit()
        if not self._output_path:
            self._output_path = str(Path(filename).with_suffix(".pptx"))
            self.outputPathChanged.emit()
        try:
            self._total_pages = get_page_count(filename)
            self.totalPagesChanged.emit()
            self._set_status(f"Loaded {self._total_pages} pages")
        except Exception as exc:
            self._set_status(f"Could not read PDF: {exc}")

    @Slot()
    def selectOutput(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(None, "Save PowerPoint", self._output_path, "PowerPoint (*.pptx)")
        if filename:
            if not filename.lower().endswith(".pptx"):
                filename += ".pptx"
            self._output_path = filename
            self.outputPathChanged.emit()

    @Slot(str, result=str)
    def loadApiKey(self, provider: str) -> str:
        return get_provider_api_key(provider) or ""

    @Slot(str, str)
    def saveApiKey(self, provider: str, api_key: str) -> None:
        if api_key.strip():
            set_provider_api_key(provider, api_key.strip())
            self._set_status(f"Saved {provider} API key")

    @Slot(str, str)
    def updateProxy(self, proxy_url: str, proxy_token: str) -> None:
        self._proxy_url = proxy_url.strip()
        self._proxy_token = proxy_token.strip()
        self.credentialsChanged.emit()

    @Slot(str, str, int, int, str, str)
    def startConversion(
        self,
        provider: str,
        auth_mode: str,
        start_page: int,
        end_page: int,
        api_key: str,
        output_path: str,
    ) -> None:
        if self._busy:
            return
        if not self._pdf_path or not Path(self._pdf_path).exists():
            self._set_status("Select a valid PDF first")
            return
        if output_path.strip():
            self._output_path = output_path.strip()
            self.outputPathChanged.emit()
        if not self._output_path:
            self._set_status("Choose an output file")
            return
        if end_page < start_page:
            self._set_status("End page must be after start page")
            return
        if auth_mode == "byok" and provider != "mock" and not api_key.strip() and not get_provider_api_key(provider):
            self._set_status(f"Missing {provider} API key")
            return
        if auth_mode == "proxy" and (not self._proxy_url or not self._proxy_token):
            self._set_status("Proxy URL and token are required")
            return

        self._set_busy(True)
        self._progress = 0
        self.progressChanged.emit()
        self._set_status("Starting conversion")

        self._thread = QThread()
        self._worker = ConversionWorker(
            pdf_path=self._pdf_path,
            output_path=self._output_path,
            provider=provider,
            auth_mode=auth_mode,
            api_key=api_key.strip(),
            proxy_url=self._proxy_url,
            proxy_token=self._proxy_token,
            start_page=start_page,
            end_page=end_page,
        )
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progressChanged.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    @Slot()
    def openOutputFolder(self) -> None:
        if self._last_output:
            os.startfile(str(Path(self._last_output).parent))

    @Slot(int, int, str)
    def _on_progress(self, current: int, total: int, message: str) -> None:
        if total > 0:
            self._progress = round((current / total) * 100)
            self.progressChanged.emit()
        self._set_status(message)

    @Slot(str)
    def _on_finished(self, output_path: str) -> None:
        self._last_output = output_path
        self.lastOutputChanged.emit()
        self._set_busy(False)
        self._progress = 100
        self.progressChanged.emit()
        self._set_status(f"Completed: {Path(output_path).name}")

    @Slot(str)
    def _on_failed(self, message: str) -> None:
        self._set_busy(False)
        self._set_status(f"Failed: {message}")

    def _set_status(self, status: str) -> None:
        self._status = status
        self.statusChanged.emit()

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.busyChanged.emit()
