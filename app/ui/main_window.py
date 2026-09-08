"""Main desktop application window for IMRD ResearchGuard.
Tailored for SES's R. C. Patel Institute of Management Research and Development (IMRD), Shirpur.
Provides native Windows menus, institutional branding banner, responsive navigation, and analytical views.
"""

from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QAction, QIcon, QKeySequence, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)
from app.config import (
    AFFILIATION_TEXT,
    APP_NAME,
    APP_TITLE,
    APP_VERSION,
    BASE_DIR,
    INSTITUTION_NAME,
    INSTITUTION_SHORT,
    LIBRARY_DEPARTMENT,
)
from app.database.models import Document
from app.database.session import get_db, get_setting, set_setting
from app.ui.theme import get_theme_stylesheet
from app.ui.views.dashboard_view import DashboardView
from app.ui.views.documents_view import DocumentsView
from app.ui.views.help_view import HelpView
from app.ui.views.match_viewer_view import MatchViewerView
from app.ui.views.new_check_view import NewCheckView
from app.ui.views.results_view import ResultsView
from app.ui.views.settings_view import SettingsView
from app.ui.views.source_library_view import SourceLibraryView


class MainWindow(QMainWindow):
    """Primary desktop application frame for IMRD Central Library plagiarism verification."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_TITLE)
        self.resize(1300, 860)
        self.setMinimumSize(1080, 720)

        # Set Window and Taskbar Icon
        icon_path = BASE_DIR / "resources" / "app_icon.png"
        if not icon_path.exists():
            icon_path = BASE_DIR / "Logo.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._active_theme = get_setting("theme", "light")
        self._init_ui()
        self._apply_theme(self._active_theme)

    def _init_ui(self):
        # 1. Native Windows Menu Bar
        self._create_menu_bar()

        # Central widget and root layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_vbox = QVBoxLayout(central_widget)
        root_vbox.setContentsMargins(0, 0, 0, 0)
        root_vbox.setSpacing(0)

        # 2. Institutional College Header
        self.inst_header = self._create_institutional_header()
        root_vbox.addWidget(self.inst_header)

        # 3. Main Workspace (Sidebar + Central Stack)
        workspace = QWidget()
        ws_layout = QHBoxLayout(workspace)
        ws_layout.setContentsMargins(0, 0, 0, 0)
        ws_layout.setSpacing(0)

        # Left Desktop Navigation Sidebar
        self.sidebar = self._create_sidebar()
        ws_layout.addWidget(self.sidebar)

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

        # Stack indices:
        # 0: Dashboard
        # 1: Verify Student Paper (New Check)
        # 2: Student Records Archive (Documents)
        # 3: Results & Certificate
        # 4: Match Viewer
        # 5: Source Library
        # 6: System Settings
        # 7: Librarian SOP & Help
        self.stack.addWidget(self.view_dashboard)    # 0
        self.stack.addWidget(self.view_new_check)    # 1
        self.stack.addWidget(self.view_documents)    # 2
        self.stack.addWidget(self.view_results)      # 3
        self.stack.addWidget(self.view_match_viewer) # 4
        self.stack.addWidget(self.view_sources)      # 5
        self.stack.addWidget(self.view_settings)     # 6
        self.stack.addWidget(self.view_help)         # 7

        ws_layout.addWidget(self.stack, 1)
        root_vbox.addWidget(workspace, 1)

        # 4. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("SES's R. C. Patel IMRD Shirpur • Central Library Verification Cell • Ready")

    def _create_menu_bar(self):
        """Builds standard Windows native desktop menu bar with accelerators."""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")

        act_new = QAction("&New Student Verification...", self)
        act_new.setShortcut(QKeySequence("Ctrl+N"))
        act_new.triggered.connect(lambda: self._navigate_to(1))
        file_menu.addAction(act_new)

        act_open = QAction("&Open Document to Verify...", self)
        act_open.setShortcut(QKeySequence("Ctrl+O"))
        act_open.triggered.connect(self._open_document_dialog)
        file_menu.addAction(act_open)

        file_menu.addSeparator()

        act_print_cert = QAction("&Print / Export Clearance Certificate...", self)
        act_print_cert.setShortcut(QKeySequence("Ctrl+P"))
        act_print_cert.triggered.connect(lambda: self.view_results._export_pdf())
        file_menu.addAction(act_print_cert)

        act_export_archive = QAction("&Export Student Register (CSV)...", self)
        act_export_archive.triggered.connect(lambda: self.view_documents.export_to_csv())
        file_menu.addAction(act_export_archive)

        file_menu.addSeparator()

        act_exit = QAction("E&xit", self)
        act_exit.setShortcut(QKeySequence("Alt+F4"))
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # Edit Menu
        edit_menu = menu_bar.addMenu("&Edit")

        act_clear_form = QAction("&Clear Current Intake Form", self)
        act_clear_form.triggered.connect(lambda: self.view_new_check._clear_form())
        edit_menu.addAction(act_clear_form)

        edit_menu.addSeparator()

        act_settings = QAction("&Preferences / Settings...", self)
        act_settings.setShortcut(QKeySequence("Ctrl+,"))
        act_settings.triggered.connect(lambda: self._navigate_to(6))
        edit_menu.addAction(act_settings)

        # View Menu
        view_menu = menu_bar.addMenu("&View")

        act_v_dash = QAction("&Dashboard", self)
        act_v_dash.setShortcut(QKeySequence("F1"))
        act_v_dash.triggered.connect(lambda: self._navigate_to(0))
        view_menu.addAction(act_v_dash)

        act_v_new = QAction("&Verify Student Paper", self)
        act_v_new.setShortcut(QKeySequence("F2"))
        act_v_new.triggered.connect(lambda: self._navigate_to(1))
        view_menu.addAction(act_v_new)

        act_v_docs = QAction("&Student Records Archive", self)
        act_v_docs.setShortcut(QKeySequence("F3"))
        act_v_docs.triggered.connect(lambda: self._navigate_to(2))
        view_menu.addAction(act_v_docs)

        act_v_res = QAction("&Similarity Results & Certificate", self)
        act_v_res.setShortcut(QKeySequence("F4"))
        act_v_res.triggered.connect(lambda: self._navigate_to(3))
        view_menu.addAction(act_v_res)

        act_v_src = QAction("Reference &Source Library", self)
        act_v_src.setShortcut(QKeySequence("F5"))
        act_v_src.triggered.connect(lambda: self._navigate_to(5))
        view_menu.addAction(act_v_src)

        view_menu.addSeparator()

        act_theme = QAction("Toggle &Light / Dark Theme", self)
        act_theme.triggered.connect(self._toggle_theme)
        view_menu.addAction(act_theme)

        # Tools Menu
        tools_menu = menu_bar.addMenu("&Tools")

        act_refresh_lib = QAction("&Refresh Comparison Corpora", self)
        act_refresh_lib.triggered.connect(lambda: self.view_sources.refresh_list())
        tools_menu.addAction(act_refresh_lib)

        act_db_check = QAction("&Database Integrity Check", self)
        act_db_check.triggered.connect(self._check_database_integrity)
        tools_menu.addAction(act_db_check)

        # Reports Menu
        reports_menu = menu_bar.addMenu("&Reports")

        act_r_cert = QAction("Official IMRD Clearance &Certificate (PDF)", self)
        act_r_cert.triggered.connect(lambda: self.view_results._export_pdf())
        reports_menu.addAction(act_r_cert)

        act_r_html = QAction("Interactive &HTML Audit Report", self)
        act_r_html.triggered.connect(lambda: self.view_results._export_html())
        reports_menu.addAction(act_r_html)

        # Help Menu
        help_menu = menu_bar.addMenu("&Help")

        act_sop = QAction("&Librarian Verification SOP", self)
        act_sop.triggered.connect(lambda: self._navigate_to(7))
        help_menu.addAction(act_sop)

        act_ugc = QAction("&UGC 2018 Plagiarism Regulations Guide", self)
        act_ugc.triggered.connect(lambda: self._navigate_to(7))
        help_menu.addAction(act_ugc)

        help_menu.addSeparator()

        act_about = QAction("&About IMRD ResearchGuard...", self)
        act_about.triggered.connect(self._show_about_dialog)
        help_menu.addAction(act_about)

    def _create_institutional_header(self) -> QFrame:
        """Creates the formal college banner featuring IMRD Shirpur credentials."""
        hdr = QFrame()
        hdr.setObjectName("instHeader")
        layout = QHBoxLayout(hdr)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(12)

        # College Logo
        logo_path = BASE_DIR / "resources" / "app_icon.png"
        if not logo_path.exists():
            logo_path = BASE_DIR / "Logo.png"

        logo_lbl = QLabel()
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path)).scaled(44, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pixmap)
        else:
            logo_lbl.setText("IMRD")
            logo_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #FFFFFF;")
        logo_lbl.setFixedWidth(48)
        layout.addWidget(logo_lbl)

        # College Title & Accreditation
        title_box = QVBoxLayout()
        title_box.setSpacing(1)

        t1 = QLabel(INSTITUTION_NAME.upper())
        t1.setStyleSheet("color: #FFFFFF; font-size: 12.5px; font-weight: 800; letter-spacing: 0.3px;")

        t2 = QLabel(f"{AFFILIATION_TEXT} • Central Library Verification Cell")
        t2.setStyleSheet("color: #FDE68A; font-size: 10.5px; font-weight: 600;")

        title_box.addWidget(t1)
        title_box.addWidget(t2)
        layout.addLayout(title_box, 1)

        layout.addStretch()

        # Action controls on the right side of header: Theme toggle and Engine status
        self.theme_btn = QPushButton("Theme: " + self._active_theme.capitalize())
        self.theme_btn.setObjectName("headerBtn")
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.clicked.connect(self._toggle_theme)
        layout.addWidget(self.theme_btn)

        # Status indicator pill
        status_pill = QLabel("● Engine Ready")
        status_pill.setObjectName("statusPill")
        layout.addWidget(status_pill)

        return hdr

    def _create_sidebar(self) -> QFrame:
        """Creates clean Windows desktop sidebar navigation without casual emojis."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(235)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(6, 12, 6, 12)
        layout.setSpacing(3)

        nav_header = QLabel("CENTRAL LIBRARY MODULES")
        nav_header.setStyleSheet("color: #64748B; font-size: 10px; font-weight: 800; padding: 6px 12px 4px 12px; letter-spacing: 0.5px;")
        layout.addWidget(nav_header)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        nav_items = [
            ("Dashboard", 0),
            ("Verify Student Paper", 1),
            ("Student Records Archive", 2),
            ("Similarity Results", 3),
            ("Reference Source Library", 5),
            ("Institutional Settings", 6),
            ("Librarian SOP & Guidelines", 7),
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

        # Institutional Central Library Badge
        lib_box = QFrame()
        lib_box.setObjectName("sidebarLibBadge")
        lb_layout = QVBoxLayout(lib_box)
        lb_layout.setContentsMargins(8, 8, 8, 8)
        lb_layout.setSpacing(2)
        lb_title = QLabel("IMRD Central Library")
        lb_title.setStyleSheet("font-size: 11px; font-weight: 700; color: #002461;")
        lb_sub = QLabel("Plagiarism Cell • Offline Engine")
        lb_sub.setStyleSheet("font-size: 9.5px; color: #64748B;")
        lb_layout.addWidget(lb_title)
        lb_layout.addWidget(lb_sub)
        layout.addWidget(lib_box)

        # Default select Dashboard
        self.nav_buttons[0].setChecked(True)
        return sidebar

    def _navigate_to(self, index: int):
        self.stack.setCurrentIndex(index)
        if index in self.nav_buttons:
            self.nav_buttons[index].setChecked(True)

        # Refresh destination views
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
        set_setting("theme", theme_name)
        self.setStyleSheet(get_theme_stylesheet(theme_name))
        self.theme_btn.setText("Theme: " + theme_name.capitalize())

    def _open_document_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Student Dissertation / Research Paper",
            "",
            "Academic Documents (*.pdf *.docx *.txt);;PDF Files (*.pdf);;Word Documents (*.docx)",
        )
        if file_path:
            self._navigate_to(1)
            self.view_new_check._add_files_to_queue([file_path])

    def _on_analysis_finished(self, result_and_id):
        result, doc_id = result_and_id
        self.view_results.load_result(result, doc_id)
        self._navigate_to(3)

    def _on_open_match_viewer(self, data_dict):
        self.view_match_viewer.load_data(data_dict)
        self._navigate_to(4)

    def _load_document_into_results(self, doc_id: int):
        """Loads an archived student record from SQLite into the Results view."""
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

            # Student metadata
            res.student_name = doc.student_name or "Student"
            res.prn_number = doc.prn_number or "-"
            res.course_name = doc.course_name or "MCA"
            res.academic_year = doc.academic_year or "2025-2026"
            res.semester = doc.semester or "Semester IV"
            res.guide_name = doc.guide_name or "-"
            res.paper_title = doc.paper_title or doc.filename
            res.clearance_status = doc.clearance_status or "Approved (Level 0)"
            res.certificate_no = doc.certificate_no or f"IMRD/LIB/{doc.id:04d}"

            try:
                res.structure = json.loads(doc.structure_json) if doc.structure_json else {}
            except Exception:
                res.structure = {}

            @dataclass
            class MockCit:
                citation_count: int = 0
                reference_count: int = 0
                quotes: list = None
                uncited_claims: int = 0

            res.citations = MockCit(quotes=[])

            @dataclass
            class MockAI:
                likelihood: str = "Low"
                score: float = 10.0

            res.ai_writing = MockAI(likelihood=doc.ai_likelihood or "Low")

            self.view_results.load_result(res, doc_id)
            self._navigate_to(3)

    def _check_database_integrity(self):
        with get_db() as session:
            count = session.query(Document).count()
        QMessageBox.information(
            self,
            "Database Status",
            f"Central Library SQLite Database is operational.\n\n"
            f"• Verified Student Records: {count}\n"
            f"• Schema: IMRD Shirpur Academic Integrity Standard v1.0",
        )

    def _show_about_dialog(self):
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<b>{APP_NAME} v{APP_VERSION}</b><br/>"
            f"<b>SES's R. C. Patel Institute of Management Research and Development, Shirpur</b><br/>"
            f"{AFFILIATION_TEXT}<br/><br/>"
            f"<b>Department:</b> {LIBRARY_DEPARTMENT}<br/>"
            f"Developed for verification of student project reports, dissertations, and research papers "
            f"in compliance with UGC Plagiarism Regulations, 2018."
        )
