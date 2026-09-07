"""Help and academic integrity guide view."""

import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from app.config import ACADEMIC_DISCLAIMER, APP_NAME, APP_VERSION
from app.ml.semantic import get_model_status_text


class HelpView(QWidget):
    """Provides documentation, plagiarism methodology explanations, and system diagnostics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # Header
        h_box = QVBoxLayout()
        title = QLabel(f"{APP_NAME} – Documentation & Academic Guide")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #FFFFFF;")
        sub = QLabel(f"Version {APP_VERSION} • Methodological documentation and academic ethics standards")
        sub.setStyleSheet("font-size: 13px; color: #94A3B8;")
        h_box.addWidget(title)
        h_box.addWidget(sub)
        layout.addLayout(h_box)

        # Academic Disclaimer Highlight
        disc_frame = QFrame()
        disc_frame.setObjectName("card")
        disc_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(245, 158, 11, 0.1);
                border: 1px solid #F59E0B;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        d_box = QVBoxLayout(disc_frame)
        d_title = QLabel("⚠️ MANDATORY ACADEMIC ETHICS & DISCLAIMER NOTICE")
        d_title.setStyleSheet("font-weight: 800; color: #F59E0B; font-size: 14px;")
        d_desc = QLabel(ACADEMIC_DISCLAIMER)
        d_desc.setStyleSheet("color: #FDE68A; font-size: 13px; line-height: 1.5;")
        d_desc.setWordWrap(True)
        d_box.addWidget(d_title)
        d_box.addWidget(d_desc)
        layout.addWidget(disc_frame)

        # Detection Methodology Section
        meth_card = QFrame()
        meth_card.setObjectName("card")
        m_box = QVBoxLayout(meth_card)
        m_title = QLabel("PLAGIARISM & SIMILARITY DETECTION METHODOLOGY")
        m_title.setStyleSheet("font-weight: 700; color: #818CF8; font-size: 14px; margin-bottom: 8px;")
        m_box.addWidget(m_title)

        method_text = """
        <p><b>1. Exact Matching (Hash & N-gram Overlap):</b><br/>
        Identifies verbatim copying using rolling cryptographic SHA-256 sentence hashing. Even if punctuation is altered, normalized canonical token strings detect exact sentence duplication.</p>

        <p><b>2. Fuzzy Matching (RapidFuzz Token Set Ratio):</b><br/>
        Detects minor modifications, word substitutions, reorderings, and light paraphrasing using Levenshtein distance metrics. Identifies instances where sentence structure has been superficially tweaked.</p>

        <p><b>3. Semantic Similarity (Sentence-Transformers all-MiniLM-L6-v2):</b><br/>
        Generates dense vector embeddings of individual sentences and compares cosine angle similarities. Detects conceptual paraphrasing where vocabulary is completely different but intellectual semantics remain identical.</p>

        <p><b>4. Quotation and Citation Isolation:</b><br/>
        Recognizes academic formatting standards (IEEE [1], APA/Harvard author-year) and isolates text enclosed in quotation marks. If content is quoted and accompanied by an adjacent citation, it is cataloged as <i>'Quoted / Cited Content'</i> rather than uncredited plagiarism.</p>

        <p><b>5. References Section Exclusion:</b><br/>
        Academic papers naturally duplicate bibliographies and citation entries. ResearchGuard automatically detects the start of the References/Bibliography section and excludes it from inflating the main body similarity score.</p>
        """
        lbl_meth = QLabel(method_text)
        lbl_meth.setStyleSheet("color: #CBD5E1; font-size: 13px; line-height: 1.6;")
        lbl_meth.setWordWrap(True)
        m_box.addWidget(lbl_meth)
        layout.addWidget(meth_card)

        # System Diagnostics Card
        diag_card = QFrame()
        diag_card.setObjectName("card")
        diag_box = QVBoxLayout(diag_card)
        diag_title = QLabel("SYSTEM & RUNTIME DIAGNOSTICS")
        diag_title.setStyleSheet("font-weight: 700; color: #10B981; font-size: 14px; margin-bottom: 8px;")
        diag_box.addWidget(diag_title)

        import platform
        diag_html = f"""
        <b>Operating System:</b> {platform.system()} {platform.release()} ({platform.machine()})<br/>
        <b>Python Engine:</b> {platform.python_version()} ({platform.python_implementation()})<br/>
        <b>NLP Semantic Model:</b> {get_model_status_text()}<br/>
        <b>Execution Architecture:</b> 64-bit Desktop GUI Application<br/>
        <b>Storage Engine:</b> SQLite 3 with SQLAlchemy ORM Persistence<br/>
        """
        lbl_diag = QLabel(diag_html)
        lbl_diag.setStyleSheet("color: #94A3B8; font-size: 12px; line-height: 1.6;")
        lbl_diag.setWordWrap(True)
        diag_box.addWidget(lbl_diag)
        layout.addWidget(diag_card)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
