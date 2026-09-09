"""Plagiarism and research paper verification results view.
Presents UGC compliance status, multidimensional scores, interactive document heatmap,
reference verification table, in-text citation audits, and researcher human review workspace.
"""

from pathlib import Path
from typing import Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
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
    """Presents research verification results across Overview, Similarity, Sections, References, Citations, Sources, and Review tabs."""

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
            message="No research paper verification has been conducted in this session. Select an archived paper from 'Student Records Archive' or verify a new draft in 'Verify Student Paper'.",
            parent=empty_container,
        )
        empty_layout.addWidget(self.empty_state)
        self.stack.addWidget(empty_container)

        # Page 1: Results Workspace
        results_container = QWidget()
        results_layout = QVBoxLayout(results_container)
        results_layout.setContentsMargins(20, 16, 20, 16)
        results_layout.setSpacing(12)

        # 1. Top Header Bar
        h_layout = QHBoxLayout()
        v_title = QVBoxLayout()
        v_title.setSpacing(2)

        self.title_lbl = QLabel("Research Paper Verification & Academic Clearance")
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #002461;")
        self.title_lbl.setWordWrap(True)
        
        self.student_bar_lbl = QLabel("Author: - • Identifier: - • Department: -")
        self.student_bar_lbl.setStyleSheet("font-size: 11.5px; font-weight: 600; color: #005FEA;")
        
        self.file_lbl = QLabel("Document: - • Words: 0 • Pages: 0")
        self.file_lbl.setStyleSheet("font-size: 11px; color: #64748B;")

        v_title.addWidget(self.title_lbl)
        v_title.addWidget(self.student_bar_lbl)
        v_title.addWidget(self.file_lbl)
        h_layout.addLayout(v_title, 1)

        # Action Buttons
        btn_bar = QHBoxLayout()
        btn_bar.setSpacing(8)

        self.inspect_btn = QPushButton("Inspect Matches")
        self.inspect_btn.setObjectName("primaryBtn")
        self.inspect_btn.setFixedHeight(34)
        self.inspect_btn.setMinimumWidth(125)
        self.inspect_btn.setCursor(Qt.PointingHandCursor)
        self.inspect_btn.clicked.connect(self._on_inspect_clicked)
        btn_bar.addWidget(self.inspect_btn)

        self.export_cert_btn = QPushButton("Clearance Certificate (PDF)")
        self.export_cert_btn.setObjectName("certBtn")
        self.export_cert_btn.setFixedHeight(34)
        self.export_cert_btn.setMinimumWidth(165)
        self.export_cert_btn.setCursor(Qt.PointingHandCursor)
        self.export_cert_btn.clicked.connect(self._export_pdf)
        btn_bar.addWidget(self.export_cert_btn)

        self.export_html_btn = QPushButton("HTML Audit Report")
        self.export_html_btn.setFixedHeight(34)
        self.export_html_btn.setMinimumWidth(125)
        self.export_html_btn.setCursor(Qt.PointingHandCursor)
        self.export_html_btn.clicked.connect(self._export_html)
        btn_bar.addWidget(self.export_html_btn)

        h_layout.addLayout(btn_bar, 0)
        results_layout.addLayout(h_layout)

        # 2. Main Tab Widget for Verification Modules
        self.tabs = QTabWidget()
        self.tabs.setObjectName("resultsTabs")

        # Tab 1: Overview
        self.tab_overview = self._build_overview_tab()
        self.tabs.addTab(self.tab_overview, "📊 Overview")

        # Tab 2: Similarity & Heatmap
        self.tab_similarity = self._build_similarity_tab()
        self.tabs.addTab(self.tab_similarity, "🔥 Similarity & Heatmap")

        # Tab 3: Section Breakdown
        self.tab_sections = self._build_sections_tab()
        self.tabs.addTab(self.tab_sections, "📑 Sections")

        # Tab 4: Reference Verification
        self.tab_references = self._build_references_tab()
        self.tabs.addTab(self.tab_references, "📚 References")

        # Tab 5: Citation Audit
        self.tab_citations = self._build_citations_tab()
        self.tabs.addTab(self.tab_citations, "🔍 Citations")

        # Tab 6: Discovered Sources
        self.tab_sources = self._build_sources_tab()
        self.tabs.addTab(self.tab_sources, "🌐 Sources")

        # Tab 7: Human Review
        self.tab_review = self._build_review_tab()
        self.tabs.addTab(self.tab_review, "✍️ Human Review")

        results_layout.addWidget(self.tabs, 1)
        self.stack.addWidget(results_container)
        outer_layout.addWidget(self.stack)

    # ----------------------------------------------------------------------
    # TAB BUILDERS
    # ----------------------------------------------------------------------

    def _build_overview_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        # Academic Verdict Banner
        self.verdict_frame = QFrame()
        self.verdict_frame.setObjectName("card")
        vf_layout = QHBoxLayout(self.verdict_frame)
        vf_layout.setContentsMargins(14, 10, 14, 10)

        self.verdict_badge = QLabel("LOW CONCERN")
        self.verdict_badge.setStyleSheet("""
            background-color: #ECFDF5; color: #047857; border: 1.5px solid #10B981;
            border-radius: 6px; font-size: 13px; font-weight: 800; padding: 6px 14px;
        """)
        vf_layout.addWidget(self.verdict_badge)

        self.verdict_desc = QLabel("No significant unattributed similarity detected. Document appears suitable for submission.")
        self.verdict_desc.setStyleSheet("color: #0F172A; font-size: 12px; font-weight: 500;")
        self.verdict_desc.setWordWrap(True)
        vf_layout.addWidget(self.verdict_desc, 1)

        layout.addWidget(self.verdict_frame)

        # UGC 2018 Regulation Status Card
        self.ugc_frame = QFrame()
        self.ugc_frame.setObjectName("card")
        self.ugc_layout = QHBoxLayout(self.ugc_frame)
        self.ugc_layout.setContentsMargins(14, 8, 14, 8)

        self.ugc_badge = QLabel("UGC LEVEL 0: CLEARED")
        self.ugc_badge.setStyleSheet("background-color: #F0FDF4; color: #15803D; font-weight: 700; font-size: 11.5px; padding: 4px 10px; border-radius: 4px;")
        self.ugc_layout.addWidget(self.ugc_badge)

        self.ugc_desc = QLabel("Similarity index is within the permissible 10.0% institutional threshold.")
        self.ugc_desc.setStyleSheet("color: #475569; font-size: 11px;")
        self.ugc_layout.addWidget(self.ugc_desc, 1)
        layout.addWidget(self.ugc_frame)

        # Top Grid: Gauge & Multidimensional Scorecards
        top_grid = QHBoxLayout()
        top_grid.setSpacing(12)

        gauge_card = QFrame()
        gauge_card.setObjectName("card")
        g_box = QVBoxLayout(gauge_card)
        g_box.setAlignment(Qt.AlignCenter)
        
        g_lbl = QLabel("OVERALL SIMILARITY")
        g_lbl.setStyleSheet("color: #002461; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        g_box.addWidget(g_lbl, alignment=Qt.AlignCenter)
        
        self.gauge = SimilarityGaugeWidget()
        g_box.addWidget(self.gauge, alignment=Qt.AlignCenter)
        
        self.risk_badge = RiskBadge("Very Low")
        self.risk_badge.setFixedWidth(130)
        g_box.addWidget(self.risk_badge, alignment=Qt.AlignCenter)
        top_grid.addWidget(gauge_card, 1)

        # 6 KPI Metric Cards
        metrics_col = QVBoxLayout()
        metrics_col.setSpacing(8)

        self.card_direct = MetricCard("Direct Text Match", "0.0%", "Verbatim identical phrasing", "#EF4444")
        self.card_semantic = MetricCard("Semantic Similarity", "0.0%", "Conceptual / paraphrase overlap", "#8B5CF6")
        self.card_citation_cov = MetricCard("Citation Coverage", "100%", "In-text citations integrity", "#10B981")
        self.card_ref_verif = MetricCard("Reference Verification", "100%", "Discovered in Crossref/OpenAlex", "#0284C7")
        self.card_high_risk = MetricCard("High-Risk Matches", "0.0%", "Unattributed external overlaps", "#DC2626")
        self.card_quoted = MetricCard("Quoted / Cited", "0", "Legitimate academic quotes", "#059669")

        row1 = QHBoxLayout()
        row1.addWidget(self.card_direct)
        row1.addWidget(self.card_semantic)
        row1.addWidget(self.card_high_risk)
        metrics_col.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(self.card_citation_cov)
        row2.addWidget(self.card_ref_verif)
        row2.addWidget(self.card_quoted)
        metrics_col.addLayout(row2)

        top_grid.addLayout(metrics_col, 2)
        layout.addLayout(top_grid)

        # Bottom Split: Structure Parser vs Citations & AI Heuristics
        details_row = QHBoxLayout()
        details_row.setSpacing(12)

        struct_card = QFrame()
        struct_card.setObjectName("card")
        sb_layout = QVBoxLayout(struct_card)
        sb_title = QLabel("PAPER STRUCTURE RECOGNITION")
        sb_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #002461;")
        sb_layout.addWidget(sb_title)
        self.structure_text = QLabel("Analyzing...")
        self.structure_text.setTextFormat(Qt.RichText)
        self.structure_text.setStyleSheet("font-size: 11.5px; line-height: 1.4;")
        sb_layout.addWidget(self.structure_text)
        details_row.addWidget(struct_card, 1)

        heuristics_card = QFrame()
        heuristics_card.setObjectName("card")
        hb_layout = QVBoxLayout(heuristics_card)
        hb_title = QLabel("CITATIONS & STYLOMETRIC HEURISTICS")
        hb_title.setStyleSheet("font-size: 11px; font-weight: 800; color: #002461;")
        hb_layout.addWidget(hb_title)
        self.citations_text = QLabel("Analyzing...")
        self.citations_text.setTextFormat(Qt.RichText)
        self.citations_text.setStyleSheet("font-size: 11.5px; line-height: 1.4;")
        hb_layout.addWidget(self.citations_text)
        details_row.addWidget(heuristics_card, 1)

        layout.addLayout(details_row)
        return container

    def _build_similarity_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Document Heatmap Bar
        hm_hdr = QHBoxLayout()
        hm_lbl = QLabel("DOCUMENT SIMILARITY HEATMAP")
        hm_lbl.setStyleSheet("font-size: 11.5px; font-weight: 800; color: #002461;")
        hm_hdr.addWidget(hm_lbl)
        hm_hdr.addStretch()
        legend = QLabel("Legend: 🟩 Original  🟨 Fuzzy/Paraphrased  🟥 Exact Match  🟦 Quoted")
        legend.setStyleSheet("font-size: 11px; color: #475569;")
        hm_hdr.addWidget(legend)
        layout.addLayout(hm_hdr)

        self.heatmap_bar = QProgressBar()
        self.heatmap_bar.setTextVisible(False)
        self.heatmap_bar.setFixedHeight(18)
        self.heatmap_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #CBD5E1; border-radius: 4px; background-color: #ECFDF5; }
            QProgressBar::chunk { background-color: #EF4444; }
        """)
        layout.addWidget(self.heatmap_bar)

        # Flagged Matches Table
        table_lbl = QLabel("FLAGGED SIMILARITY PASSAGES")
        table_lbl.setStyleSheet("font-size: 11.5px; font-weight: 800; color: #002461; margin-top: 8px;")
        layout.addWidget(table_lbl)

        self.matches_table = QTableWidget()
        self.matches_table.setColumnCount(6)
        self.matches_table.setHorizontalHeaderLabels([
            "Page", "Similarity", "Classification", "Confidence", "Matched Passage", "Source"
        ])
        self.matches_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.matches_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.matches_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.matches_table.doubleClicked.connect(lambda: self._on_inspect_clicked())
        layout.addWidget(self.matches_table)

        return container

    def _build_sections_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        hdr = QLabel("SECTION-BY-SECTION SIMILARITY BREAKDOWN")
        hdr.setStyleSheet("font-size: 12px; font-weight: 800; color: #002461;")
        layout.addWidget(hdr)

        self.sections_grid = QGridLayout()
        self.sections_grid.setSpacing(10)
        self._section_bars = {}

        standard_sections = [
            "Title", "Abstract", "Introduction", "Literature Review",
            "Methodology", "Results", "Discussion", "Conclusion"
        ]

        for idx, s_name in enumerate(standard_sections):
            row = idx // 2
            col = (idx % 2) * 2

            s_lbl = QLabel(s_name)
            s_lbl.setStyleSheet("font-weight: 700; color: #1E293B; font-size: 11.5px;")
            self.sections_grid.addWidget(s_lbl, row, col)

            pbar = QProgressBar()
            pbar.setFixedHeight(18)
            pbar.setRange(0, 100)
            pbar.setValue(0)
            pbar.setFormat("%v%")
            pbar.setStyleSheet("""
                QProgressBar { border: 1px solid #CBD5E1; border-radius: 4px; text-align: center; font-size: 10.5px; }
                QProgressBar::chunk { background-color: #005FEA; border-radius: 3px; }
            """)
            self.sections_grid.addWidget(pbar, row, col + 1)
            self._section_bars[s_name] = pbar

        layout.addLayout(self.sections_grid)
        layout.addStretch()
        return container

    def _build_references_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        hdr_row = QHBoxLayout()
        hdr = QLabel("ACADEMIC REFERENCE & BIBLIOGRAPHY VERIFICATION")
        hdr.setStyleSheet("font-size: 12px; font-weight: 800; color: #002461;")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        self.ref_status_summary = QLabel("Total: 0 • Verified: 0 • Suspicious: 0")
        self.ref_status_summary.setStyleSheet("font-size: 11px; font-weight: 600; color: #475569;")
        hdr_row.addWidget(self.ref_status_summary)
        layout.addLayout(hdr_row)

        self.refs_table = QTableWidget()
        self.refs_table.setColumnCount(7)
        self.refs_table.setHorizontalHeaderLabels([
            "#", "Title", "Authors", "Year", "DOI / Link", "Verification Status", "Registry Notes"
        ])
        self.refs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.refs_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.refs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.refs_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.refs_table)

        return container

    def _build_citations_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        hdr_row = QHBoxLayout()
        hdr = QLabel("IN-TEXT CITATION & REFERENCE INTEGRITY AUDIT")
        hdr.setStyleSheet("font-size: 12px; font-weight: 800; color: #002461;")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        self.cit_issues_summary = QLabel("0 Anomalies Detected")
        self.cit_issues_summary.setStyleSheet("font-size: 11px; font-weight: 700; color: #047857;")
        hdr_row.addWidget(self.cit_issues_summary)
        layout.addLayout(hdr_row)

        self.citations_table = QTableWidget()
        self.citations_table.setColumnCount(4)
        self.citations_table.setHorizontalHeaderLabels([
            "Issue Category", "In-Text Citation", "Page", "Forensic Audit Details"
        ])
        self.citations_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.citations_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.citations_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.citations_table)

        return container

    def _build_sources_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        hdr = QLabel("DISCOVERED SCHOLARLY & REPOSITORY SOURCES")
        hdr.setStyleSheet("font-size: 12px; font-weight: 800; color: #002461;")
        layout.addWidget(hdr)

        self.sources_table = QTableWidget()
        self.sources_table.setColumnCount(6)
        self.sources_table.setHorizontalHeaderLabels([
            "Source Publication Title", "Domain", "Type", "Reliability", "Primary / Secondary", "Identifier"
        ])
        self.sources_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.sources_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.sources_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.sources_table)

        return container

    def _build_review_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        hdr_row = QHBoxLayout()
        hdr = QLabel("RESEARCHER HUMAN REVIEW & VERIFICATION DECISIONS")
        hdr.setStyleSheet("font-size: 12px; font-weight: 800; color: #002461;")
        hdr_row.addWidget(hdr)
        hdr_row.addStretch()
        note = QLabel("Double-click any passage to inspect side-by-side or record review notes.")
        note.setStyleSheet("font-size: 11px; color: #64748B; font-style: italic;")
        hdr_row.addWidget(note)
        layout.addLayout(hdr_row)

        self.review_table = QTableWidget()
        self.review_table.setColumnCount(5)
        self.review_table.setHorizontalHeaderLabels([
            "Passage", "Similarity", "Review Status", "Review Notes", "Action"
        ])
        self.review_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.review_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.review_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.review_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.review_table)

        return container

    # ----------------------------------------------------------------------
    # POPULATION & RESULTS LOADING
    # ----------------------------------------------------------------------

    def load_result(self, result_obj, doc_id: Optional[int] = None):
        """Populates all tabs from the completed DetectionResult object."""
        self._current_result = result_obj
        self._doc_id = doc_id
        self.stack.setCurrentIndex(1)

        # 1. Update Header Information
        s_name = getattr(result_obj, "student_name", "Student Name")
        prn = getattr(result_obj, "prn_number", "-")
        course = getattr(result_obj, "course_name", "MCA")
        year = getattr(result_obj, "academic_year", "2025-2026")
        sem = getattr(result_obj, "semester", "Semester IV")
        guide = getattr(result_obj, "guide_name", "Supervisor")

        self.title_lbl.setText(f"Verification: {getattr(result_obj, 'paper_title', result_obj.document_filename)}")
        self.student_bar_lbl.setText(f"Author: {s_name} (PRN: {prn}) • {course} • {year} ({sem}) • Supervisor: {guide}")
        self.file_lbl.setText(f"File: {result_obj.document_filename} • Words: {result_obj.word_count:,} • Pages: {result_obj.page_count}")

        # 2. Update Overview Scores & Badges
        sb = result_obj.score_breakdown
        overall_sim = sb.overall_similarity
        self.gauge.set_score(overall_sim)
        self.risk_badge.set_level(sb.risk_level)

        self.card_direct.set_value(f"{sb.direct_match_score:.1f}%")
        self.card_semantic.set_value(f"{sb.semantic_similarity_score:.1f}%")
        self.card_citation_cov.set_value(f"{sb.citation_coverage_score:.0f}%")
        self.card_ref_verif.set_value(f"{sb.reference_verification_score:.0f}%")
        self.card_high_risk.set_value(f"{sb.high_risk_similarity:.1f}%")
        self.card_quoted.set_value(str(sb.quoted_count))

        # Academic Verdict
        verdict = sb.academic_verdict
        self.verdict_badge.setText(verdict)
        self.verdict_desc.setText(sb.verdict_summary or "Evaluation completed.")

        if verdict == "LOW CONCERN":
            self.verdict_badge.setStyleSheet("background-color: #ECFDF5; color: #047857; border: 1.5px solid #10B981; border-radius: 6px; font-weight: 800; font-size: 13px; padding: 6px 14px;")
        elif verdict == "MODERATE CONCERN":
            self.verdict_badge.setStyleSheet("background-color: #FFFBEB; color: #B45309; border: 1.5px solid #F59E0B; border-radius: 6px; font-weight: 800; font-size: 13px; padding: 6px 14px;")
        elif verdict == "HIGH CONCERN":
            self.verdict_badge.setStyleSheet("background-color: #FEF2F2; color: #B91C1C; border: 1.5px solid #EF4444; border-radius: 6px; font-weight: 800; font-size: 13px; padding: 6px 14px;")
        else:
            self.verdict_badge.setStyleSheet("background-color: #F1F5F9; color: #475569; border: 1.5px solid #94A3B8; border-radius: 6px; font-weight: 800; font-size: 13px; padding: 6px 14px;")

        # UGC Regulation Tiers
        if overall_sim <= 10.0:
            self.ugc_badge.setText("UGC LEVEL 0: CLEARED")
            self.ugc_badge.setStyleSheet("background-color: #F0FDF4; color: #15803D; font-weight: 700; font-size: 11.5px; padding: 4px 10px; border-radius: 4px;")
            self.ugc_desc.setText(f"Similarity index of <b>{overall_sim:.1f}%</b> is within the permissible 10.0% threshold under UGC Regulations 2018.")
        elif overall_sim <= 40.0:
            self.ugc_badge.setText("UGC LEVEL 1: REVISIONS REQUIRED ⚠")
            self.ugc_badge.setStyleSheet("background-color: #FFFBEB; color: #B45309; font-weight: 700; font-size: 11.5px; padding: 4px 10px; border-radius: 4px;")
            self.ugc_desc.setText(f"Similarity index of <b>{overall_sim:.1f}%</b> falls under UGC Level 1 (10.1% - 40.0%). Script must be revised under supervisor guidance.")
        elif overall_sim <= 60.0:
            self.ugc_badge.setText("UGC LEVEL 2: MAJOR REVISIONS ⚠")
            self.ugc_badge.setStyleSheet("background-color: #FEF2F2; color: #B91C1C; font-weight: 700; font-size: 11.5px; padding: 4px 10px; border-radius: 4px;")
            self.ugc_desc.setText(f"Similarity index of <b>{overall_sim:.1f}%</b> falls under UGC Level 2 (40.1% - 60.0%). Debarred for 1 year.")
        else:
            self.ugc_badge.setText("UGC LEVEL 3: REJECTED ❌")
            self.ugc_badge.setStyleSheet("background-color: #450A0A; color: #FFFFFF; font-weight: 700; font-size: 11.5px; padding: 4px 10px; border-radius: 4px;")
            self.ugc_desc.setText(f"Similarity index of <b>{overall_sim:.1f}%</b> exceeds 60.0%. Registration cancellation recommended.")

        # Structure Parser Text
        struct_lines = []
        for name, boundary in result_obj.structure.items():
            det = boundary.detected if hasattr(boundary, "detected") else boundary.get("detected", False)
            mark = "✓" if det else "⚠"
            status = "Identified" if det else "Not detected"
            color = "#047857" if det else "#64748B"
            struct_lines.append(f"<font color='{color}'><b>{mark} {name}:</b> {status}</font>")
        self.structure_text.setText("<br/>".join(struct_lines))

        # Citations and AI
        cit = result_obj.citations
        ai = result_obj.ai_writing
        ai_lik = getattr(ai, "likelihood", "Low")
        ai_score = getattr(ai, "score", 0.0)
        quote_count = len(cit.quotes) if cit.quotes else 0
        uncited = cit.uncited_claims

        cit_html = (
            f"<b>In-Text Citations:</b> {cit.citation_count} parsed (IEEE, APA, Harvard)<br/>"
            f"<b>References Count:</b> {cit.reference_count} bibliographic entries<br/>"
            f"<b>Quoted Passages:</b> {quote_count} sections isolated<br/>"
            f"<b>Uncited Sections:</b> {uncited} paragraphs<br/><br/>"
            f"<b>AI Writing Likelihood:</b> <font color='#005FEA'><b>{ai_lik} ({ai_score:.0f}%)</b></font><br/>"
            f"<font color='#64748B'><i>Note: Indicative stylometric variance heuristic only.</i></font>"
        )
        self.citations_text.setText(cit_html)

        # 3. Update Similarity Tab Table
        matches = result_obj.matches
        self.heatmap_bar.setValue(int(overall_sim))
        self.matches_table.setRowCount(len(matches))
        for row, m in enumerate(matches):
            self.matches_table.setItem(row, 0, QTableWidgetItem(f"p. {m.get('page_number', 1)}"))
            self.matches_table.setItem(row, 1, QTableWidgetItem(f"{m.get('similarity_score', 0):.0f}%"))
            self.matches_table.setItem(row, 2, QTableWidgetItem(m.get("match_category", "Copied")))
            self.matches_table.setItem(row, 3, QTableWidgetItem(m.get("confidence", "High")))
            self.matches_table.setItem(row, 4, QTableWidgetItem(m.get("sentence", "")[:80] + "..."))
            self.matches_table.setItem(row, 5, QTableWidgetItem(m.get("source_name", "Source")))

        # 4. Update Sections Tab
        sec_scores = sb.section_scores
        for s_name, pbar in self._section_bars.items():
            val = int(sec_scores.get(s_name, 0.0))
            pbar.setValue(val)

        # 5. Update References Tab
        refs: List = getattr(result_obj, "references", [])
        self.refs_table.setRowCount(len(refs))
        verified_count = 0
        suspicious_count = 0

        for row, r in enumerate(refs):
            st = getattr(r, "status", "NOT VERIFIED")
            if st in ["VERIFIED", "PARTIALLY VERIFIED"]:
                verified_count += 1
            if st == "SUSPICIOUS":
                suspicious_count += 1

            self.refs_table.setItem(row, 0, QTableWidgetItem(str(getattr(r, "ref_number", row + 1))))
            self.refs_table.setItem(row, 1, QTableWidgetItem(getattr(r, "title", "")[:60]))
            self.refs_table.setItem(row, 2, QTableWidgetItem(getattr(r, "authors", "")[:35]))
            self.refs_table.setItem(row, 3, QTableWidgetItem(str(getattr(r, "year", "-"))))
            doi_or_url = getattr(r, "doi", "") or getattr(r, "url", "") or "-"
            self.refs_table.setItem(row, 4, QTableWidgetItem(doi_or_url))
            self.refs_table.setItem(row, 5, QTableWidgetItem(st))
            self.refs_table.setItem(row, 6, QTableWidgetItem(getattr(r, "difference_notes", "") or getattr(r, "verification_source", "")))

        self.ref_status_summary.setText(f"Total: {len(refs)} • Verified: {verified_count} • Suspicious: {suspicious_count}")

        # 6. Update Citations Tab
        c_issues = getattr(cit, "citation_issues", [])
        self.citations_table.setRowCount(len(c_issues))
        for row, ci in enumerate(c_issues):
            self.citations_table.setItem(row, 0, QTableWidgetItem(getattr(ci, "issue_type", "Anomaly")))
            self.citations_table.setItem(row, 1, QTableWidgetItem(getattr(ci, "citation_text", "-")))
            self.citations_table.setItem(row, 2, QTableWidgetItem(f"p. {getattr(ci, 'page_number', 1)}"))
            self.citations_table.setItem(row, 3, QTableWidgetItem(getattr(ci, "details", "")))

        if c_issues:
            self.cit_issues_summary.setText(f"{len(c_issues)} Citation Issues Detected")
            self.cit_issues_summary.setStyleSheet("font-size: 11px; font-weight: 700; color: #DC2626;")
        else:
            self.cit_issues_summary.setText("0 Citation Anomalies Detected (Clean)")
            self.cit_issues_summary.setStyleSheet("font-size: 11px; font-weight: 700; color: #047857;")

        # 7. Update Sources Tab
        seen_sources = {}
        for m in matches:
            s_name = m.get("source_name", "Comparison Source")
            if s_name not in seen_sources:
                seen_sources[s_name] = m

        self.sources_table.setRowCount(len(seen_sources))
        for row, (s_name, s_m) in enumerate(seen_sources.items()):
            self.sources_table.setItem(row, 0, QTableWidgetItem(s_name))
            self.sources_table.setItem(row, 1, QTableWidgetItem(s_m.get("source_domain", "Library")))
            self.sources_table.setItem(row, 2, QTableWidgetItem(s_m.get("source_type", "Journal")))
            self.sources_table.setItem(row, 3, QTableWidgetItem(s_m.get("source_reliability", "High")))
            self.sources_table.setItem(row, 4, QTableWidgetItem("Primary Source"))
            self.sources_table.setItem(row, 5, QTableWidgetItem(s_m.get("source_url") or "-"))

        # 8. Update Review Tab
        self.review_table.setRowCount(len(matches))
        for row, m in enumerate(matches):
            self.review_table.setItem(row, 0, QTableWidgetItem(m.get("sentence", "")[:70] + "..."))
            self.review_table.setItem(row, 1, QTableWidgetItem(f"{m.get('similarity_score', 0):.0f}%"))
            self.review_table.setItem(row, 2, QTableWidgetItem(m.get("review_decision", "Pending Review")))
            self.review_table.setItem(row, 3, QTableWidgetItem(m.get("review_notes", "") or "-"))

            inspect_cell_btn = QPushButton("Review Match")
            inspect_cell_btn.setFixedHeight(24)
            inspect_cell_btn.clicked.connect(self._on_inspect_clicked)
            self.review_table.setCellWidget(row, 4, inspect_cell_btn)

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
            QMessageBox.warning(self, "No Document Loaded", "Please verify a research document before generating certificate.")
            return

        student_name = getattr(self._current_result, "student_name", "Author").replace(" ", "_")
        prn = getattr(self._current_result, "prn_number", "PRN")
        default_name = f"IMRD_Clearance_Certificate_{student_name}_{prn}.pdf"
        default_path = str(REPORTS_DIR / default_name)

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Official IMRD Clearance Certificate",
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
                    "student_name": getattr(self._current_result, "student_name", "Author"),
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
                    "direct_match_score": getattr(sb, "direct_match_score", 0.0),
                    "semantic_similarity_score": getattr(sb, "semantic_similarity_score", 0.0),
                    "citation_coverage_score": getattr(sb, "citation_coverage_score", 100.0),
                    "reference_verification_score": getattr(sb, "reference_verification_score", 100.0),
                    "high_risk_similarity": getattr(sb, "high_risk_similarity", 0.0),
                    "academic_verdict": getattr(sb, "academic_verdict", "LOW CONCERN"),
                }
                cit_dict = {
                    "citation_count": self._current_result.citations.citation_count,
                    "reference_count": self._current_result.citations.reference_count,
                    "quotes": self._current_result.citations.quotes,
                    "uncited_claims": self._current_result.citations.uncited_claims,
                    "citation_issues": getattr(self._current_result.citations, "citation_issues", []),
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
                    references=getattr(self._current_result, "references", []),
                )
                QMessageBox.information(
                    self,
                    "Certificate Generated",
                    f"Official IMRD Library Clearance Certificate successfully generated:\n\n{save_path}",
                )
            except Exception as e:
                logger.error(f"Certificate generation error: {e}", exc_info=True)
                QMessageBox.critical(self, "Generation Error", f"Could not generate clearance certificate: {e}")

    def _export_html(self):
        if not self._current_result:
            QMessageBox.warning(self, "No Document Loaded", "Please verify a research document before generating HTML report.")
            return

        student_name = getattr(self._current_result, "student_name", "Author").replace(" ", "_")
        prn = getattr(self._current_result, "prn_number", "PRN")
        default_name = f"IMRD_Audit_Report_{student_name}_{prn}.html"
        default_path = str(REPORTS_DIR / default_name)

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
                    "student_name": getattr(self._current_result, "student_name", "Author"),
                    "prn_number": getattr(self._current_result, "prn_number", "-"),
                    "course_name": getattr(self._current_result, "course_name", "MCA"),
                    "paper_title": getattr(self._current_result, "paper_title", self._current_result.document_filename),
                    "certificate_no": getattr(self._current_result, "certificate_no", "IMRD/LIB/PLAG/2026/0001"),
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
                    "academic_verdict": getattr(sb, "academic_verdict", "LOW CONCERN"),
                }
                gen.generate_report(
                    document_data=doc_data,
                    score_breakdown=score_dict,
                    extracted_text=self._current_result.extracted_text,
                    matches=self._current_result.matches,
                    references=getattr(self._current_result, "references", []),
                    citation_issues=getattr(self._current_result.citations, "citation_issues", []),
                )
                QMessageBox.information(
                    self,
                    "HTML Report Generated",
                    f"Interactive HTML Audit Report successfully generated:\n\n{save_path}",
                )
            except Exception as e:
                logger.error(f"HTML generation error: {e}", exc_info=True)
                QMessageBox.critical(self, "Generation Error", f"Could not generate HTML audit report: {e}")
