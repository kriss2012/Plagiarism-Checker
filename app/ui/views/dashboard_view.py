"""Central Library Dashboard view for SES's R. C. Patel IMRD Shirpur.
Displays academic verification KPIs, clearance distribution, and recent student submissions.
"""

from typing import Optional
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
from app.config import INSTITUTION_SHORT
from app.database.session import get_dashboard_metrics
from app.ml.semantic import get_model_status_text
from app.ui.widgets.cards import MetricCard, RiskBadge
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
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_lbl = QLabel("Central Library • Student Plagiarism & Research Clearance Dashboard")
        title_lbl.setStyleSheet("font-size: 19px; font-weight: 800; color: #002461;")
        sub_lbl = QLabel(
            f"{INSTITUTION_SHORT} • Plagiarism Verification Cell • UGC (Promotion of Academic Integrity) Regulations, 2018"
        )
        sub_lbl.setStyleSheet("font-size: 12px; color: #64748B;")
        title_box.addWidget(title_lbl)
        title_box.addWidget(sub_lbl)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.new_check_btn = QPushButton("+ Verify Student Paper")
        self.new_check_btn.setObjectName("certBtn")
        self.new_check_btn.setMinimumHeight(38)
        self.new_check_btn.setCursor(Qt.PointingHandCursor)
        self.new_check_btn.clicked.connect(self.start_check_requested.emit)
        header_layout.addWidget(self.new_check_btn)

        main_layout.addLayout(header_layout)

        # 2. KPI Cards Grid
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(12)

        self.card_total = MetricCard("Total Papers Verified", "0", "Archived student reports", "#002461")
        self.card_cleared = MetricCard("UGC Level 0 Cleared", "0", "Within <= 10% limit", "#10B981")
        self.card_revisions = MetricCard("Revisions Required", "0", "10.1% to 60.0% range", "#D97706")
        self.card_avg = MetricCard("Average Similarity", "0.0%", "Across verified papers", "#005FEA")
        self.card_nlp = MetricCard("Verification Engine", "Active", get_model_status_text(), "#059669")

        kpi_layout.addWidget(self.card_total)
        kpi_layout.addWidget(self.card_cleared)
        kpi_layout.addWidget(self.card_revisions)
        kpi_layout.addWidget(self.card_avg)
        kpi_layout.addWidget(self.card_nlp)

        main_layout.addLayout(kpi_layout)

        # 3. Charts Row
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(14)

        # Left Chart: Gauge & Risk Breakdown
        gauge_card = QFrame()
        gauge_card.setObjectName("card")
        gauge_box = QVBoxLayout(gauge_card)
        g_title = QLabel("AVERAGE SIMILARITY INDEX")
        g_title.setStyleSheet("color: #002461; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        gauge_box.addWidget(g_title)
        self.gauge_widget = SimilarityGaugeWidget()
        gauge_box.addWidget(self.gauge_widget, alignment=Qt.AlignCenter)
        self.risk_dist_widget = RiskDistributionWidget()
        gauge_box.addWidget(self.risk_dist_widget)
        charts_layout.addWidget(gauge_card, 1)

        # Right Chart: History Timeline
        timeline_card = QFrame()
        timeline_card.setObjectName("card")
        timeline_box = QVBoxLayout(timeline_card)
        t_title = QLabel("RECENT STUDENT DISSERTATION SIMILARITY SCORES")
        t_title.setStyleSheet("color: #002461; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        timeline_box.addWidget(t_title)
        self.timeline_widget = TimelineBarChartWidget()
        timeline_box.addWidget(self.timeline_widget)
        charts_layout.addWidget(timeline_card, 2)

        main_layout.addLayout(charts_layout)

        # 4. Recent Student Verifications Table
        table_card = QFrame()
        table_card.setObjectName("card")
        table_box = QVBoxLayout(table_card)
        table_box.setSpacing(8)

        tbl_hdr = QHBoxLayout()
        tbl_lbl = QLabel("Recent Student Dissertation Verifications")
        tbl_lbl.setStyleSheet("font-size: 13px; font-weight: 800; color: #002461;")
        tbl_hdr.addWidget(tbl_lbl)
        tbl_hdr.addStretch()

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setFixedHeight(26)
        self.refresh_btn.clicked.connect(self.refresh_data)
        tbl_hdr.addWidget(self.refresh_btn)
        table_box.addLayout(tbl_hdr)

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
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setFixedHeight(180)
        table_box.addWidget(self.table)

        main_layout.addWidget(table_card)

        scroll.setWidget(container)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

    def refresh_data(self):
        """Pulls latest stats and recent checks from database."""
        try:
            metrics = get_dashboard_metrics()
            self.card_total.set_value(str(metrics["total_docs"]), "Archived papers")
            self.card_cleared.set_value(str(metrics.get("approved_count", 0)), "UGC Level 0")
            self.card_revisions.set_value(str(metrics.get("revisions_count", 0)), "Level 1 & 2")
            self.card_avg.set_value(f"{metrics['avg_similarity']}%", "Institutional average")
            self.card_nlp.set_value("Ready ✓", get_model_status_text())

            self.gauge_widget.set_value(metrics["avg_similarity"])
            self.risk_dist_widget.set_data(metrics["risk_distribution"])

            recent = metrics["recent_docs"]
            timeline_tuples = [
                (d.get("student_name") or d["filename"], d["overall_similarity"])
                for d in reversed(recent)
            ]
            self.timeline_widget.set_data(timeline_tuples)

            self.table.setRowCount(len(recent))
            for row_idx, doc in enumerate(recent):
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
                    font-size: 10px;
                    font-weight: 700;
                    padding: 2px 6px;
                """)
                self.table.setCellWidget(row_idx, 5, badge)

                view_btn = QPushButton("Certificate")
                view_btn.setObjectName("certBtn")
                view_btn.setFixedHeight(24)
                view_btn.setStyleSheet("padding: 2px 8px; font-size: 11px;")
                view_btn.clicked.connect(lambda chk=False, d_id=doc["id"]: self.view_document_requested.emit(d_id))
                self.table.setCellWidget(row_idx, 6, view_btn)

        except Exception:
            pass
