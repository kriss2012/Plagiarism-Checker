"""Main desktop application window for ResearchGuard.
Contains the persistent sidebar navigation, top bar controls, and stacked central views.
"""

from typing import Dict, Optional
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)
from app.config import APP_NAME, APP_TITLE, APP_VERSION
from app.database.models import Document, Match
from app.database.session import get_db, get_setting
from app.ui.theme import get_theme_stylesheet
from app.ui.views.dashboard_view import DashboardView
from app.ui.views.documents_view import DocumentsView
from app.ui.views.help_view import HelpView
from app.ui.views.match_viewer_view import MatchViewerView
from app.ui.views.new_check_view import NewCheckView
from app.ui.views.results_view import ResultsView
from app.ui.views.source_library_view import SourceLibraryView
from app.ui.views.settings_view import SettingsView


class MainWindow(QMainWindow):
    """Primary application frame hosting responsive navigation and analytical views."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1280, 840)
        self.setMinimumSize(1024, 700)

        # Set Window Icon
        from pathlib import Path
        from PySide6.QtGui import QIcon, QPixmap
        icon_path = Path(__file__).resolve().parent.parent.parent / "resources" / "app_icon.png"
        if not icon_path.exists():
            icon_path = Path(__file__).resolve().parent.parent.parent / "Logo.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._active_theme = get_setting("theme", "dark")
        self._init_ui()
        self._apply_theme(self._active_theme)

    def _init_ui(self):
        # Central widget and root horizontal layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Left Sidebar
        self.sidebar = self._create_sidebar()
        root_layout.addWidget(self.sidebar)

        # 2. Right Area (Top Bar + Main Stack)
        right_container = QWidget()
        right_box = QVBoxLayout(right_container)
        right_box.setContentsMargins(0, 0, 0, 0)
        right_box.setSpacing(0)

        self.top_bar = self._create_top_bar()
        right_box.addWidget(self.top_bar)

        # Central Stacked Views
        self.stack = QStackedWidget()
        self.stack.setObjectName("contentArea")

        self.view_dashboard = DashboardView()
        self.view_new_check = NewCheckView()
        self.view_documents = DocumentsView()
        self.view_results = ResultsView()
        self.view_match_viewer = MatchViewerView()
        self.view_sources = SourceLibraryView()
        self.view_settings = SettingsView()
        self.view_help = HelpView()

        # Connect inter-view signals
        self.view_dashboard.start_check_requested.connect(lambda: self._navigate_to(1))
        self.view_dashboard.view_document_requested.connect(self._load_document_into_results)
        self.view_documents.view_doc_requested.connect(self._load_document_into_results)
        self.view_new_check.analysis_completed.connect(self._on_analysis_finished)
        self.view_results.open_match_viewer.connect(self._on_open_match_viewer)
        self.view_match_viewer.back_to_results.connect(lambda: self._navigate_to(3))
        self.view_settings.theme_changed.connect(self._apply_theme)

        # Add to stack (Indices: 0=Dashboard, 1=New Check, 2=Documents, 3=Results, 4=MatchViewer, 5=Sources, 6=Settings, 7=Help)
        self.stack.addWidget(self.view_dashboard)    # 0
        self.stack.addWidget(self.view_new_check)    # 1
        self.stack.addWidget(self.view_documents)    # 2
        self.stack.addWidget(self.view_results)      # 3
        self.stack.addWidget(self.view_match_viewer) # 4
        self.stack.addWidget(self.view_sources)      # 5
        self.stack.addWidget(self.view_settings)     # 6
        self.stack.addWidget(self.view_help)         # 7

        right_box.addWidget(self.stack, 1)
        root_layout.addWidget(right_container, 1)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("ResearchGuard Academic Plagiarism Checker • Ready")

    def _create_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 18, 12, 18)
        layout.setSpacing(6)

        # Logo / Branding
        from pathlib import Path
        from PySide6.QtGui import QPixmap
        logo_path = Path(__file__).resolve().parent.parent.parent / "resources" / "app_icon.png"
        if not logo_path.exists():
            logo_path = Path(__file__).resolve().parent.parent.parent / "Logo.png"

        brand_box = QHBoxLayout()
        logo_lbl = QLabel()
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path)).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pixmap)
        else:
            logo_lbl.setText("🛡️")
            logo_lbl.setStyleSheet("font-size: 24px;")
        logo_lbl.setStyleSheet("background: transparent; border: none;")
        brand_box.addWidget(logo_lbl)

        brand_txt = QVBoxLayout()
        title = QLabel(APP_NAME)
        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #FFFFFF; letter-spacing: 0.5px;")
        sub = QLabel("Academic Systems")
        sub.setStyleSheet("font-size: 11px; color: #818CF8; font-weight: 600;")
        brand_txt.addWidget(title)
        brand_txt.addWidget(sub)
        brand_box.addLayout(brand_txt)
        brand_box.addStretch()
        layout.addLayout(brand_box)

        layout.addSpacing(18)

        # Navigation Buttons
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        nav_items = [
            ("📊  Dashboard", 0),
            ("➕  New Check", 1),
            ("📁  Documents", 2),
            ("📈  Results", 3),
            ("📚  Source Library", 5),
            ("⚙️  Settings", 6),
            ("❓  Help / About", 7),
        ]

        self.nav_buttons = {}
        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setObjectName("navBtn")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=index: self._navigate_to(idx))
            self.nav_group.addButton(btn, index)
            self.nav_buttons[index] = btn
            layout.addWidget(btn)

        layout.addStretch()

        # Offline Mode Badge in Sidebar bottom
        offline_box = QFrame()
        offline_box.setStyleSheet("""
            QFrame {
                background-color: rgba(16, 185, 129, 0.1);
                border: 1px solid #10B981;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        ob_layout = QVBoxLayout(offline_box)
        ob_layout.setSpacing(2)
        ob_title = QLabel("🟢 OFFLINE MODE")
        ob_title.setStyleSheet("font-size: 10px; font-weight: 800; color: #10B981;")
        ob_desc = QLabel("Documents remain local")
        ob_desc.setStyleSheet("font-size: 10px; color: #94A3B8;")
        ob_layout.addWidget(ob_title)
        ob_layout.addWidget(ob_desc)
        layout.addWidget(offline_box)

        # Default select Dashboard
        self.nav_buttons[0].setChecked(True)
        return sidebar

    def _create_top_bar(self) -> QFrame:
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)

        # Global Search
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search documents, sources, or matches...")
        self.search_bar.setFixedWidth(300)
        self.search_bar.returnPressed.connect(self._on_search_triggered)
        layout.addWidget(self.search_bar)

        layout.addStretch()

        # Theme Toggle
        self.theme_btn = QPushButton("🌙 Theme")
        self.theme_btn.setFixedHeight(32)
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

        # Settings shortcut
        settings_btn = QPushButton("Settings")
        settings_btn.setFixedHeight(32)
        settings_btn.clicked.connect(lambda: self._navigate_to(6))
        layout.addWidget(settings_btn)

        # System Status Pill
        status_pill = QLabel("  ● Ready  ")
        status_pill.setStyleSheet("""
            background-color: rgba(16, 185, 129, 0.15);
            color: #10B981;
            border: 1px solid #10B981;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 700;
            padding: 4px 8px;
        """)
        layout.addWidget(status_pill)

        return top_bar

    def _navigate_to(self, index: int):
        self.stack.setCurrentIndex(index)
        if index in self.nav_buttons:
            self.nav_buttons[index].setChecked(True)

        # Refresh target view if applicable
        if index == 0:
            self.view_dashboard.refresh_data()
        elif index == 2:
            self.view_documents.refresh_list()
        elif index == 5:
            self.view_sources.refresh_list()

    def _toggle_theme(self):
        new_theme = "light" if self._active_theme == "dark" else "dark"
        self._apply_theme(new_theme)

    def _apply_theme(self, theme_name: str):
        self._active_theme = theme_name
        self.setStyleSheet(get_theme_stylesheet(theme_name))
        self.theme_btn.setText("☀️ Light" if theme_name == "light" else "🌙 Dark")

    def _on_analysis_finished(self, result_and_id):
        result, doc_id = result_and_id
        self.view_results.load_result(result, doc_id)
        self._navigate_to(3)  # Switch to Results view

    def _on_open_match_viewer(self, data_dict):
        self.view_match_viewer.load_data(data_dict)
        self._navigate_to(4)  # Switch to Match Viewer view

    def _load_document_into_results(self, doc_id: int):
        """Loads a past document from DB into the Results view."""
        import json
        from dataclasses import dataclass
        from app.core.scoring import ScoreBreakdown

        with get_db() as session:
            doc = session.query(Document).filter_by(id=doc_id).first()
            if not doc:
                return

            matches = [m.to_dict() for m in doc.matches]

            sb = ScoreBreakdown(
                overall_similarity=doc.overall_similarity,
                risk_level=doc.risk_level,
                exact_percentage=round((doc.exact_matches_count / max(1, doc.word_count)) * 100, 1),
                fuzzy_percentage=round((doc.fuzzy_matches_count / max(1, doc.word_count)) * 100, 1),
                semantic_percentage=round((doc.semantic_matches_count / max(1, doc.word_count)) * 100, 1),
                quoted_percentage=round((doc.quoted_matches_count / max(1, doc.word_count)) * 100, 1),
                total_analyzed_words=doc.word_count,
                matched_words=0,
                exact_count=doc.exact_matches_count,
                fuzzy_count=doc.fuzzy_matches_count,
                semantic_count=doc.semantic_matches_count,
                quoted_count=doc.quoted_matches_count,
                ignored_count=0,
                explanation="",
            )

            # Reconstitute mock result object
            class SavedResult:
                pass

            res = SavedResult()
            res.document_filename = doc.filename
            res.file_hash = doc.hash
            res.word_count = doc.word_count
            res.page_count = doc.page_count
            res.extracted_text = doc.extracted_text or ""
            res.score_breakdown = sb
            res.matches = matches

            # Structure
            try:
                res.structure = json.loads(doc.structure_json) if doc.structure_json else {}
            except Exception:
                res.structure = {}

            # Citations
            @dataclass
            class MockCit:
                citation_count: int = 0
                reference_count: int = 0
                quotes: list = None
                uncited_claims: int = 0

            res.citations = MockCit(quotes=[])

            # AI
            @dataclass
            class MockAI:
                likelihood: str = "Low"
                score: float = 15.0

            res.ai_writing = MockAI(likelihood=doc.ai_likelihood or "Low")

            self.view_results.load_result(res, doc_id)
            self._navigate_to(3)

    def _on_search_triggered(self):
        txt = self.search_bar.text().strip()
        if txt:
            self.view_documents.search_input.setText(txt)
            self._navigate_to(2)  # Switch to documents view
