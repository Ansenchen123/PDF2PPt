from pathlib import Path


def test_desktop_app_module_imports_without_pyside_runtime():
    import pdf2ppt.desktop.app as app

    assert callable(app.run)


def test_qml_workspace_contains_core_controls():
    qml_path = Path("pdf2ppt/desktop/ui/Main.qml")
    assert qml_path.exists()
    content = qml_path.read_text(encoding="utf-8")

    assert "ApplicationWindow" in content
    assert "providerCombo" in content
    assert "authModeCombo" in content
    assert "Start conversion" in content
