"""Plagiarism verification results view presenting UGC compliance status, similarity metrics, and clearance certificate actions."""

from pathlib import Path
from typing import Dict, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from app.config import ACADEMIC_DISCLAIMER, REPORTS_DIR
from app.reports.html_generator import HTMLReportGenerator
from app.reports.pdf_generator import PDFReportGenerator
from app.ui.widgets.cards import EmptyStateWidget, MetricCard, RiskBadge
from app.ui.widgets.charts import SimilarityGaugeWidget
from app.utils.logger import logger


class ResultsView(QWidget):
    """Presents verification results, UGC compliance tier, and prints the official clearance certificate."""

    open_match_viewer = Signal(dict)
    start_check_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_result = None
        self._doc_id = None
        self._init_ui()

    def _init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget(self)

        # Page 0: Empty State
        empty_container = QWidget()
        empty_layout = QVBoxLayout(empty_container)
        empty_layout.setContentsMargins(24, 40, 24, 40)
        self.empty_state = EmptyStateWidget(
            title="No Active Verification Results",
            message="No dissertation verification has been conducted in this session. Select an archived student paper from 'Student Records Archive' or verify a new draft in 'Verify Student Paper'.",
            parent=empty_container,
        )
        empty_layout.addWidget(self.empty_state)
        self.stack.addWidget(empty_container)

        # Page 1: Results Content Scroll Area
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(14)

        # 1. Header with Student Metadata Summary & Action Buttons
        h_layout = QHBoxLayout()
        v_title = QVBoxLayout()
        v_title.setSpacing(2)

        self.title_lbl = QLabel("Student Dissertation Plagiarism Verification & Clearance")
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #002461;")
        
        self.student_bar_lbl = QLabel("Student: - • PRN: - • Program: -")
        self.student_bar_lbl.setStyleSheet("font-size: 11.5px; font-weight: 600; color: #005FEA;")
        
        self.file_lbl = QLabel("Document: - • Words: 0 • Pages: 0")
        self.file_lbl.setStyleSheet("font-size: 11px; color: #64748B;")

        v_title.addWidget(self.title_lbl)
        v_title.addWidget(self.student_bar_lbl)
        v_title.addWidget(self.file_lbl)
        h_layout.addLayout(v_title, 1)

        # Action Buttons
        self.export_cert_btn = QPushButton("Print Clearance Certificate (PDF)")
        self.export_cert_btn.setObjectName("certBtn")
        self.export_cert_btn.setFixedHeight(34)
        self.export_cert_btn.setMinimumWidth(210)
        self.export_cert_btn.setCursor(Qt.PointingHandCursor)
        self.export_cert_btn.clicked.connect(self._export_pdf)
        h_layout.addWidget(self.export_cert_btn)

        self.inspect_btn = QPushButton("Inspect Matches")
        self.inspect_btn.setObjectName("primaryBtn")
        self.inspect_btn.setFixedHeight(34)
        self.inspect_btn.setMinimumWidth(120)
        self.inspect_btn.setCursor(Qt.PointingHandCursor)
        self.inspect_btn.clicked.connect(self._on_inspect_clicked)
        h_layout.addWidget(self.inspect_btn)

        self.export_html_btn = QPushButton("HTML Audit Report")
        self.export_html_btn.setFixedHeight(34)
        self.export_html_btn.setMinimumWidth(140)
        self.export_html_btn.setCursor(Qt.PointingHandCursor)
        self.export_html_btn.clicked.connect(self._export_html)
        h_layout.addWidget(self.export_html_btn)

        layout.addLayout(h_layout)

        # 2. UGC Regulation 2018 Compliance Status Card
        self.ugc_frame = QFrame()
        self.ugc_frame.setObjectName("card")
        self.ugc_layout = QHBoxLayout(self.ugc_frame)
        self.ugc_layout.setContentsMargins(14, 10, 14, 10)

        self.ugc_badge = QLabel("UGC LEVEL 0: CLEARED")
        self.ugc_badge.setStyleSheet("""
            background-color: #ECFDF5;
            color: #047857;
            border: 1.5px solid #10B981;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 800;
            padding: 6px 12px;
        """)
        self.ugc_layout.addWidget(self.ugc_badge)

        self.ugc_desc = QLabel(
            "Overall similarity is within the 10.0% permissible threshold under UGC (Promotion of Academic Integrity "
            "and Prevention of Plagiarism in Higher Educational Institutions) Regulations, 2018. Student is eligible for clearance."
        )
        self.ugc_desc.setStyleSheet("color: #0F172A; font-size: 11.5px; font-weight: 500;")
        self.ugc_desc.setWordWrap(True)
        self.ugc_layout.addWidget(self.ugc_desc, 1)

        layout.addWidget(self.ugc_frame)

        # 3. Top Metrics: Gauge & Breakdown Cards
        top_grid = QHBoxLayout()
        top_grid.setSpacing(14)

        gauge_card = QFrame()
        gauge_card.setObjectName("card")
        g_box = QVBoxLayout(gauge_card)
        g_box.setAlignment(Qt.AlignCenter)
        
        g_lbl = QLabel("OVERALL SIMILARITY INDEX")
        g_lbl.setStyleSheet("color: #002461; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        g_box.addWidget(g_lbl, alignment=Qt.AlignCenter)
        
        self.gauge = SimilarityGaugeWidget()
        g_box.addWidget(self.gauge, alignment=Qt.AlignCenter)
        
        self.risk_badge = RiskBadge("Very Low")
        self.risk_badge.setFixedWidth(140)
        g_box.addWidget(self.risk_badge, alignment=Qt.AlignCenter)
        top_grid.addWidget(gauge_card, 1)

        # Metric Cards
        metrics_col = QVBoxLayout()
        metrics_col.setSpacing(8)

        self.card_exact = MetricCard("Exact Overlap", "0", "Direct identical phrasing", "#EF4444")
        self.card_fuzzy = MetricCard("Paraphrased / Fuzzy", "0", "High lexical similarity", "#F59E0B")
        self.card_semantic = MetricCard("Semantic Proximity", "0", "Topical / concept match", "#8B5CF6")
        self.card_quoted = MetricCard("Quoted / Cited", "0", "Legitimate academic quotes", "#0284C7")

        row1 = QHBoxLayout()
        row1.setSpacing(8)
        row1.addWidget(self.card_exact)
        row1.addWidget(self.card_fuzzy)
        metrics_col.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(8)
        row2.addWidget(self.card_semantic)
        row2.addWidget(self.card_quoted)
        metrics_col.addLayout(row2)

        top_grid.addLayout(metrics_col, 2)
        layout.addLayout(top_grid)

        # 4. Details Split: Paper Structure vs Citations & AI Heuristics
        details_row = QHBoxLayout()
        details_row.setSpacing(14)

        # Structure Parser Card
        struct_card = QFrame()
        struct_card.setObjectName("card")
        sb_layout = QVBoxLayout(struct_card)
        sb_layout.setSpacing(6)
        sb_title = QLabel("DISSERTATION STRUCTURE RECOGNITION")
        sb_title.setStyleSheet("color: #002461; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        sb_layout.addWidget(sb_title)
        self.structure_text = QLabel("Analyzing document structure...")
        self.structure_text.setStyleSheet("font-size: 12px; color: #334155; line-height: 1.4;")
        self.structure_text.setWordWrap(True)
        sb_layout.addWidget(self.structure_text)
        details_row.addWidget(struct_card, 1)

        # Citations & Stylometrics Card
        cit_card = QFrame()
        cit_card.setObjectName("card")
        cb_layout = QVBoxLayout(cit_card)
        cb_layout.setSpacing(6)
        cb_title = QLabel("CITATIONS, REFERENCES & STYLOMETRIC HEURISTICS")
        cb_title.setStyleSheet("color: #002461; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        cb_layout.addWidget(cb_title)
        self.citations_text = QLabel("Auditing citation density...")
        self.citations_text.setStyleSheet("font-size: 12px; color: #334155; line-height: 1.4;")
        self.citations_text.setWordWrap(True)
        cb_layout.addWidget(self.citations_text)
        details_row.addWidget(cit_card, 1)

        layout.addLayout(details_row)

        # 5. Institutional Academic Disclaimer Banner
        disc_frame = QFrame()
        disc_frame.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 10px 14px;
            }
        """)
        disc_layout = QVBoxLayout(disc_frame)
        disc_layout.setSpacing(2)
        disc_title = QLabel("INSTITUTIONAL PLAGIARISM CLEARANCE DISCLAIMER")
        disc_title.setStyleSheet("font-size: 10px; font-weight: 800; color: #002461; letter-spacing: 0.5px;")
        disc_layout.addWidget(disc_title)
        disc_text = QLabel(
            f"<b>SES's R. C. Patel IMRD Shirpur Central Library:</b> {ACADEMIC_DISCLAIMER}"
        )
        disc_text.setStyleSheet("color: #64748B; font-size: 10.5px;")
        disc_text.setWordWrap(True)
        disc_layout.addWidget(disc_text)
        layout.addWidget(disc_frame)

        scroll.setWidget(container)
        self.stack.addWidget(scroll)

        outer_layout.addWidget(self.stack)
        self.stack.setCurrentIndex(0)

    def load_result(self, result_obj, doc_id: Optional[int] = None):
        """Populates the view with completed student verification results."""
        self._current_result = result_obj
        self._doc_id = doc_id
        self.stack.setCurrentIndex(1)

        # Update Student Header Bar
        student_name = getattr(result_obj, "student_name", "Student Name")
        prn = getattr(result_obj, "prn_number", "-")
        course = getattr(result_obj, "course_name", "MCA")
        sem = getattr(result_obj, "semester", "Semester IV")
        guide = getattr(result_obj, "guide_name", "Faculty Supervisor")
        title = getattr(result_obj, "paper_title", result_obj.document_filename)

        self.student_bar_lbl.setText(
            f"Student: <b>{student_name}</b> | PRN: <b>{prn}</b> | Program: <b>{course} ({sem})</b> | Guide: <b>{guide}</b>"
        )
        self.file_lbl.setText(
            f"Title: \"{title}\" • File: {result_obj.document_filename} • Words: {result_obj.word_count:,} • Pages: {result_obj.page_count}"
        )

        # Update Gauge & Badges
        sb = result_obj.score_breakdown
        self.gauge.set_value(sb.overall_similarity)
        self.risk_badge.set_level(sb.risk_level)

        # Update Metric cards
        self.card_exact.set_value(str(sb.exact_count), f"{sb.exact_percentage:.1f}% document overlap")
        self.card_fuzzy.set_value(str(sb.fuzzy_count), f"{sb.fuzzy_percentage:.1f}% document overlap")
        self.card_semantic.set_value(str(sb.semantic_count), f"{sb.semantic_percentage:.1f}% semantic index")
        self.card_quoted.set_value(str(sb.quoted_count), f"{sb.quoted_percentage:.1f}% cited/quoted")

        # Update UGC Compliance Card
        overall_sim = sb.overall_similarity
        if overall_sim <= 10.0:
            self.ugc_badge.setText("UGC LEVEL 0: CLEARED ✓")
            self.ugc_badge.setStyleSheet("background-color: #ECFDF5; color: #047857; border: 1.5px solid #10B981; border-radius: 6px; font-size: 12px; font-weight: 800; padding: 6px 12px;")
            self.ugc_desc.setText(
                f"Textual similarity index of <b>{overall_sim:.1f}%</b> is within permissible threshold (<= 10.0%) under UGC Regulations 2018. "
                "<b>Student is GRANTED PLAGIARISM CLEARANCE for final submission.</b>"
            )
        elif overall_sim <= 40.0:
            self.ugc_badge.setText("UGC LEVEL 1: REVISIONS REQUIRED ⚠")
            self.ugc_badge.setStyleSheet("background-color: #FFFBEB; color: #B45309; border: 1.5px solid #F59E0B; border-radius: 6px; font-size: 12px; font-weight: 800; padding: 6px 12px;")
            self.ugc_desc.setText(
                f"Similarity index of <b>{overall_sim:.1f}%</b> falls under UGC Level 1 (10.1% - 40.0%). "
                "Student must revise uncredited sections under supervisor guidance and resubmit for verification."
            )
        elif overall_sim <= 60.0:
            self.ugc_badge.setText("UGC LEVEL 2: MAJOR REVISIONS ⚠")
            self.ugc_badge.setStyleSheet("background-color: #FEF2F2; color: #B91C1C; border: 1.5px solid #EF4444; border-radius: 6px; font-size: 12px; font-weight: 800; padding: 6px 12px;")
            self.ugc_desc.setText(
                f"Similarity index of <b>{overall_sim:.1f}%</b> falls under UGC Level 2 (40.1% - 60.0%). "
                "Major revisions required. Student must revise dissertation and resubmit."
            )
        else:
            self.ugc_badge.setText("UGC LEVEL 3: REJECTED ❌")
            self.ugc_badge.setStyleSheet("background-color: #450A0A; color: #FFFFFF; border: 1.5px solid #991B1B; border-radius: 6px; font-size: 12px; font-weight: 800; padding: 6px 12px;")
            self.ugc_desc.setText(
                f"Similarity index of <b>{overall_sim:.1f}%</b> represents severe textual overlap exceeding 60.0%. "
                "Paper rejected under university academic integrity policy."
            )

        # Update Structure text
        struct_lines = []
        for name, boundary in result_obj.structure.items():
            det = boundary.detected if hasattr(boundary, "detected") else boundary.get("detected", False)
            mark = "✓" if det else "⚠"
            status = "Identified" if det else "Not detected"
            color = "#047857" if det else "#64748B"
            struct_lines.append(f"<font color='{color}'><b>{mark} {name}:</b> {status}</font>")
        self.structure_text.setText("<br/>".join(struct_lines))

        # Update Citations text — with correct pluralization
        cit = result_obj.citations
        ai = result_obj.ai_writing
        ai_lik = getattr(ai, "likelihood", "Low")
        ai_score = getattr(ai, "score", 0.0)

        def _pl(n: int, singular: str, plural: str = "") -> str:
            """Return correctly pluralized unit string."""
            if not plural:
                plural = singular + "s"
            return singular if n == 1 else plural

        quote_count = len(cit.quotes) if cit.quotes else 0
        uncited = cit.uncited_claims

        cit_html = (
            f"<b>In-Text Citations:</b> {cit.citation_count} "
            f"{_pl(cit.citation_count, 'citation')} parsed (IEEE, APA, Harvard)<br/>"
            f"<b>References Count:</b> {cit.reference_count} bibliographic "
            f"{_pl(cit.reference_count, 'entry', 'entries')}<br/>"
            f"<b>Quoted Passages:</b> {quote_count} "
            f"{_pl(quote_count, 'section')} isolated<br/>"
            f"<b>Potentially Uncited Sections:</b> {uncited} "
            f"{_pl(uncited, 'paragraph')}<br/><br/>"
            f"<b>AI Writing Likelihood:</b> "
            f"<font color='#005FEA'><b>{ai_lik} ({ai_score:.0f}%)</b></font><br/>"
            f"<font color='#64748B'><i>Note: This score is an indicative heuristic based on "
            f"stylometric variance analysis and does not constitute definitive proof "
            f"of AI-generated content.</i></font>"
        )
        self.citations_text.setText(cit_html)

    def _on_inspect_clicked(self):
        if self._current_result:
            self.open_match_viewer.emit({
                "document_filename": self._current_result.document_filename,
                "extracted_text": self._current_result.extracted_text,
                "matches": self._current_result.matches,
                "score_breakdown": self._current_result.score_breakdown,
            })

    def _export_pdf(self):
        if not self._current_result:
            QMessageBox.warning(self, "No Document Loaded", "Please verify a student document before generating certificate.")
            return

        student_name = getattr(self._current_result, "student_name", "Student").replace(" ", "_")
        prn = getattr(self._current_result, "prn_number", "PRN")
        default_name = f"IMRD_Clearance_Certificate_{student_name}_{prn}.pdf"
        default_path = str(REPORTS_DIR / default_name)

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Official IMRD Library Clearance Certificate",
            default_path,
            "PDF Documents (*.pdf)",
        )
        if save_path:
            try:
                gen = PDFReportGenerator(save_path)
                doc_data = {
                    "filename": self._current_result.document_filename,
                    "hash": self._current_result.file_hash,
                    "word_count": self._current_result.word_count,
                    "page_count": self._current_result.page_count,
                    "student_name": getattr(self._current_result, "student_name", "Student Name"),
                    "prn_number": getattr(self._current_result, "prn_number", "-"),
                    "course_name": getattr(self._current_result, "course_name", "MCA"),
                    "academic_year": getattr(self._current_result, "academic_year", "2025-2026"),
                    "semester": getattr(self._current_result, "semester", "Semester IV"),
                    "guide_name": getattr(self._current_result, "guide_name", "Supervisor"),
                    "paper_title": getattr(self._current_result, "paper_title", self._current_result.document_filename),
                    "certificate_no": getattr(self._current_result, "certificate_no", "IMRD/LIB/PLAG/2026/0001"),
                }
                sb = self._current_result.score_breakdown
                score_dict = {
                    "overall_similarity": sb.overall_similarity,
                    "risk_level": sb.risk_level,
                    "exact_percentage": sb.exact_percentage,
                    "exact_count": sb.exact_count,
                    "fuzzy_percentage": sb.fuzzy_percentage,
                    "fuzzy_count": sb.fuzzy_count,
                    "semantic_percentage": sb.semantic_percentage,
                    "semantic_count": sb.semantic_count,
                    "quoted_percentage": sb.quoted_percentage,
                    "quoted_count": sb.quoted_count,
                    "ignored_count": sb.ignored_count,
                }
                cit_dict = {
                    "citation_count": self._current_result.citations.citation_count,
                    "reference_count": self._current_result.citations.reference_count,
                    "quotes": self._current_result.citations.quotes,
                    "uncited_claims": self._current_result.citations.uncited_claims,
                }
                metadata = {
                    "student_name": doc_data["student_name"],
                    "prn_number": doc_data["prn_number"],
                    "course_name": doc_data["course_name"],
                    "academic_year": doc_data["academic_year"],
                    "semester": doc_data["semester"],
                    "guide_name": doc_data["guide_name"],
                    "paper_title": doc_data["paper_title"],
                    "certificate_no": doc_data["certificate_no"],
                    "ai_likelihood": getattr(self._current_result.ai_writing, "likelihood", "Low"),
                }
                gen.generate_report(
                    document_data=doc_data,
                    score_breakdown=score_dict,
                    matches=self._current_result.matches,
                    citation_data=cit_dict,
                    structure_data=self._current_result.structure,
                    metadata=metadata,
                )
                QMessageBox.information(
                    self,
                    "Certificate Generated",
                    f"Official IMRD Library Clearance Certificate successfully generated:\n\n{save_path}",
                )
            except Exception as e:
                logger.error(f"Certificate generation error: {e}")
                QMessageBox.critical(self, "Generation Error", f"Could not generate clearance certificate: {e}")

    def _export_html(self):
        if not self._current_result:
            QMessageBox.warning(
                self,
                "No Document Loaded",
                "Please verify a student document before generating an audit report.",
            )
            return

        filename_clean = Path(self._current_result.document_filename).stem
        default_path = str(REPORTS_DIR / f"IMRD_Plagiarism_Audit_{filename_clean}.html")

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Interactive HTML Audit Report",
            default_path,
            "HTML Files (*.html)",
        )
        if save_path:
            try:
                gen = HTMLReportGenerator(save_path)
                doc_data = {
                    "filename": self._current_result.document_filename,
                    "word_count": self._current_result.word_count,
                }
                sb = self._current_result.score_breakdown
                score_dict = {
                    "overall_similarity": sb.overall_similarity,
                    "risk_level": sb.risk_level,
                    "exact_count": sb.exact_count,
                    "fuzzy_count": sb.fuzzy_count,
                    "semantic_count": sb.semantic_count,
                    "quoted_count": sb.quoted_count,
                }
                gen.generate_report(
                    document_data=doc_data,
                    score_breakdown=score_dict,
                    matches=self._current_result.matches,
                    citation_data={},
                    structure_data=self._current_result.structure,
                )
                QMessageBox.information(self, "Audit Report Saved", f"HTML report saved to:\n{save_path}")
            except Exception as e:
                logger.error(f"HTML export failed: {e}")
                QMessageBox.critical(self, "Export Failed", f"Could not generate HTML report: {e}")
