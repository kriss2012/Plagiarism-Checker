"""Institutional desktop styling for IMRD ResearchGuard (PySide6).
Tailored for SES's R. C. Patel Institute of Management Research and Development (IMRD), Shirpur.
Official website: https://www.rcpimrd.ac.in/
Brand palette:  Primary Teal  #21a7d0  |  Dark Navy  #273c66  |  Deep Navy  #112958
                Body Text     #505050  |  Light BG   #f3f8f9  |  White      #ffffff
Brand fonts:    Rubik (body)  |  Nunito (headings)  —  fall back to 'Segoe UI' on Windows.
"""

RCPIMRD_THEME = """
/* ==================== GLOBAL — RCPIMRD INSTITUTIONAL PALETTE ==================== */
QWidget {
    background-color: #f3f8f9;
    color: #505050;
    font-family: 'Rubik', 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 12px;
    selection-background-color: #21a7d0;
    selection-color: #ffffff;
}

QMainWindow {
    background-color: #f3f8f9;
}

/* ==================== NATIVE WINDOWS MENU BAR ==================== */
QMenuBar {
    background-color: #ffffff;
    color: #112958;
    border-bottom: 1px solid #d0e8f0;
    padding: 2px 6px;
    font-size: 12px;
    font-weight: 500;
}

QMenuBar::item {
    background: transparent;
    padding: 5px 10px;
    border-radius: 4px;
}

QMenuBar::item:selected, QMenuBar::item:pressed {
    background-color: #e7f6fb;
    color: #21a7d0;
}

QMenu {
    background-color: #ffffff;
    color: #505050;
    border: 1px solid #d0e8f0;
    border-radius: 4px;
    padding: 4px 0;
    font-size: 12px;
}

QMenu::item {
    padding: 6px 28px 6px 20px;
    background: transparent;
}

QMenu::item:selected {
    background-color: #21a7d0;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background: #e7f6fb;
    margin: 4px 8px;
}

/* ==================== INSTITUTIONAL HEADER ==================== */
#instHeader {
    background-color: #273c66;
    border-bottom: 3px solid #21a7d0;
    min-height: 62px;
    max-height: 62px;
    padding: 0 16px;
}

#instHeader QLabel {
    background: transparent;
    border: none;
}

#statusPill {
    background-color: rgba(33, 167, 208, 0.18);
    color: #b3e8f7;
    border: 1px solid #21a7d0;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 700;
    padding: 4px 10px;
    min-height: 18px;
    max-height: 20px;
}

/* ==================== SIDEBAR NAVIGATION ==================== */
#sidebar {
    background-color: #ffffff;
    border-right: 1px solid #d0e8f0;
    min-width: 220px;
    max-width: 220px;
}

#sidebarHeader {
    padding: 12px 14px 8px 14px;
    border-bottom: 1px solid #e7f6fb;
    margin-bottom: 6px;
}

#navBtn {
    background-color: transparent;
    color: #505050;
    text-align: left;
    padding: 9px 14px;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 5px;
    font-size: 12.5px;
    font-weight: 500;
    margin: 1px 6px;
    min-height: 34px;
}

#navBtn:hover {
    background-color: #e7f6fb;
    color: #21a7d0;
}

#navBtn:checked, #navBtn[active="true"] {
    background-color: #e0f4fb;
    color: #21a7d0;
    font-weight: 700;
    border-left: 3px solid #21a7d0;
}

#sidebarLibBadge {
    background-color: #f3f8f9;
    border: 1px solid #d0e8f0;
    border-radius: 6px;
    padding: 8px 10px;
    margin: 4px;
}

/* ==================== CONTENT CONTAINER ==================== */
#contentArea {
    background-color: #f3f8f9;
}

/* ==================== CARDS & FRAMES ==================== */
QFrame.card, QFrame#card {
    background-color: #ffffff;
    border: 1px solid #d0e8f0;
    border-radius: 8px;
    padding: 14px;
}

/* ==================== BUTTONS ==================== */
QPushButton {
    background-color: #ffffff;
    color: #273c66;
    border: 1px solid #b3d9eb;
    border-radius: 5px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 12px;
    min-height: 28px;
}

QPushButton:hover {
    background-color: #e7f6fb;
    border-color: #21a7d0;
    color: #21a7d0;
}

QPushButton:pressed {
    background-color: #c8ecf7;
}

QPushButton:focus {
    border-color: #21a7d0;
}

QPushButton:disabled {
    background-color: #f3f8f9;
    color: #aac8d8;
    border-color: #d0e8f0;
}

/* Primary Action Buttons — RCPIMRD Teal */
QPushButton.primary, QPushButton#primaryBtn {
    background-color: #21a7d0;
    color: #ffffff;
    border: 1px solid #1a8ab0;
    font-weight: 600;
}

QPushButton.primary:hover, QPushButton#primaryBtn:hover {
    background-color: #1a8ab0;
    border-color: #156e8c;
    color: #ffffff;
}

QPushButton.primary:pressed, QPushButton#primaryBtn:pressed {
    background-color: #156e8c;
}

/* Certificate Action Button — RCPIMRD Dark Navy */
QPushButton#certBtn {
    background-color: #273c66;
    color: #ffffff;
    border: 1px solid #1e2f52;
    font-weight: 700;
    font-size: 12px;
    padding: 6px 14px;
    border-radius: 5px;
}

QPushButton#certBtn:hover {
    background-color: #1e2f52;
    color: #ffffff;
}

QPushButton#certBtn:pressed {
    background-color: #112958;
}

/* Danger / Destructive Action Button */
QPushButton.danger, QPushButton#dangerBtn {
    background-color: #fef2f2;
    color: #dc2626;
    border: 1px solid #fca5a5;
    font-weight: 600;
}

QPushButton.danger:hover, QPushButton#dangerBtn:hover {
    background-color: #fee2e2;
    border-color: #ef4444;
    color: #b91c1c;
}

QPushButton.danger:pressed, QPushButton#dangerBtn:pressed {
    background-color: #fecaca;
}

/* Compact Table Action Button */
QPushButton.tableBtn, QPushButton#tableBtn {
    min-height: 24px;
    max-height: 24px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
    border-radius: 4px;
}

/* ==================== INPUTS & FORM CONTROLS ==================== */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #ffffff;
    color: #505050;
    border: 1px solid #b3d9eb;
    border-radius: 5px;
    padding: 6px 9px;
    font-size: 12px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #21a7d0;
    background-color: #ffffff;
}

QComboBox {
    background-color: #ffffff;
    color: #505050;
    border: 1px solid #b3d9eb;
    border-radius: 5px;
    padding: 5px 9px;
    font-size: 12px;
    min-height: 26px;
}

QComboBox:hover {
    border-color: #21a7d0;
}

QComboBox:focus {
    border-color: #21a7d0;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #505050;
    border: 1px solid #b3d9eb;
    selection-background-color: #21a7d0;
    selection-color: #ffffff;
}

QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    color: #505050;
    border: 1px solid #b3d9eb;
    border-radius: 5px;
    padding: 5px 9px;
    min-height: 26px;
}

QCheckBox {
    spacing: 8px;
    color: #505050;
    font-size: 12px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #b3d9eb;
    background-color: #ffffff;
}

QCheckBox::indicator:checked {
    background-color: #21a7d0;
    border-color: #1a8ab0;
}

/* ==================== PROGRESS BAR ==================== */
QProgressBar {
    background-color: #e7f6fb;
    border: 1px solid #b3d9eb;
    border-radius: 5px;
    text-align: center;
    color: #273c66;
    font-weight: 700;
    font-size: 11px;
    height: 18px;
}

QProgressBar::chunk {
    background-color: #21a7d0;
    border-radius: 4px;
}

/* ==================== DATA TABLES ==================== */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #d0e8f0;
    border-radius: 6px;
    gridline-color: #f3f8f9;
    selection-background-color: #e0f4fb;
    selection-color: #112958;
    font-size: 12px;
}

QTableWidget::item {
    padding: 6px 8px;
}

QTableWidget::item:selected {
    background-color: #c8ecf7;
    color: #112958;
    font-weight: 600;
}

QHeaderView::section {
    background-color: #f3f8f9;
    color: #273c66;
    font-family: 'Nunito', 'Segoe UI', sans-serif;
    font-weight: 700;
    font-size: 11px;
    padding: 7px 8px;
    border: none;
    border-bottom: 2px solid #21a7d0;
    border-right: 1px solid #e7f6fb;
}

/* ==================== SCROLLBARS ==================== */
QScrollBar:vertical {
    background-color: #f3f8f9;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #b3d9eb;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #21a7d0;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #f3f8f9;
    height: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background-color: #b3d9eb;
    min-width: 24px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #21a7d0;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ==================== TABS ==================== */
QTabWidget::pane {
    border: 1px solid #d0e8f0;
    background-color: #ffffff;
    border-radius: 6px;
    top: -1px;
}

QTabBar::tab {
    background-color: #f3f8f9;
    color: #505050;
    border: 1px solid #d0e8f0;
    border-bottom: none;
    padding: 7px 16px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    margin-right: 3px;
    font-size: 12px;
}

QTabBar::tab:selected {
    background-color: #ffffff;
    color: #21a7d0;
    font-weight: 700;
    border-bottom: 2px solid #21a7d0;
}

QTabBar::tab:hover {
    background-color: #e7f6fb;
    color: #21a7d0;
}

/* ==================== STATUS BAR ==================== */
QStatusBar {
    background-color: #ffffff;
    color: #505050;
    border-top: 1px solid #d0e8f0;
    font-size: 11px;
    padding: 2px 8px;
}

/* ==================== TOOLTIPS ==================== */
QToolTip {
    background-color: #273c66;
    color: #ffffff;
    border: 1px solid #21a7d0;
    padding: 5px 8px;
    border-radius: 4px;
    font-size: 11px;
}

/* ==================== HIGHLIGHT EDITOR WIDGET ==================== */
#highlightEditorText {
    background-color: #ffffff;
    color: #505050;
    border: 1px solid #d0e8f0;
    border-radius: 6px;
    padding: 14px;
    font-family: 'Rubik', 'Segoe UI', serif;
    font-size: 13.5px;
    line-height: 1.6;
}

#filterBtn {
    background-color: #f3f8f9;
    color: #273c66;
    border: 1px solid #b3d9eb;
    border-radius: 4px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
}

#filterBtn:checked {
    background-color: #21a7d0;
    color: #ffffff;
    border-color: #1a8ab0;
}
"""


def get_theme_stylesheet(theme_name: str = "light") -> str:
    """Returns the RCPIMRD institutional stylesheet.
    Dark mode has been removed; this always returns the official light theme.
    The ``theme_name`` parameter is kept for API compatibility but is ignored.
    """
    return RCPIMRD_THEME
