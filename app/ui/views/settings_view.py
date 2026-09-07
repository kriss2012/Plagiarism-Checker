"""Settings view providing comprehensive configuration tabs for analysis, documents, reports, and privacy."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from app.config import DATABASE_PATH, DEFAULT_SETTINGS
from app.database.session import get_all_settings, get_setting, set_setting


class SettingsView(QWidget):
    """Configuration control panel for ResearchGuard application parameters."""

    theme_changed = Signal(str)  # "dark" or "light"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.load_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        h_box = QVBoxLayout()
        title = QLabel("System Settings & Heuristics Configuration")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #FFFFFF;")
        sub = QLabel("Customize similarity detection sensitivity, reporting templates, and privacy policies")
        sub.setStyleSheet("font-size: 13px; color: #94A3B8;")
        h_box.addWidget(title)
        h_box.addWidget(sub)
        layout.addLayout(h_box)

        # Tabs
        self.tabs = QTabWidget()

        # ================= TAB 1: GENERAL =================
        tab_gen = QWidget()
        form_gen = QFormLayout(tab_gen)
        form_gen.setContentsMargins(20, 20, 20, 20)
        form_gen.setSpacing(14)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark Mode", "Light Mode"])
        form_gen.addRow("UI Appearance Theme:", self.theme_combo)

        self.chk_auto_save = QCheckBox("Automatically archive generated reports")
        form_gen.addRow("Report Archiving:", self.chk_auto_save)

        self.chk_confirm_del = QCheckBox("Ask for confirmation before deleting documents or sources")
        form_gen.addRow("Deletion Safety:", self.chk_confirm_del)

        self.tabs.addTab(tab_gen, "General")

        # ================= TAB 2: ANALYSIS THRESHOLDS =================
        tab_ana = QWidget()
        form_ana = QFormLayout(tab_ana)
        form_ana.setContentsMargins(20, 20, 20, 20)
        form_ana.setSpacing(14)

        self.spin_fuzzy_thresh = QDoubleSpinBox()
        self.spin_fuzzy_thresh.setRange(50.0, 99.0)
        self.spin_fuzzy_thresh.setSingleStep(5.0)
        self.spin_fuzzy_thresh.setSuffix("%")
        form_ana.addRow("Fuzzy Similarity Threshold (RapidFuzz):", self.spin_fuzzy_thresh)

        self.spin_sem_thresh = QDoubleSpinBox()
        self.spin_sem_thresh.setRange(50.0, 95.0)
        self.spin_sem_thresh.setSingleStep(5.0)
        self.spin_sem_thresh.setSuffix("%")
        form_ana.addRow("Semantic Similarity Threshold (Cosine):", self.spin_sem_thresh)

        self.spin_min_words = QSpinBox()
        self.spin_min_words.setRange(3, 20)
        form_ana.addRow("Minimum Sentence Word Count to Flag:", self.spin_min_words)

        self.chk_filter_common = QCheckBox("Filter generic academic phrases (e.g., 'the results indicate')")
        form_ana.addRow("Academic Cliché Filter:", self.chk_filter_common)

        self.tabs.addTab(tab_ana, "Analysis & Heuristics")

        # ================= TAB 3: DOCUMENTS & EXTRACTION =================
        tab_doc = QWidget()
        form_doc = QFormLayout(tab_doc)
        form_doc.setContentsMargins(20, 20, 20, 20)
        form_doc.setSpacing(14)

        self.spin_max_file_size = QSpinBox()
        self.spin_max_file_size.setRange(5, 500)
        self.spin_max_file_size.setSuffix(" MB")
        form_doc.addRow("Maximum File Size Allowed:", self.spin_max_file_size)

        self.chk_ocr = QCheckBox("Enable OCR for Scanned Documents (Optional Tesseract)")
        form_doc.addRow("OCR Processing:", self.chk_ocr)

        self.chk_ex_ref_default = QCheckBox("Exclude References / Bibliography by Default")
        form_doc.addRow("Bibliography Handling:", self.chk_ex_ref_default)

        self.chk_ex_quote_default = QCheckBox("Exclude Quoted Text from Similarity Score")
        form_doc.addRow("Quotation Handling:", self.chk_ex_quote_default)

        self.tabs.addTab(tab_doc, "Documents & Parsers")

        # ================= TAB 4: REPORTS & INSTITUTION =================
        tab_rep = QWidget()
        form_rep = QFormLayout(tab_rep)
        form_rep.setContentsMargins(20, 20, 20, 20)
        form_rep.setSpacing(14)

        self.inst_name_input = QLineEdit()
        form_rep.addRow("Institution / University Name:", self.inst_name_input)

        self.dept_name_input = QLineEdit()
        form_rep.addRow("Department / Faculty:", self.dept_name_input)

        self.researcher_name_input = QLineEdit()
        form_rep.addRow("Default Researcher Name:", self.researcher_name_input)

        self.supervisor_name_input = QLineEdit()
        form_rep.addRow("Default Supervisor / Guide:", self.supervisor_name_input)

        self.tabs.addTab(tab_rep, "Report Branding")

        # ================= TAB 5: PRIVACY & NETWORK =================
        tab_priv = QWidget()
        v_priv = QVBoxLayout(tab_priv)
        v_priv.setContentsMargins(20, 20, 20, 20)
        v_priv.setSpacing(14)

        priv_banner = QFrame()
        priv_banner.setStyleSheet("""
            QFrame {
                background-color: rgba(16, 185, 129, 0.1);
                border: 1px solid #10B981;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        pb_box = QVBoxLayout(priv_banner)
        pb_title = QLabel("🔒 OFFLINE-FIRST PRIVACY GUARANTEE")
        pb_title.setStyleSheet("font-weight: 800; color: #10B981; font-size: 14px;")
        pb_desc = QLabel(
            "Your research papers are analyzed entirely on this local workstation. "
            "No document content is uploaded to external clouds, commercial third-party LLMs, "
            "or unauthorized indexing engines."
        )
        pb_desc.setStyleSheet("color: #E2E8F0; font-size: 12px;")
        pb_desc.setWordWrap(True)
        pb_box.addWidget(pb_title)
        pb_box.addWidget(pb_desc)
        v_priv.addWidget(priv_banner)

        form_priv = QFormLayout()
        self.chk_offline_mode = QCheckBox("Enforce Strict Offline Mode (Disable all external network calls)")
        form_priv.addRow("Network Access:", self.chk_offline_mode)

        db_path_lbl = QLabel(str(DATABASE_PATH))
        db_path_lbl.setStyleSheet("color: #94A3B8; font-family: monospace; font-size: 11px;")
        form_priv.addRow("Local Database File:", db_path_lbl)
        v_priv.addLayout(form_priv)
        v_priv.addStretch()

        self.tabs.addTab(tab_priv, "Privacy & Data")

        layout.addWidget(self.tabs)

        # Save Button
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.save_btn = QPushButton("Save Settings")
        self.save_btn.setObjectName("primaryBtn")
        self.save_btn.setMinimumHeight(38)
        self.save_btn.setMinimumWidth(140)
        self.save_btn.clicked.connect(self.save_settings)
        btn_box.addWidget(self.save_btn)

        layout.addLayout(btn_box)

    def load_settings(self):
        """Populates form controls with current persistent settings."""
        settings = get_all_settings()

        # General
        th = settings.get("theme", "dark")
        self.theme_combo.setCurrentIndex(0 if th == "dark" else 1)
        self.chk_auto_save.setChecked(bool(settings.get("auto_save_reports", True)))
        self.chk_confirm_del.setChecked(bool(settings.get("confirm_deletion", True)))

        # Analysis
        self.spin_fuzzy_thresh.setValue(float(settings.get("fuzzy_similarity_threshold", 80.0)))
        self.spin_sem_thresh.setValue(float(settings.get("semantic_similarity_threshold", 75.0)))
        self.spin_min_words.setValue(int(settings.get("min_word_count_to_flag", 4)))
        self.chk_filter_common.setChecked(bool(settings.get("filter_common_phrases", True)))

        # Documents
        self.spin_max_file_size.setValue(int(settings.get("max_file_size_mb", 50)))
        self.chk_ocr.setChecked(bool(settings.get("ocr_enabled", False)))
        self.chk_ex_ref_default.setChecked(bool(settings.get("exclude_references", True)))
        self.chk_ex_quote_default.setChecked(bool(settings.get("exclude_quotes", True)))

        # Reports
        self.inst_name_input.setText(str(settings.get("institution_name", "University / Academic Department")))
        self.dept_name_input.setText(str(settings.get("department_name", "Department of Computer Science & Engineering")))
        self.researcher_name_input.setText(str(settings.get("researcher_name", "Student / Researcher")))
        self.supervisor_name_input.setText(str(settings.get("supervisor_name", "Research Advisor")))

        # Privacy
        self.chk_offline_mode.setChecked(bool(settings.get("offline_mode", True)))

    def save_settings(self):
        """Persists all modified settings to database."""
        chosen_theme = "dark" if self.theme_combo.currentIndex() == 0 else "light"
        set_setting("theme", chosen_theme)
        set_setting("auto_save_reports", self.chk_auto_save.isChecked())
        set_setting("confirm_deletion", self.chk_confirm_del.isChecked())

        set_setting("fuzzy_similarity_threshold", self.spin_fuzzy_thresh.value())
        set_setting("semantic_similarity_threshold", self.spin_sem_thresh.value())
        set_setting("min_word_count_to_flag", self.spin_min_words.value())
        set_setting("filter_common_phrases", self.chk_filter_common.isChecked())

        set_setting("max_file_size_mb", self.spin_max_file_size.value())
        set_setting("ocr_enabled", self.chk_ocr.isChecked())
        set_setting("exclude_references", self.chk_ex_ref_default.isChecked())
        set_setting("exclude_quotes", self.chk_ex_quote_default.isChecked())

        set_setting("institution_name", self.inst_name_input.text().strip())
        set_setting("department_name", self.dept_name_input.text().strip())
        set_setting("researcher_name", self.researcher_name_input.text().strip())
        set_setting("supervisor_name", self.supervisor_name_input.text().strip())

        set_setting("offline_mode", self.chk_offline_mode.isChecked())

        self.theme_changed.emit(chosen_theme)
        QMessageBox.information(self, "Settings Saved", "Application settings have been updated successfully.")
