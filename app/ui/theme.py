"""Modern professional desktop styling and themes for IMRD ResearchGuard (PySide6).
Tailored for SES's R. C. Patel Institute of Management Research and Development (IMRD), Shirpur.
Official institutional colors: Deep Navy (#002461), Royal Blue (#005FEA), Gold Seal (#D97706),
with clean native Windows 10/11 desktop light styling as default.
"""

LIGHT_THEME = """
/* ==================== GLOBAL WINDOWS DESKTOP STYLE ==================== */
QWidget {
    background-color: #F1F5F9;
    color: #0F172A;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    selection-background-color: #005FEA;
    selection-color: #FFFFFF;
}

QMainWindow {
    background-color: #F8FAFC;
}

/* ==================== NATIVE WINDOWS MENU BAR ==================== */
QMenuBar {
    background-color: #FFFFFF;
    color: #0F172A;
    border-bottom: 1px solid #CBD5E1;
    padding: 2px 6px;
    font-size: 12px;
}

QMenuBar::item {
    background: transparent;
    padding: 5px 10px;
    border-radius: 4px;
}

QMenuBar::item:selected, QMenuBar::item:pressed {
    background-color: #E2E8F0;
    color: #002461;
}

QMenu {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 4px;
    padding: 4px 0;
    font-size: 12px;
}

QMenu::item {
    padding: 6px 28px 6px 20px;
    background: transparent;
}

QMenu::item:selected {
    background-color: #005FEA;
    color: #FFFFFF;
}

QMenu::separator {
    height: 1px;
    background: #E2E8F0;
    margin: 4px 8px;
}

/* ==================== INSTITUTIONAL HEADER ==================== */
#instHeader {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #002461, stop:0.75 #00388A, stop:1 #005FEA);
    border-bottom: 2px solid #D97706;
    min-height: 64px;
    max-height: 64px;
    padding: 0 16px;
}

#instHeader QLabel {
    background: transparent;
    border: none;
}

/* ==================== SIDEBAR NAVIGATION ==================== */
#sidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #CBD5E1;
    min-width: 230px;
    max-width: 230px;
}

#sidebarHeader {
    padding: 12px 14px 8px 14px;
    border-bottom: 1px solid #E2E8F0;
    margin-bottom: 6px;
}

#navBtn {
    background-color: transparent;
    color: #334155;
    text-align: left;
    padding: 10px 16px;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    margin: 2px 8px;
}

#navBtn:hover {
    background-color: #F1F5F9;
    color: #002461;
}

#navBtn:checked, #navBtn[active="true"] {
    background-color: #EFF6FF;
    color: #005FEA;
    font-weight: 700;
    border-left: 4px solid #005FEA;
}

/* ==================== CONTENT CONTAINER ==================== */
#contentArea {
    background-color: #F1F5F9;
}

/* ==================== CARDS & FRAMES ==================== */
QFrame.card, QFrame#card {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 8px;
    padding: 14px;
}

/* ==================== BUTTONS ==================== */
QPushButton {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 5px;
    padding: 7px 16px;
    font-weight: 500;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #F8FAFC;
    border-color: #94A3B8;
    color: #002461;
}

QPushButton:pressed {
    background-color: #E2E8F0;
}

QPushButton:disabled {
    background-color: #F1F5F9;
    color: #94A3B8;
    border-color: #E2E8F0;
}

/* Primary Action Buttons - IMRD Royal Blue */
QPushButton.primary, QPushButton#primaryBtn {
    background-color: #005FEA;
    color: #FFFFFF;
    border: 1px solid #0048B5;
    font-weight: 600;
}

QPushButton.primary:hover, QPushButton#primaryBtn:hover {
    background-color: #0048B5;
    border-color: #00368B;
}

QPushButton.primary:pressed, QPushButton#primaryBtn:pressed {
    background-color: #002461;
}

/* Certificate Action Button - Academic Gold / Amber */
QPushButton#certBtn {
    background-color: #D97706;
    color: #FFFFFF;
    border: 1px solid #B45309;
    font-weight: 700;
    font-size: 13px;
    padding: 9px 18px;
    border-radius: 6px;
}

QPushButton#certBtn:hover {
    background-color: #B45309;
}

/* ==================== INPUTS & FORM CONTROLS ==================== */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 5px;
    padding: 7px 10px;
    font-size: 12px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #005FEA;
    background-color: #FFFFFF;
}

QComboBox {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 5px;
    padding: 6px 10px;
    font-size: 12px;
}

QComboBox:hover {
    border-color: #94A3B8;
}

QComboBox:focus {
    border-color: #005FEA;
}

QComboBox::drop-down {
    border: none;
    width: 22px;
}

QComboBox QAbstractItemView {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    selection-background-color: #005FEA;
    selection-color: #FFFFFF;
}

QSpinBox, QDoubleSpinBox {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 5px;
    padding: 6px 10px;
}

QCheckBox {
    spacing: 8px;
    color: #334155;
    font-size: 12px;
}

QCheckBox::indicator {
    width: 17px;
    height: 17px;
    border-radius: 3px;
    border: 1px solid #94A3B8;
    background-color: #FFFFFF;
}

QCheckBox::indicator:checked {
    background-color: #005FEA;
    border-color: #0048B5;
}

/* ==================== PROGRESS BAR ==================== */
QProgressBar {
    background-color: #E2E8F0;
    border: 1px solid #CBD5E1;
    border-radius: 5px;
    text-align: center;
    color: #0F172A;
    font-weight: 700;
    font-size: 11px;
    height: 18px;
}

QProgressBar::chunk {
    background-color: #005FEA;
    border-radius: 4px;
}

/* ==================== DATA TABLES ==================== */
QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    gridline-color: #E2E8F0;
    selection-background-color: #EFF6FF;
    selection-color: #002461;
    font-size: 12px;
}

QTableWidget::item {
    padding: 6px 10px;
}

QTableWidget::item:selected {
    background-color: #E0E7FF;
    color: #002461;
    font-weight: 600;
}

QHeaderView::section {
    background-color: #F8FAFC;
    color: #002461;
    font-weight: 700;
    font-size: 11px;
    padding: 8px 10px;
    border: none;
    border-bottom: 2px solid #CBD5E1;
    border-right: 1px solid #E2E8F0;
}

/* ==================== SCROLLBARS ==================== */
QScrollBar:vertical {
    background-color: #F1F5F9;
    width: 10px;
    margin: 0;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #CBD5E1;
    min-height: 24px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background-color: #94A3B8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ==================== TABS ==================== */
QTabWidget::pane {
    border: 1px solid #CBD5E1;
    background-color: #FFFFFF;
    border-radius: 6px;
    top: -1px;
}

QTabBar::tab {
    background-color: #F1F5F9;
    color: #475569;
    border: 1px solid #CBD5E1;
    border-bottom: none;
    padding: 8px 16px;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    margin-right: 3px;
    font-size: 12px;
}

QTabBar::tab:selected {
    background-color: #FFFFFF;
    color: #002461;
    font-weight: 700;
    border-bottom: 2px solid #005FEA;
}

/* ==================== STATUS BAR ==================== */
QStatusBar {
    background-color: #FFFFFF;
    color: #475569;
    border-top: 1px solid #CBD5E1;
    font-size: 11px;
    padding: 2px 8px;
}

/* ==================== TOOLTIPS ==================== */
QToolTip {
    background-color: #002461;
    color: #FFFFFF;
    border: 1px solid #005FEA;
    padding: 5px 8px;
    border-radius: 4px;
    font-size: 11px;
}
"""

DARK_THEME = """
/* ==================== HIGH-CONTRAST DARK DESKTOP THEME ==================== */
QWidget {
    background-color: #0F172A;
    color: #F8FAFC;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    selection-background-color: #005FEA;
    selection-color: #FFFFFF;
}

QMainWindow {
    background-color: #0B0F19;
}

QMenuBar {
    background-color: #0B0F19;
    color: #F8FAFC;
    border-bottom: 1px solid #1E293B;
    padding: 2px 6px;
    font-size: 12px;
}

QMenuBar::item:selected {
    background-color: #1E293B;
    color: #60A5FA;
}

QMenu {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #334155;
    padding: 4px 0;
}

QMenu::item:selected {
    background-color: #005FEA;
    color: #FFFFFF;
}

QMenu::separator {
    height: 1px;
    background: #334155;
}

#instHeader {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #001740, stop:0.75 #002461, stop:1 #00388A);
    border-bottom: 2px solid #D97706;
    min-height: 64px;
    max-height: 64px;
    padding: 0 16px;
}

#instHeader QLabel {
    background: transparent;
    border: none;
}

#sidebar {
    background-color: #0B0F19;
    border-right: 1px solid #1E293B;
    min-width: 230px;
    max-width: 230px;
}

#navBtn {
    background-color: transparent;
    color: #94A3B8;
    text-align: left;
    padding: 10px 16px;
    border: none;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    margin: 2px 8px;
}

#navBtn:hover {
    background-color: #1E293B;
    color: #F8FAFC;
}

#navBtn:checked, #navBtn[active="true"] {
    background-color: #1E293B;
    color: #60A5FA;
    font-weight: 700;
    border-left: 4px solid #005FEA;
}

#contentArea {
    background-color: #0F172A;
}

QFrame.card, QFrame#card {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 14px;
}

QPushButton {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 5px;
    padding: 7px 16px;
    font-weight: 500;
    font-size: 12px;
}

QPushButton:hover {
    background-color: #334155;
    border-color: #475569;
}

QPushButton.primary, QPushButton#primaryBtn {
    background-color: #005FEA;
    color: #FFFFFF;
    border: 1px solid #0048B5;
    font-weight: 600;
}

QPushButton.primary:hover, QPushButton#primaryBtn:hover {
    background-color: #0048B5;
}

QPushButton#certBtn {
    background-color: #D97706;
    color: #FFFFFF;
    border: 1px solid #B45309;
    font-weight: 700;
    font-size: 13px;
    padding: 9px 18px;
    border-radius: 6px;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #0B0F19;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 5px;
    padding: 7px 10px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #005FEA;
}

QComboBox {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 5px;
    padding: 6px 10px;
}

QTableWidget {
    background-color: #1E293B;
    border: 1px solid #334155;
    gridline-color: #334155;
    selection-background-color: #1E3A8A;
    selection-color: #FFFFFF;
}

QHeaderView::section {
    background-color: #0B0F19;
    color: #94A3B8;
    font-weight: 700;
    padding: 8px 10px;
    border: none;
    border-bottom: 2px solid #334155;
}

QProgressBar {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 5px;
    text-align: center;
    color: #F8FAFC;
    height: 18px;
}

QProgressBar::chunk {
    background-color: #005FEA;
    border-radius: 4px;
}

QStatusBar {
    background-color: #0B0F19;
    color: #94A3B8;
    border-top: 1px solid #1E293B;
}
"""


def get_theme_stylesheet(theme_name: str = "light") -> str:
    """Returns the CSS stylesheet string for the requested theme."""
    return DARK_THEME if theme_name.lower() == "dark" else LIGHT_THEME
