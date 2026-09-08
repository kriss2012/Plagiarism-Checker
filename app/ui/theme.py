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
    font-size: 12px;
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
    min-height: 60px;
    max-height: 60px;
    padding: 0 16px;
}

#instHeader QLabel {
    background: transparent;
    border: none;
}

#headerBtn {
    background-color: rgba(255, 255, 255, 0.12);
    color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.28);
    font-size: 11.5px;
    font-weight: 600;
    padding: 5px 12px;
    min-height: 28px;
    max-height: 28px;
    border-radius: 5px;
}

#headerBtn:hover {
    background-color: rgba(255, 255, 255, 0.24);
    border-color: rgba(255, 255, 255, 0.45);
}

#headerBtn:pressed {
    background-color: rgba(255, 255, 255, 0.32);
}

#statusPill {
    background-color: rgba(16, 185, 129, 0.2);
    color: #A7F3D0;
    border: 1px solid #10B981;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 700;
    padding: 4px 10px;
    min-height: 18px;
    max-height: 20px;
}

/* ==================== SIDEBAR NAVIGATION ==================== */
#sidebar {
    background-color: #FFFFFF;
    border-right: 1px solid #CBD5E1;
    min-width: 235px;
    max-width: 235px;
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
    padding: 8px 14px;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 5px;
    font-size: 12.5px;
    font-weight: 500;
    margin: 1px 6px;
    min-height: 32px;
}

#navBtn:hover {
    background-color: #F1F5F9;
    color: #002461;
}

#navBtn:checked, #navBtn[active="true"] {
    background-color: #EFF6FF;
    color: #005FEA;
    font-weight: 700;
    border-left: 3px solid #005FEA;
}

#sidebarLibBadge {
    background-color: #F8FAFC;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 8px 10px;
    margin: 4px;
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
    padding: 6px 14px;
    font-weight: 600;
    font-size: 12px;
    min-height: 28px;
}

QPushButton:hover {
    background-color: #F8FAFC;
    border-color: #94A3B8;
    color: #002461;
}

QPushButton:pressed {
    background-color: #E2E8F0;
}

QPushButton:focus {
    border-color: #005FEA;
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
    color: #FFFFFF;
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
    font-size: 12px;
    padding: 6px 14px;
    border-radius: 5px;
}

QPushButton#certBtn:hover {
    background-color: #B45309;
    color: #FFFFFF;
}

QPushButton#certBtn:pressed {
    background-color: #92400E;
}

/* Danger / Destructive Action Button */
QPushButton.danger, QPushButton#dangerBtn {
    background-color: #FEF2F2;
    color: #DC2626;
    border: 1px solid #FCA5A5;
    font-weight: 600;
}

QPushButton.danger:hover, QPushButton#dangerBtn:hover {
    background-color: #FEE2E2;
    border-color: #EF4444;
    color: #B91C1C;
}

QPushButton.danger:pressed, QPushButton#dangerBtn:pressed {
    background-color: #FECACA;
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
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 5px;
    padding: 6px 9px;
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
    padding: 5px 9px;
    font-size: 12px;
    min-height: 26px;
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
    padding: 5px 9px;
    min-height: 26px;
}

QCheckBox {
    spacing: 8px;
    color: #334155;
    font-size: 12px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
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
    gridline-color: #F1F5F9;
    selection-background-color: #EFF6FF;
    selection-color: #002461;
    font-size: 12px;
}

QTableWidget::item {
    padding: 6px 8px;
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
    padding: 7px 8px;
    border: none;
    border-bottom: 2px solid #CBD5E1;
    border-right: 1px solid #F1F5F9;
}

/* ==================== SCROLLBARS ==================== */
QScrollBar:vertical {
    background-color: #F1F5F9;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #CBD5E1;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #94A3B8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #F1F5F9;
    height: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background-color: #CBD5E1;
    min-width: 24px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #94A3B8;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
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
    padding: 7px 15px;
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

/* ==================== HIGHLIGHT EDITOR WIDGET ==================== */
#highlightEditorText {
    background-color: #FFFFFF;
    color: #0F172A;
    border: 1px solid #CBD5E1;
    border-radius: 6px;
    padding: 14px;
    font-family: 'Segoe UI', serif;
    font-size: 13.5px;
    line-height: 1.6;
}

#filterBtn {
    background-color: #F8FAFC;
    color: #334155;
    border: 1px solid #CBD5E1;
    border-radius: 4px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
}

#filterBtn:checked {
    background-color: #005FEA;
    color: #FFFFFF;
    border-color: #0048B5;
}
"""

DARK_THEME = """
/* ==================== HIGH-CONTRAST DARK DESKTOP THEME ==================== */
QWidget {
    background-color: #0F172A;
    color: #F8FAFC;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 12px;
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
    min-height: 60px;
    max-height: 60px;
    padding: 0 16px;
}

#instHeader QLabel {
    background: transparent;
    border: none;
}

#headerBtn {
    background-color: rgba(255, 255, 255, 0.12);
    color: #FFFFFF;
    border: 1px solid rgba(255, 255, 255, 0.28);
    font-size: 11.5px;
    font-weight: 600;
    padding: 5px 12px;
    min-height: 28px;
    max-height: 28px;
    border-radius: 5px;
}

#headerBtn:hover {
    background-color: rgba(255, 255, 255, 0.24);
    border-color: rgba(255, 255, 255, 0.45);
}

#headerBtn:pressed {
    background-color: rgba(255, 255, 255, 0.32);
}

#statusPill {
    background-color: rgba(16, 185, 129, 0.2);
    color: #A7F3D0;
    border: 1px solid #10B981;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 700;
    padding: 4px 10px;
    min-height: 18px;
    max-height: 20px;
}

#sidebar {
    background-color: #0B0F19;
    border-right: 1px solid #1E293B;
    min-width: 235px;
    max-width: 235px;
}

#navBtn {
    background-color: transparent;
    color: #94A3B8;
    text-align: left;
    padding: 8px 14px;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 5px;
    font-size: 12.5px;
    font-weight: 500;
    margin: 1px 6px;
    min-height: 32px;
}

#navBtn:hover {
    background-color: #1E293B;
    color: #F8FAFC;
}

#navBtn:checked, #navBtn[active="true"] {
    background-color: #1E293B;
    color: #60A5FA;
    font-weight: 700;
    border-left: 3px solid #005FEA;
}

#sidebarLibBadge {
    background-color: #1E293B;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 8px 10px;
    margin: 4px;
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
    padding: 6px 14px;
    font-weight: 600;
    font-size: 12px;
    min-height: 28px;
}

QPushButton:hover {
    background-color: #334155;
    border-color: #475569;
}

QPushButton:pressed {
    background-color: #0F172A;
}

QPushButton.primary, QPushButton#primaryBtn {
    background-color: #005FEA;
    color: #FFFFFF;
    border: 1px solid #0048B5;
    font-weight: 600;
}

QPushButton.primary:hover, QPushButton#primaryBtn:hover {
    background-color: #0048B5;
    color: #FFFFFF;
}

QPushButton#certBtn {
    background-color: #D97706;
    color: #FFFFFF;
    border: 1px solid #B45309;
    font-weight: 700;
    font-size: 12px;
    padding: 6px 14px;
    border-radius: 5px;
}

QPushButton.danger, QPushButton#dangerBtn {
    background-color: #450A0A;
    color: #FCA5A5;
    border: 1px solid #991B1B;
    font-weight: 600;
}

QPushButton.danger:hover, QPushButton#dangerBtn:hover {
    background-color: #7F1D1D;
    color: #FFFFFF;
}

QPushButton.tableBtn, QPushButton#tableBtn {
    min-height: 24px;
    max-height: 24px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: 600;
    border-radius: 4px;
}

QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #0B0F19;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 5px;
    padding: 6px 9px;
    font-size: 12px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #005FEA;
}

QComboBox {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 5px;
    padding: 5px 9px;
    font-size: 12px;
    min-height: 26px;
}

QTableWidget {
    background-color: #1E293B;
    border: 1px solid #334155;
    gridline-color: #1E293B;
    selection-background-color: #1E3A8A;
    selection-color: #FFFFFF;
    font-size: 12px;
}

QTableWidget::item {
    padding: 6px 8px;
}

QHeaderView::section {
    background-color: #0B0F19;
    color: #94A3B8;
    font-weight: 700;
    font-size: 11px;
    padding: 7px 8px;
    border: none;
    border-bottom: 2px solid #334155;
    border-right: 1px solid #1E293B;
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
    font-size: 11px;
}

#highlightEditorText {
    background-color: #0B0F19;
    color: #F8FAFC;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 14px;
    font-family: 'Segoe UI', serif;
    font-size: 13.5px;
    line-height: 1.6;
}

#filterBtn {
    background-color: #1E293B;
    color: #94A3B8;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
}

#filterBtn:checked {
    background-color: #005FEA;
    color: #FFFFFF;
    border-color: #0048B5;
}
"""


def get_theme_stylesheet(theme_name: str = "light") -> str:
    """Returns the CSS stylesheet string for the requested theme."""
    return DARK_THEME if theme_name.lower() == "dark" else LIGHT_THEME

