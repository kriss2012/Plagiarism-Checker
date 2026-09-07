"""Dashboard view displaying academic integrity KPIs, risk distribution, charts, and recent checks."""

from typing import Callable, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from app.database.session import get_dashboard_metrics
from app.ml.semantic import get_model_status_text
from app.ui.widgets.cards import MetricCard, RiskBadge
from app.ui.widgets.charts import RiskDistributionWidget, SimilarityGaugeWidget, TimelineBarChartWidget


class DashboardView(QWidget):
    """Executive dashboard presenting high-level similarity statistics and recent history."""

    start_check_requested = Signal()
    view_document_requested = Signal(int)  # document_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.refresh_data()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Top Header Banner
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_lbl = QLabel("Academic Integrity & Plagiarism Dashboard")
        title_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: #FFFFFF;")
        sub_lbl = QLabel("Comprehensive similarity overview, heuristic risk metrics, and recent paper audits")
        sub_lbl.setStyleSheet("font-size: 13px; color: #94A3B8;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.new_check_btn = QPushButton("+ New Plagiarism Check")
        self.new_check_btn.setObjectName("primaryBtn")
        self.new_check_btn.setMinimumHeight(38)
        self.new_check_btn.clicked.connect(self.start_check_requested.emit)
        header_layout.addWidget(self.new_check_btn)

        main_layout.addLayout(header_layout)

        # KPI Metric Cards Grid
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(14)

        self.card_total = MetricCard("Total Documents", "0", "Archived papers", "#4F46E5")
        self.card_avg = MetricCard("Average Similarity", "0.0%", "Across all checks", "#3B82F6")
        self.card_high = MetricCard("Highest Similarity", "0.0%", "Peak similarity index", "#F59E0B")
        self.card_risk = MetricCard("High Risk Papers", "0", "> 40% threshold", "#EF4444")
        self.card_nlp = MetricCard("NLP Model Status", "Ready", get_model_status_text(), "#10B981")

        kpi_layout.addWidget(self.card_total)
        kpi_layout.addWidget(self.card_avg)
        kpi_layout.addWidget(self.card_high)
        kpi_layout.addWidget(self.card_risk)
        kpi_layout.addWidget(self.card_nlp)

        main_layout.addLayout(kpi_layout)

        # Charts Section
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(16)

        # Left Chart: Gauge & Risk Breakdown
        gauge_card = QFrame()
        gauge_card.setObjectName("card")
        gauge_box = QVBoxLayout(gauge_card)
        gauge_box.addWidget(QLabel("AVERAGE SYSTEM SIMILARITY"))
        self.gauge_widget = SimilarityGaugeWidget()
        gauge_box.addWidget(self.gauge_widget, alignment=Qt.AlignCenter)
        self.risk_dist_widget = RiskDistributionWidget()
        gauge_box.addWidget(self.risk_dist_widget)
        charts_layout.addWidget(gauge_card, 1)

        # Right Chart: History Timeline
        timeline_card = QFrame()
        timeline_card.setObjectName("card")
        timeline_box = QVBoxLayout(timeline_card)
        timeline_box.addWidget(QLabel("SIMILARITY SCORES OF RECENT AUDITS"))
        self.timeline_widget = TimelineBarChartWidget()
        timeline_box.addWidget(self.timeline_widget)
        charts_layout.addWidget(timeline_card, 2)

        main_layout.addLayout(charts_layout)

        # Recent Checks Table
        table_card = QFrame()
        table_card.setObjectName("card")
        table_box = QVBoxLayout(table_card)

        tbl_hdr = QHBoxLayout()
        tbl_lbl = QLabel("Recent Document Analyses")
        tbl_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        tbl_hdr.addWidget(tbl_lbl)
        tbl_hdr.addStretch()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setFixedWidth(80)
        self.refresh_btn.clicked.connect(self.refresh_data)
        tbl_hdr.addWidget(self.refresh_btn)
        table_box.addLayout(tbl_hdr)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Document", "Date Analyzed", "Word Count", "Similarity", "Risk Level", "Action"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setMinimumHeight(180)
        table_box.addWidget(self.table)

        main_layout.addWidget(table_card)

    def refresh_data(self):
        """Pulls latest stats and recent checks from database."""
        try:
            metrics = get_dashboard_metrics()
            self.card_total.set_value(str(metrics["total_docs"]), "Archived papers")
            self.card_avg.set_value(f"{metrics['avg_similarity']}%", "System average")
            self.card_high.set_value(f"{metrics['highest_similarity']}%", "Max detected")
            self.card_risk.set_value(str(metrics["high_risk_count"]), "> 40% threshold")
            self.card_nlp.set_value("Loaded ✓", get_model_status_text())

            self.gauge_widget.set_value(metrics["avg_similarity"])
            self.risk_dist_widget.set_data(metrics["risk_distribution"])

            # Update timeline chart with recent docs
            recent = metrics["recent_docs"]
            timeline_tuples = [(d["filename"], d["overall_similarity"]) for d in reversed(recent)]
            self.timeline_widget.set_data(timeline_tuples)

            # Update table
            self.table.setRowCount(len(recent))
            for row_idx, doc in enumerate(recent):
                self.table.setItem(row_idx, 0, QTableWidgetItem(doc["filename"]))
                self.table.setItem(row_idx, 1, QTableWidgetItem(doc["upload_date"][:10]))
                self.table.setItem(row_idx, 2, QTableWidgetItem(f"{doc['word_count']:,}"))

                sim_item = QTableWidgetItem(f"{doc['overall_similarity']:.1f}%")
                sim_item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_idx, 3, sim_item)

                badge = RiskBadge(doc["risk_level"])
                self.table.setCellWidget(row_idx, 4, badge)

                view_btn = QPushButton("View")
                view_btn.setFixedHeight(26)
                view_btn.clicked.connect(lambda chk=False, d_id=doc["id"]: self.view_document_requested.emit(d_id))
                self.table.setCellWidget(row_idx, 5, view_btn)

        except Exception as e:
            pass
