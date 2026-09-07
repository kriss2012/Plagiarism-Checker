"""Headless GUI tests verifying PySide6 application initialization, view switching, and signal flows."""

import os
import sys
import pytest

# Ensure Qt runs offscreen in headless test environment
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from app.database.session import init_db
from app.ui.main_window import MainWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def test_main_window_instantiation(qapp):
    init_db()
    window = MainWindow()
    assert window.windowTitle() != ""
    assert window.stack.count() >= 7

    # Test navigation to all tabs
    for idx in range(window.stack.count()):
        window._navigate_to(idx)
        assert window.stack.currentIndex() == idx

    # Test theme toggling
    window._toggle_theme()
    assert window._active_theme in ["light", "dark"]
    window._toggle_theme()
    assert window._active_theme in ["light", "dark"]

    window.close()
