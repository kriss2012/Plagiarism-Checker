"""Documents history view managing analyzed papers, filtering, and reporting."""

import os
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from app.config import REPORTS_DIR
from app.database.models import Document
from app.database.session import get_all_documents, get_db
from app.ui.widgets.cards import RiskBadge


class DocumentsView(QWidget):
    """Archived documents history view with search, risk filters, and action triggers."""

    view_doc_requested = Signal(int)  # document_id
    reanalyze_requested = Signal(int)  # document_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_docs = []
        self._init_ui()
        self.refresh_list()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        h_box = QVBoxLayout()
        title = QLabel("Analyzed Documents & Audit Archives")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #FFFFFF;")
        sub = QLabel("Browse historical plagiarism audits, filter by academic risk, and re-export reports")
        sub.setStyleSheet("font-size: 13px; color: #94A3B8;")
        h_box.addWidget(title)
        h_box.addWidget(sub)
        layout.addLayout(h_box)

        # Filter & Search Bar
        filter_card = QFrame()
        filter_card.setObjectName("card")
        f_layout = QHBoxLayout(filter_card)
        f_layout.setContentsMargins(12, 10, 12, 10)

        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search documents by filename or hash...")
        self.search_input.textChanged.connect(self._apply_filters)
        f_layout.addWidget(self.search_input, 2)

        # Risk Filter
        f_layout.addWidget(QLabel("Risk Level:"))
        self.risk_filter = QComboBox()
        self.risk_filter.addItems(["All Risk Levels", "Very Low", "Low", "Moderate", "High", "Very High"])
        self.risk_filter.currentTextChanged.connect(self._apply_filters)
        f_layout.addWidget(self.risk_filter, 1)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_list)
        f_layout.addWidget(refresh_btn)

        layout.addWidget(filter_card)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Document", "Date", "Word Count", "Similarity", "Risk", "Status", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 6):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

    def refresh_list(self):
        """Fetches all documents from database and populates table."""
        try:
            self._all_docs = [d.to_dict() for d in get_all_documents(limit=200)]
            self._apply_filters()
        except Exception as e:
            pass

    def _apply_filters(self):
        search_txt = self.search_input.text().strip().lower()
        risk_sel = self.risk_filter.currentText()

        filtered = []
        for d in self._all_docs:
            # Name filter
            if search_txt and search_txt not in d["filename"].lower() and search_txt not in d["hash"].lower():
                continue
            # Risk filter
            if risk_sel != "All Risk Levels" and d["risk_level"] != risk_sel:
                continue
            filtered.append(d)

        self.table.setRowCount(len(filtered))
        for r_idx, doc in enumerate(filtered):
            self.table.setItem(r_idx, 0, QTableWidgetItem(doc["filename"]))
            self.table.setItem(r_idx, 1, QTableWidgetItem(doc["upload_date"][:10]))
            self.table.setItem(r_idx, 2, QTableWidgetItem(f"{doc['word_count']:,}"))

            sim_item = QTableWidgetItem(f"{doc['overall_similarity']:.1f}%")
            sim_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r_idx, 3, sim_item)

            badge = RiskBadge(doc["risk_level"])
            self.table.setCellWidget(r_idx, 4, badge)

            self.table.setItem(r_idx, 5, QTableWidgetItem(doc["status"]))

            # Actions cell
            btn_box = QWidget()
            b_layout = QHBoxLayout(btn_box)
            b_layout.setContentsMargins(0, 0, 0, 0)
            b_layout.setSpacing(4)

            view_btn = QPushButton("View")
            view_btn.setFixedHeight(24)
            view_btn.clicked.connect(lambda chk=False, d_id=doc["id"]: self.view_doc_requested.emit(d_id))
            b_layout.addWidget(view_btn)

            del_btn = QPushButton("Delete")
            del_btn.setFixedHeight(24)
            del_btn.setStyleSheet("color: #F87171; border-color: #7F1D1D;")
            del_btn.clicked.connect(lambda chk=False, d_id=doc["id"]: self._delete_document(d_id))
            b_layout.addWidget(del_btn)

            self.table.setCellWidget(r_idx, 6, btn_box)

    def _delete_document(self, doc_id: int):
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to delete this document audit record?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            with get_db() as session:
                target = session.query(Document).filter_by(id=doc_id).first()
                if target:
                    session.delete(target)
            self.refresh_list()
