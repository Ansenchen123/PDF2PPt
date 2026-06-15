from __future__ import annotations

import sys
from pathlib import Path


def run() -> int:
    try:
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QGuiApplication
        from PySide6.QtQml import QQmlApplicationEngine
    except ImportError as exc:
        raise RuntimeError(
            "PySide6 is required for the commercial desktop app. Install dependencies with "
            "`python -m pip install -r requirements.txt`."
        ) from exc

    from pdf2ppt.desktop.controller import AppController

    app = QGuiApplication(sys.argv)
    app.setApplicationDisplayName("PDF2PPt Studio")
    app.setOrganizationName("PDF2PPt")

    engine = QQmlApplicationEngine()
    controller = AppController()
    engine.rootContext().setContextProperty("appController", controller)
    qml_path = Path(__file__).parent / "ui" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    if not engine.rootObjects():
        return 1
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(run())
