"""Central Library Dashboard view for SES's R. C. Patel IMRD Shirpur.
Displays academic verification KPIs, clearance distribution, and recent student submissions.
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from app.config import INSTITUTION_SHORT
from app.database.session import get_dashboard_metrics
from app.ml.semantic import get_model_status_text
from app.ui.widgets.cards import EmptyStateWidget, MetricCard, RiskBadge
from app.ui.widgets.charts import RiskDistributionWidget, SimilarityGaugeWidget, TimelineBarChartWidget


class DashboardView(QWidget):
    """Executive dashboard for the institute librarian presenting student paper verification statistics."""

    start_check_requested = Signal()
    view_document_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.refresh_data()

    def _init_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(20, 18, 20, 20)
        main_layout.setSpacing(14)

        # 1. Header Banner
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("Central Library • Student Plagiarism & Research Clearance Dashboard")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #002461;")
        sub_lbl = QLabel(
            f"{INSTITUTION_SHORT} • Plagiarism Verification Cell • UGC (Promotion of Academic Integrity) Regulations, 2018"
        )
        sub_lbl.setStyleSheet("font-size: 11.5px; color: #64748B;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box, 1)

        self.new_check_btn = QPushButton("+ Verify Student Paper")
        self.new_check_btn.setObjectName("certBtn")
        self.new_check_btn.setMinimumHeight(36)
        self.new_check_btn.setCursor(Qt.PointingHandCursor)
        self.new_check_btn.clicked.connect(self.start_check_requested.emit)
        header_layout.addWidget(self.new_check_btn)

        main_layout.addLayout(header_layout)

        # 2. Responsive KPI Cards Grid
        self.kpi_container = QWidget()
        self.kpi_grid = QGridLayout(self.kpi_container)
        self.kpi_grid.setContentsMargins(0, 0, 0, 0)
        self.kpi_grid.setSpacing(10)

        self.card_total = MetricCard("Total Papers Verified", "0", "Archived student papers", "#002461")
        self.card_cleared = MetricCard("UGC Level 0 Cleared", "0", "Within <= 10.0% limit", "#10B981")
        self.card_revisions = MetricCard("Revisions Required", "0", "10.1% to 60.0% range", "#D97706")
        self.card_avg = MetricCard("Average Similarity", "0.0%", "Across verified papers", "#005FEA")
        self.card_nlp = MetricCard("Verification Engine", "Ready", "Local NLP • all-MiniLM-L6-v2", "#059669")

        self.cards = [
            self.card_total,
            self.card_cleared,
            self.card_revisions,
            self.card_avg,
            self.card_nlp,
        ]

        self._relayout_cards(is_narrow=False)
        main_layout.addWidget(self.kpi_container)

        # 3. Aligned Analysis Panels (Equal Heights and Proportions)
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(14)

        # Left Panel: Gauge & Risk Distribution
        gauge_card = QFrame()
        gauge_card.setObjectName("card")
        gauge_card.setMinimumHeight(280)
        gauge_box = QVBoxLayout(gauge_card)
        gauge_box.setContentsMargins(16, 14, 16, 14)
        gauge_box.setSpacing(8)

        g_title = QLabel("AVERAGE SIMILARITY INDEX")
        g_title.setStyleSheet("color: #002461; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        gauge_box.addWidget(g_title)

        self.gauge_widget = SimilarityGaugeWidget()
        gauge_box.addWidget(self.gauge_widget, alignment=Qt.AlignCenter)

        self.risk_dist_widget = RiskDistributionWidget()
        gauge_box.addWidget(self.risk_dist_widget)
        charts_layout.addWidget(gauge_card, 1)

        # Right Panel: History Timeline Bar Chart
        timeline_card = QFrame()
        timeline_card.setObjectName("card")
        timeline_card.setMinimumHeight(280)
        timeline_box = QVBoxLayout(timeline_card)
        timeline_box.setContentsMargins(16, 14, 16, 14)
        timeline_box.setSpacing(8)

        t_title = QLabel("RECENT STUDENT DISSERTATION SIMILARITY SCORES")
        t_title.setStyleSheet("color: #002461; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        timeline_box.addWidget(t_title)

        self.timeline_widget = TimelineBarChartWidget()
        self.timeline_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        timeline_box.addWidget(self.timeline_widget)
        charts_layout.addWidget(timeline_card, 2)

        main_layout.addLayout(charts_layout)

        # 4. Recent Student Verifications Table & Empty State
        self.table_card = QFrame()
        self.table_card.setObjectName("card")
        self.table_box = QVBoxLayout(self.table_card)
        self.table_box.setContentsMargins(16, 14, 16, 14)
        self.table_box.setSpacing(10)

        tbl_hdr = QHBoxLayout()
        tbl_lbl = QLabel("Recent Student Dissertation Verifications")
        tbl_lbl.setStyleSheet("font-size: 13px; font-weight: 800; color: #002461;")
        tbl_hdr.addWidget(tbl_lbl)
        tbl_hdr.addStretch()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setFixedHeight(28)
        self.refresh_btn.setToolTip("Reload dashboard metrics and recent verifications")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.clicked.connect(self.refresh_data)
        tbl_hdr.addWidget(self.refresh_btn)
        self.table_box.addLayout(tbl_hdr)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "PRN / Roll No", "Student Name", "Program", "Verification Date", "Similarity", "UGC Clearance Status", "Action"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.table.setColumnWidth(5, 165)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 110)
        self.table.horizontalHeader().setMinimumSectionSize(75)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(40)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setMinimumHeight(120)
        self.table_box.addWidget(self.table)

        # Empty State
        self.empty_state = EmptyStateWidget(
            title="No Student Verifications Recorded Yet",
            message="Student dissertation checks, similarity indices, and official clearance certificates will appear here once papers are verified.",
            action_text="+ Verify First Student Paper",
            action_callback=self.start_check_requested.emit,
        )
        self.empty_state.setVisible(False)
        self.table_box.addWidget(self.empty_state)

        # Error State
        self.error_state = EmptyStateWidget(
            title="Dashboard Data Unavailable",
            message="An error occurred while loading the dashboard metrics. Please check the logs and try again.",
            action_text="Retry Loading Data",
            action_callback=self.refresh_data,
        )
        self.error_state.setVisible(False)
        self.table_box.addWidget(self.error_state)

        main_layout.addWidget(self.table_card)

        scroll.setWidget(container)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

    def _relayout_cards(self, is_narrow: bool):
        """Intelligently lays out statistic cards in 1 row (wide) or 2 rows (narrow)."""
        # Clear current grid
        while self.kpi_grid.count():
            item = self.kpi_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

        if is_narrow:
            # Row 0: 3 cards, Row 1: 2 cards
            for col, card in enumerate(self.cards[:3]):
                self.kpi_grid.addWidget(card, 0, col)
                self.kpi_grid.setColumnStretch(col, 1)
            for col, card in enumerate(self.cards[3:]):
                self.kpi_grid.addWidget(card, 1, col)
            self.kpi_grid.setColumnStretch(2, 1)
        else:
            # Row 0: all 5 cards
            for col, card in enumerate(self.cards):
                self.kpi_grid.addWidget(card, 0, col)
                self.kpi_grid.setColumnStretch(col, 1)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Adapt cards layout if width is under 1100px
        is_narrow = self.width() < 1100
        if getattr(self, "_is_narrow_state", None) != is_narrow:
            self._is_narrow_state = is_narrow
            self._relayout_cards(is_narrow)

    def refresh_data(self):
        """Pulls latest stats and recent checks from database."""
        try:
            metrics = get_dashboard_metrics()
            self.card_total.set_value(str(metrics["total_docs"]), "Archived student papers")
            self.card_cleared.set_value(str(metrics.get("approved_count", 0)), "UGC Level 0 (<=10%)")
            self.card_revisions.set_value(str(metrics.get("revisions_count", 0)), "UGC Level 1 & 2")
            self.card_avg.set_value(f"{metrics['avg_similarity']}%", "Institutional average")
            self.card_nlp.set_value("Ready ✓", "Local NLP Model Active")

            self.gauge_widget.set_value(metrics["avg_similarity"])
            self.risk_dist_widget.set_data(metrics["risk_distribution"])

            recent = metrics.get("recent_docs", [])
            timeline_tuples = [
                (d.get("student_name") or d["filename"], d["overall_similarity"])
                for d in reversed(recent)
            ]
            self.timeline_widget.set_data(timeline_tuples)

            if not recent:
                self.table.setVisible(False)
                self.empty_state.setVisible(True)
                self.error_state.setVisible(False)
            else:
                self.table.setVisible(True)
                self.empty_state.setVisible(False)
                self.error_state.setVisible(False)
                self.table.setRowCount(len(recent))
                row_h = 40
                header_h = self.table.horizontalHeader().height() or 34
                desired_h = min(360, header_h + len(recent) * row_h + 6)
                self.table.setMinimumHeight(desired_h)
                self.table.setMaximumHeight(desired_h)

                for row_idx, doc in enumerate(recent):
                    self.table.setRowHeight(row_idx, row_h)
                    self.table.setItem(row_idx, 0, QTableWidgetItem(doc.get("prn_number") or "-"))
                    name = doc.get("student_name") or doc["filename"]
                    self.table.setItem(row_idx, 1, QTableWidgetItem(name))
                    self.table.setItem(row_idx, 2, QTableWidgetItem(doc.get("course_name") or "MCA"))
                    self.table.setItem(row_idx, 3, QTableWidgetItem(doc["upload_date"][:10]))

                    sim_val = doc.get("overall_similarity", 0.0)
                    sim_item = QTableWidgetItem(f"{sim_val:.1f}%")
                    sim_item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row_idx, 4, sim_item)

                    # Clearance Status Badge
                    status_str = doc.get("clearance_status") or ("Approved (Level 0)" if sim_val <= 10.0 else "Revisions Required")
                    badge = QLabel(status_str)
                    badge.setAlignment(Qt.AlignCenter)
                    if "Approved" in status_str or sim_val <= 10.0:
                        bg, fg, border = "#ECFDF5", "#047857", "#10B981"
                    elif "Revisions" in status_str:
                        bg, fg, border = "#FFFBEB", "#B45309", "#F59E0B"
                    else:
                        bg, fg, border = "#FEF2F2", "#B91C1C", "#EF4444"

                    badge.setStyleSheet(f"""
                        background-color: {bg};
                        color: {fg};
                        border: 1px solid {border};
                        border-radius: 4px;
                        font-size: 11px;
                        font-weight: 700;
                        padding: 3px 8px;
                        min-height: 22px;
                    """)
                    badge_box = QWidget()
                    badge_box.setStyleSheet("background: transparent;")
                    badge_layout = QHBoxLayout(badge_box)
                    badge_layout.setContentsMargins(4, 2, 4, 2)
                    badge_layout.setAlignment(Qt.AlignCenter)
                    badge_layout.addWidget(badge)
                    self.table.setCellWidget(row_idx, 5, badge_box)

                    view_btn = QPushButton("Certificate")
                    view_btn.setObjectName("certBtn")
                    view_btn.setCursor(Qt.PointingHandCursor)
                    student_name_label = doc.get("student_name") or doc["filename"]
                    view_btn.setToolTip(f"View verification results for {student_name_label}")
                    view_btn.setAccessibleName(f"View certificate for {student_name_label}")
                    view_btn.clicked.connect(lambda chk=False, d_id=doc["id"]: self.view_document_requested.emit(d_id))

                    btn_box = QWidget()
                    btn_box.setStyleSheet("background: transparent;")
                    btn_layout = QHBoxLayout(btn_box)
                    btn_layout.setContentsMargins(6, 2, 6, 2)
                    btn_layout.setAlignment(Qt.AlignCenter)
                    btn_layout.addWidget(view_btn)
                    self.table.setCellWidget(row_idx, 6, btn_box)

        except Exception as e:
            from app.utils.logger import logger
            logger.error(f"Failed to refresh dashboard data: {e}", exc_info=True)
            self.table.setVisible(False)
            self.empty_state.setVisible(False)
            self.error_state.setVisible(True)
