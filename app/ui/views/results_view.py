"""Results summary view presenting similarity indicators, structure checks, and report export actions."""

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
    QVBoxLayout,
    QWidget,
)
from app.config import ACADEMIC_DISCLAIMER, REPORTS_DIR
from app.reports.export import export_analysis_to_json, export_matches_to_csv
from app.reports.html_generator import HTMLReportGenerator
from app.reports.pdf_generator import PDFReportGenerator
from app.ui.widgets.cards import MetricCard, RiskBadge
from app.ui.widgets.charts import SimilarityGaugeWidget
from app.utils.logger import logger


class ResultsView(QWidget):
    """Presents a comprehensive summary of analysis results with export capabilities."""

    open_match_viewer = Signal(dict)  # Passes result data to match viewer

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_result = None
        self._doc_id = None
        self._init_ui()

    def _init_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header Title
        h_layout = QHBoxLayout()
        v_title = QVBoxLayout()
        self.title_lbl = QLabel("Plagiarism & Textual Similarity Audit Summary")
        self.title_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #FFFFFF;")
        self.file_lbl = QLabel("Document: -")
        self.file_lbl.setStyleSheet("font-size: 13px; color: #94A3B8;")
        v_title.addWidget(self.title_lbl)
        v_title.addWidget(self.file_lbl)
        h_layout.addLayout(v_title)
        h_layout.addStretch()

        # Action Buttons
        self.inspect_btn = QPushButton("🔍 Inspect Matches Side-by-Side")
        self.inspect_btn.setObjectName("primaryBtn")
        self.inspect_btn.setMinimumHeight(38)
        self.inspect_btn.clicked.connect(self._on_inspect_clicked)
        h_layout.addWidget(self.inspect_btn)

        self.export_pdf_btn = QPushButton("📄 Export PDF Report")
        self.export_pdf_btn.setMinimumHeight(38)
        self.export_pdf_btn.clicked.connect(self._export_pdf)
        h_layout.addWidget(self.export_pdf_btn)

        self.export_html_btn = QPushButton("🌐 HTML Report")
        self.export_html_btn.setMinimumHeight(38)
        self.export_html_btn.clicked.connect(self._export_html)
        h_layout.addWidget(self.export_html_btn)

        layout.addLayout(h_layout)

        # Academic Disclaimer Alert
        disc_frame = QFrame()
        disc_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(245, 158, 11, 0.1);
                border: 1px solid #F59E0B;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        disc_layout = QHBoxLayout(disc_frame)
        disc_icon = QLabel("⚠️")
        disc_icon.setStyleSheet("font-size: 16px; background: transparent; border: none;")
        disc_layout.addWidget(disc_icon)
        disc_text = QLabel(f"<b>ACADEMIC REVIEW NOTICE:</b> {ACADEMIC_DISCLAIMER}")
        disc_text.setStyleSheet("color: #FDE68A; font-size: 12px; background: transparent; border: none;")
        disc_text.setWordWrap(True)
        disc_layout.addWidget(disc_text, 1)
        layout.addWidget(disc_frame)

        # Top Section: Gauge & Risk Breakdown
        top_grid = QHBoxLayout()
        top_grid.setSpacing(16)

        # Gauge Card
        gauge_card = QFrame()
        gauge_card.setObjectName("card")
        g_box = QVBoxLayout(gauge_card)
        g_box.setAlignment(Qt.AlignCenter)
        g_box.addWidget(QLabel("OVERALL SIMILARITY SCORE"), alignment=Qt.AlignCenter)
        self.gauge = SimilarityGaugeWidget()
        g_box.addWidget(self.gauge, alignment=Qt.AlignCenter)
        self.risk_badge = RiskBadge("Very Low")
        self.risk_badge.setFixedWidth(140)
        g_box.addWidget(self.risk_badge, alignment=Qt.AlignCenter)
        top_grid.addWidget(gauge_card, 1)

        # Metric Breakdown Cards
        metrics_col = QVBoxLayout()
        metrics_col.setSpacing(10)

        row1 = QHBoxLayout()
        self.card_exact = MetricCard("Exact Matches", "0", "0.0% overlap", "#EF4444")
        self.card_fuzzy = MetricCard("Fuzzy Matches", "0", "0.0% overlap", "#F59E0B")
        row1.addWidget(self.card_exact)
        row1.addWidget(self.card_fuzzy)
        metrics_col.addLayout(row1)

        row2 = QHBoxLayout()
        self.card_semantic = MetricCard("Semantic Paraphrases", "0", "0.0% similarity", "#8B5CF6")
        self.card_quoted = MetricCard("Quoted / Cited Content", "0", "Excluded from uncredited", "#0284C7")
        row2.addWidget(self.card_semantic)
        row2.addWidget(self.card_quoted)
        metrics_col.addLayout(row2)

        top_grid.addLayout(metrics_col, 2)
        layout.addLayout(top_grid)

        # Academic Paper Structure & Citations Analysis Grid
        sub_grid = QHBoxLayout()
        sub_grid.setSpacing(16)

        # Structure Card
        struct_card = QFrame()
        struct_card.setObjectName("card")
        s_box = QVBoxLayout(struct_card)
        s_box.addWidget(QLabel("RESEARCH PAPER STRUCTURE VERIFICATION"))
        self.structure_text = QLabel("Section analysis loading...")
        self.structure_text.setStyleSheet("color: #CBD5E1; font-size: 12px; line-height: 1.5;")
        self.structure_text.setWordWrap(True)
        s_box.addWidget(self.structure_text)
        sub_grid.addWidget(struct_card, 1)

        # Citations & AI Card
        cit_card = QFrame()
        cit_card.setObjectName("card")
        c_box = QVBoxLayout(cit_card)
        c_box.addWidget(QLabel("CITATIONS & AI-WRITING INDICATORS"))
        self.citations_text = QLabel("Citation metrics loading...")
        self.citations_text.setStyleSheet("color: #CBD5E1; font-size: 12px; line-height: 1.5;")
        self.citations_text.setWordWrap(True)
        c_box.addWidget(self.citations_text)
        sub_grid.addWidget(cit_card, 1)

        layout.addLayout(sub_grid)

        scroll.setWidget(container)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

    def load_result(self, result_obj, doc_id: Optional[int] = None):
        """Populates the view with completed detection results."""
        self._current_result = result_obj
        self._doc_id = doc_id

        # Update header
        self.file_lbl.setText(f"Document: {result_obj.document_filename} • Words: {result_obj.word_count:,} • Pages: {result_obj.page_count}")

        # Update Gauge & Badges
        sb = result_obj.score_breakdown
        self.gauge.set_value(sb.overall_similarity)
        self.risk_badge.set_level(sb.risk_level)

        # Update Metric cards
        self.card_exact.set_value(str(sb.exact_count), f"{sb.exact_percentage:.1f}% document overlap")
        self.card_fuzzy.set_value(str(sb.fuzzy_count), f"{sb.fuzzy_percentage:.1f}% document overlap")
        self.card_semantic.set_value(str(sb.semantic_count), f"{sb.semantic_percentage:.1f}% semantic index")
        self.card_quoted.set_value(str(sb.quoted_count), f"{sb.quoted_percentage:.1f}% cited/quoted")

        # Update Structure text
        struct_lines = []
        for name, boundary in result_obj.structure.items():
            det = boundary.detected if hasattr(boundary, "detected") else boundary.get("detected", False)
            mark = "✓" if det else "⚠"
            status = "Detected" if det else "Not clearly detected"
            color = "#10B981" if det else "#94A3B8"
            struct_lines.append(f"<font color='{color}'><b>{mark} {name}:</b> {status}</font>")
        self.structure_text.setText("<br/>".join(struct_lines))

        # Update Citations text
        cit = result_obj.citations
        ai = result_obj.ai_writing
        ai_lik = getattr(ai, "likelihood", "Low")
        ai_score = getattr(ai, "score", 0.0)

        cit_html = f"""
            <b>In-Text Citations:</b> {cit.citation_count} parsed (IEEE, APA, Harvard)<br/>
            <b>References Count:</b> {cit.reference_count} entries estimated<br/>
            <b>Quoted Passages:</b> {len(cit.quotes)} sections isolated<br/>
            <b>Uncited Paragraphs:</b> {cit.uncited_claims} potential narrative sections<br/><br/>
            <b>AI-Writing Likelihood:</b> <font color='#818CF8'><b>{ai_lik} ({ai_score:.0f}%)</b></font><br/>
            <font size='1' color='#94A3B8'>*Stylometric indicator based on sentence length variance & burstiness.</font>
        """
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
            return

        filename_clean = Path(self._current_result.document_filename).stem
        default_name = f"ResearchGuard_Report_{filename_clean}.pdf"
        default_path = str(REPORTS_DIR / default_name)

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save PDF Plagiarism Report",
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
                gen.generate_report(
                    document_data=doc_data,
                    score_breakdown=score_dict,
                    matches=self._current_result.matches,
                    citation_data=cit_dict,
                    structure_data=self._current_result.structure,
                )
                QMessageBox.information(self, "Report Generated", f"PDF report successfully saved to:\n{save_path}")
            except Exception as e:
                logger.error(f"PDF export failed: {e}")
                QMessageBox.critical(self, "Export Failed", f"Could not generate PDF report: {e}")

    def _export_html(self):
        if not self._current_result:
            return

        filename_clean = Path(self._current_result.document_filename).stem
        default_path = str(REPORTS_DIR / f"ResearchGuard_Report_{filename_clean}.html")

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Interactive HTML Report",
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
                QMessageBox.information(self, "Report Generated", f"Interactive HTML report saved to:\n{save_path}")
            except Exception as e:
                logger.error(f"HTML export failed: {e}")
                QMessageBox.critical(self, "Export Failed", f"Could not generate HTML report: {e}")
