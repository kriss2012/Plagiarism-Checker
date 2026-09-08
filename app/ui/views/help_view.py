"""Help and academic integrity guide view.
Tailored for Central Library verification officers at SES's R. C. Patel IMRD Shirpur.
Contains Librarian SOP, UGC 2018 regulations, methodology, and diagnostics.
"""

import platform
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from app.config import (
    ACADEMIC_DISCLAIMER,
    AFFILIATION_TEXT,
    APP_NAME,
    APP_VERSION,
    INSTITUTION_NAME,
    INSTITUTION_SHORT,
)
from app.ml.semantic import get_model_status_text


class HelpView(QWidget):
    """Provides documentation, Librarian SOP, UGC Plagiarism guidelines, and system diagnostics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(14)

        # Header
        h_box = QVBoxLayout()
        title = QLabel(f"{INSTITUTION_SHORT} Central Library • Plagiarism Verification SOP & Guidelines")
        title.setStyleSheet("font-size: 19px; font-weight: 800; color: #002461;")
        sub = QLabel(f"{INSTITUTION_NAME} • {AFFILIATION_TEXT} • System v{APP_VERSION}")
        sub.setStyleSheet("font-size: 12px; color: #64748B;")
        h_box.addWidget(title)
        h_box.addWidget(sub)
        layout.addLayout(h_box)

        # 1. Central Library Verification SOP Card
        sop_card = QFrame()
        sop_card.setObjectName("card")
        sop_box = QVBoxLayout(sop_card)
        sop_title = QLabel("LIBRARIAN STANDARD OPERATING PROCEDURE (SOP) FOR STUDENT PAPERS")
        sop_title.setStyleSheet("font-weight: 800; font-size: 12px; margin-bottom: 4px;")
        sop_box.addWidget(sop_title)

        sop_html = """
        <p><b>Step 1: Student Intake & Submission</b><br/>
        Enter the student's Full Name, University PRN / Roll Number, Program (MCA, MBA, BCA, BBA, Integrated MCA), 
        Academic Year, Semester, and Project Supervisor Name in the <i>'Verify Student Paper'</i> module.</p>

        <p><b>Step 2: Paper File Selection</b><br/>
        Load the final draft dissertation or project report (.PDF or .DOCX format). The system pre-extracts word count and page count.</p>

        <p><b>Step 3: Verification Parameters & UGC Exclusions</b><br/>
        Ensure <i>'Exclude References & Bibliography'</i> and <i>'Exclude Quoted Passages'</i> remain checked as mandated by UGC Regulations 2018 Section 6.1.</p>

        <p><b>Step 4: Audit & Certificate Issuance</b><br/>
        Review the similarity percentage and UGC compliance tier. If similarity is <b><= 10.0% (Level 0)</b>, click 
        <i>'Print IMRD Clearance Certificate (PDF)'</i>. The official certificate will be generated on college letterhead with signature blocks 
        for the Student, Research Guide, and Librarian.</p>
        """
        lbl_sop = QLabel(sop_html)
        lbl_sop.setStyleSheet("font-size: 12px; line-height: 1.5;")
        lbl_sop.setWordWrap(True)
        sop_box.addWidget(lbl_sop)
        layout.addWidget(sop_card)

        # 2. UGC Regulations 2018 Compliance Tiers Card
        ugc_card = QFrame()
        ugc_card.setObjectName("card")
        ugc_box = QVBoxLayout(ugc_card)
        ugc_title = QLabel("UGC PLAGIARISM REGULATIONS 2018 – PENALTY & COMPLIANCE TIERS")
        ugc_title.setStyleSheet("font-weight: 800; font-size: 12px; margin-bottom: 4px;")
        ugc_box.addWidget(ugc_title)

        ugc_html = """
        <table width='100%' cellpadding='4' cellspacing='0' style='border-collapse: collapse;'>
            <tr>
                <th align='left'><b>UGC Level</b></th>
                <th align='left'><b>Similarity Range</b></th>
                <th align='left'><b>Institutional Action / Recommendation</b></th>
            </tr>
            <tr>
                <td><b>Level 0</b></td>
                <td><b>Similarities up to 10.0%</b></td>
                <td>Minor textual overlap. <b>Permitted for final thesis submission and evaluation. Clearance granted.</b></td>
            </tr>
            <tr>
                <td><b>Level 1</b></td>
                <td><b>Similarities above 10.0% to 40.0%</b></td>
                <td>Student must be asked to submit a revised script within a stipulated time-period not exceeding 6 months.</td>
            </tr>
            <tr>
                <td><b>Level 2</b></td>
                <td><b>Similarities above 40.0% to 60.0%</b></td>
                <td>Student shall be debarred from submitting a revised script for a period of one year.</td>
            </tr>
            <tr>
                <td><b>Level 3</b></td>
                <td><b>Similarities above 60.0%</b></td>
                <td>Severe academic misconduct. Student registration for that program shall be cancelled.</td>
            </tr>
        </table>
        """
        lbl_ugc = QLabel(ugc_html)
        lbl_ugc.setStyleSheet("font-size: 11.5px; line-height: 1.5;")
        lbl_ugc.setWordWrap(True)
        ugc_box.addWidget(lbl_ugc)
        layout.addWidget(ugc_card)

        # 3. Detection Methodology Card
        meth_card = QFrame()
        meth_card.setObjectName("card")
        m_box = QVBoxLayout(meth_card)
        m_title = QLabel("SIMILARITY DETECTION ALGORITHMIC PIPELINE")
        m_title.setStyleSheet("font-weight: 800; font-size: 12px; margin-bottom: 4px;")
        m_box.addWidget(m_title)

        method_text = """
        <p><b>1. Exact Matching (Hash & N-Gram Containment):</b> Identifies verbatim duplication using rolling SHA-256 sentence hashing and canonical token normalization.</p>
        <p><b>2. Fuzzy Matching (RapidFuzz Token Set Ratio):</b> Detects minor syntactic alterations, word substitutions, and shallow paraphrasing using Levenshtein distance metrics.</p>
        <p><b>3. Semantic Similarity (Sentence-Transformers all-MiniLM-L6-v2):</b> Projects sentences into vector space to recognize deep conceptual paraphrasing where meaning is preserved but phrasing is altered.</p>
        <p><b>4. Quotation & Citation Isolation:</b> Standard IEEE [1] and APA/Harvard citations enclosed in quotation marks are excluded from uncredited plagiarism.</p>
        <p><b>5. References Section Exclusion:</b> Detects bibliography and reference entries and excludes them from inflating the body similarity index.</p>
        """
        lbl_meth = QLabel(method_text)
        lbl_meth.setStyleSheet("font-size: 11.5px; line-height: 1.5;")
        lbl_meth.setWordWrap(True)
        m_box.addWidget(lbl_meth)
        layout.addWidget(meth_card)

        # 4. Academic Ethics & Disclaimer
        disc_frame = QFrame()
        disc_frame.setObjectName("card")
        d_box = QVBoxLayout(disc_frame)
        d_title = QLabel("ACADEMIC ETHICS & DISCLAIMER NOTICE")
        d_title.setStyleSheet("font-weight: 800; font-size: 11px;")
        d_desc = QLabel(ACADEMIC_DISCLAIMER)
        d_desc.setStyleSheet("font-size: 11px; line-height: 1.4;")
        d_desc.setWordWrap(True)
        d_box.addWidget(d_title)
        d_box.addWidget(d_desc)
        layout.addWidget(disc_frame)

        # 5. Diagnostics Card
        diag_card = QFrame()
        diag_card.setObjectName("card")
        diag_box = QVBoxLayout(diag_card)
        diag_title = QLabel("CENTRAL LIBRARY SYSTEM & RUNTIME DIAGNOSTICS")
        diag_title.setStyleSheet("font-weight: 800; font-size: 11px; margin-bottom: 4px;")
        diag_box.addWidget(diag_title)

        diag_html = f"""
        <b>Institution:</b> {INSTITUTION_NAME}<br/>
        <b>Platform:</b> {platform.system()} {platform.release()} ({platform.machine()})<br/>
        <b>Python Engine:</b> {platform.python_version()}<br/>
        <b>NLP Semantic Engine:</b> {get_model_status_text()}<br/>
        <b>Database:</b> SQLite 3 Local Persistence (Offline-First)<br/>
        """
        lbl_diag = QLabel(diag_html)
        lbl_diag.setStyleSheet("font-size: 11px; line-height: 1.5;")
        lbl_diag.setWordWrap(True)
        diag_box.addWidget(lbl_diag)
        layout.addWidget(diag_card)

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
