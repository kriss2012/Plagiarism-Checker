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
    # Test student intake form in NewCheckView
    new_check = window.view_new_check
    new_check.input_student_name.setText("Test Student")
    new_check.input_prn.setText("2024015400999999")
    new_check.input_guide.setText("Dr. S. B. Patil")
    new_check.input_title.setText("Automated Library Plagiarism Verification")
    assert new_check.input_student_name.text() == "Test Student"

    # Test clearing form
    new_check._clear_form()
    assert new_check.input_student_name.text() == ""

    # Test DocumentsView filter
    doc_view = window.view_documents
    doc_view.refresh_list()
    assert doc_view.table.columnCount() == 9

    window.close()
