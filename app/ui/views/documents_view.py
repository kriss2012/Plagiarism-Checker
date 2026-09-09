"""Student Plagiarism Verification Records & Master Library Register view.
Provides the IMRD Central Library with filtering by student, PRN, program, year, and UGC clearance status.
"""

import csv
from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
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
from app.ui.widgets.cards import EmptyStateWidget
from app.ui.widgets.cards import RiskBadge


class DocumentsView(QWidget):
    """Master archive register of verified student dissertations and project papers."""

    view_doc_requested = Signal(int)  # document_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_docs = []
        self._load_error = False
        self._init_ui()
        self.refresh_list()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(12)

        # 1. Header
        h_box = QHBoxLayout()
        v_title = QVBoxLayout()
        v_title.setSpacing(2)
        title = QLabel("Student Plagiarism Verification Records & Library Register")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #002461;")
        sub = QLabel("Official record of student dissertations, similarity indices, and UGC clearance certificates")
        sub.setStyleSheet("font-size: 11.5px; color: #64748B;")
        sub.setWordWrap(True)
        v_title.addWidget(title)
        v_title.addWidget(sub)
        h_box.addLayout(v_title, 1)

        self.export_csv_btn = QPushButton("Export Register (CSV)")
        self.export_csv_btn.setFixedHeight(32)
        self.export_csv_btn.setCursor(Qt.PointingHandCursor)
        self.export_csv_btn.setToolTip("Export the complete verification register as a CSV file for NAAC inspection")
        self.export_csv_btn.clicked.connect(self.export_to_csv)
        h_box.addWidget(self.export_csv_btn)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setFixedHeight(32)
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setToolTip("Reload student records from the database")
        self.refresh_btn.clicked.connect(self.refresh_list)
        h_box.addWidget(self.refresh_btn)

        layout.addLayout(h_box)

        # 2. Search & Filter Bar
        filter_card = QFrame()
        filter_card.setObjectName("card")
        f_layout = QHBoxLayout(filter_card)
        f_layout.setContentsMargins(12, 8, 12, 8)
        f_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Student Name, PRN, or Title...")
        self.search_input.setToolTip("Search across student name, PRN number, paper title, and filename")
        self.search_input.textChanged.connect(self._apply_filters)
        f_layout.addWidget(self.search_input, 3)

        prog_lbl = QLabel("Program:")
        prog_lbl.setMinimumWidth(60)
        f_layout.addWidget(prog_lbl)
        self.course_filter = QComboBox()
        self.course_filter.addItems(["All Programs", "MCA", "MBA", "BCA", "BBA", "Integrated MCA"])
        self.course_filter.setToolTip("Filter records by academic program")
        self.course_filter.currentTextChanged.connect(self._apply_filters)
        f_layout.addWidget(self.course_filter, 1)

        ugc_lbl = QLabel("UGC Status:")
        ugc_lbl.setMinimumWidth(72)
        f_layout.addWidget(ugc_lbl)
        self.status_filter = QComboBox()
        self.status_filter.addItems([
            "All Statuses",
            "Approved (Level 0)",
            "Revisions Required (Level 1)",
            "Major Revisions (Level 2)",
            "Rejected (Level 3)",
        ])
        self.status_filter.setToolTip("Filter records by UGC plagiarism clearance status")
        self.status_filter.currentTextChanged.connect(self._apply_filters)
        f_layout.addWidget(self.status_filter, 2)

        layout.addWidget(filter_card)

        # 3. Master Register Table
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Cert. No.", "PRN / Roll No", "Student Name", "Program",
            "Supervisor", "Date", "Similarity", "UGC Clearance", "Actions"
        ])

        # Column sizing
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.Stretch)
        hh.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(7, QHeaderView.Fixed)
        hh.setSectionResizeMode(8, QHeaderView.Fixed)
        self.table.setColumnWidth(7, 165)
        self.table.setColumnWidth(8, 185)
        hh.setMinimumSectionSize(60)

        self.table.verticalHeader().setVisible(False)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        layout.addWidget(self.table)

        # ── Three distinct empty/error states (only one shown at a time) ──
        self.empty_state = EmptyStateWidget(
            title="No Student Verification Records Found",
            message=(
                "No verified student dissertations or project papers have been processed yet. "
                "Use 'Verify Student Paper' to conduct the first plagiarism check."
            ),
        )
        self.empty_state.setVisible(False)
        layout.addWidget(self.empty_state)

        self.no_results_state = EmptyStateWidget(
            title="No Records Match Your Search / Filter",
            message=(
                "Modify the search text, program filter, or UGC status filter to find matching records."
            ),
        )
        self.no_results_state.setVisible(False)
        layout.addWidget(self.no_results_state)

        self.error_state = EmptyStateWidget(
            title="Unable to Load Student Verification Records",
            message=(
                "A database error occurred while retrieving records. "
                "Please click Retry or restart the application."
            ),
            action_text="Retry",
            action_callback=self.refresh_list,
        )
        self.error_state.setVisible(False)
        layout.addWidget(self.error_state)

    def _hide_all_states(self):
        self.table.setVisible(False)
        self.empty_state.setVisible(False)
        self.no_results_state.setVisible(False)
        self.error_state.setVisible(False)

    def _has_active_filters(self) -> bool:
        return bool(
            self.search_input.text().strip()
            or self.course_filter.currentText() != "All Programs"
            or self.status_filter.currentText() != "All Statuses"
        )

    def refresh_list(self):
        """Fetches all student documents from database."""
        self._load_error = False
        try:
            self._all_docs = [d.to_dict() for d in get_all_documents(limit=500)]
            self._apply_filters()
        except Exception:
            self._load_error = True
            self._all_docs = []
            self._hide_all_states()
            self.error_state.setVisible(True)

    def _apply_filters(self):
        search_txt = self.search_input.text().strip().lower()
        course_sel = self.course_filter.currentText()
        status_sel = self.status_filter.currentText()

        filtered = []
        for d in self._all_docs:
            name = (d.get("student_name") or "").lower()
            prn = (d.get("prn_number") or "").lower()
            title = (d.get("paper_title") or "").lower()
            fn = (d.get("filename") or "").lower()

            if search_txt and not any(search_txt in field for field in (name, prn, title, fn)):
                continue

            if course_sel != "All Programs":
                doc_course = d.get("course_name") or "MCA"
                if course_sel not in doc_course:
                    continue

            if status_sel != "All Statuses":
                doc_status = d.get("clearance_status") or ""
                if status_sel != doc_status:
                    continue

            filtered.append(d)

        self._hide_all_states()

        if not filtered:
            if not self._all_docs:
                self.empty_state.setVisible(True)
            elif self._has_active_filters():
                self.no_results_state.setVisible(True)
            else:
                self.empty_state.setVisible(True)
            return

        self.table.setVisible(True)
        self.table.setRowCount(len(filtered))

        for r_idx, doc in enumerate(filtered):
            self.table.setRowHeight(r_idx, 38)
            cert_no = doc.get("certificate_no") or f"IMRD/LIB/{doc['id']:04d}"

            cert_item = QTableWidgetItem(cert_no)
            cert_item.setToolTip(cert_no)
            self.table.setItem(r_idx, 0, cert_item)

            self.table.setItem(r_idx, 1, QTableWidgetItem(doc.get("prn_number") or "-"))

            name_item = QTableWidgetItem(doc.get("student_name") or doc["filename"])
            name_item.setToolTip(doc.get("paper_title") or doc["filename"])
            self.table.setItem(r_idx, 2, name_item)

            self.table.setItem(r_idx, 3, QTableWidgetItem(doc.get("course_name") or "MCA"))
            self.table.setItem(r_idx, 4, QTableWidgetItem(doc.get("guide_name") or "-"))
            self.table.setItem(r_idx, 5, QTableWidgetItem(doc["upload_date"][:10]))

            sim_val = doc.get("overall_similarity", 0.0)
            sim_item = QTableWidgetItem(f"{sim_val:.1f}%")
            sim_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r_idx, 6, sim_item)

            # UGC Clearance Badge
            status_str = doc.get("clearance_status") or (
                "Approved (Level 0)" if sim_val <= 10.0 else "Revisions Required (Level 1)"
            )
            badge = QLabel(status_str)
            badge.setAlignment(Qt.AlignCenter)

            if "Approved" in status_str or sim_val <= 10.0:
                bg, fg, border = "#ECFDF5", "#047857", "#10B981"
            elif "Revisions Required" in status_str:
                bg, fg, border = "#FFFBEB", "#B45309", "#F59E0B"
            elif "Major" in status_str:
                bg, fg, border = "#FEF2F2", "#B91C1C", "#EF4444"
            else:
                bg, fg, border = "#450A0A", "#FFFFFF", "#991B1B"

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
            self.table.setCellWidget(r_idx, 7, badge_box)

            # ── Actions cell ──────────────────────────────────────────
            btn_box = QWidget()
            btn_box.setContentsMargins(0, 0, 0, 0)
            b_layout = QHBoxLayout(btn_box)
            b_layout.setContentsMargins(4, 2, 4, 2)
            b_layout.setSpacing(6)

            student_label = doc.get("student_name") or doc["filename"]

            view_btn = QPushButton("Certificate")
            view_btn.setObjectName("certBtn")
            view_btn.setFixedHeight(24)
            view_btn.setMinimumWidth(82)
            view_btn.setStyleSheet("padding: 2px 6px; font-size: 11px;")
            view_btn.setCursor(Qt.PointingHandCursor)
            view_btn.setToolTip(f"View results and print clearance certificate for {student_label}")
            view_btn.setAccessibleName(f"View certificate for {student_label}")
            view_btn.clicked.connect(
                lambda chk=False, d_id=doc["id"]: self.view_doc_requested.emit(d_id)
            )
            b_layout.addWidget(view_btn)

            del_btn = QPushButton("Delete")
            del_btn.setObjectName("dangerBtn")
            del_btn.setFixedHeight(24)
            del_btn.setMinimumWidth(60)
            del_btn.setStyleSheet("font-size: 11px; padding: 2px 6px;")
            del_btn.setCursor(Qt.PointingHandCursor)
            del_btn.setToolTip(f"Permanently delete the verification record for {student_label}")
            del_btn.setAccessibleName(f"Delete record for {student_label}")
            del_btn.clicked.connect(
                lambda chk=False, d_id=doc["id"]: self._delete_document(d_id)
            )
            b_layout.addWidget(del_btn)

            b_layout.addStretch()
            self.table.setCellWidget(r_idx, 8, btn_box)

    def _delete_document(self, doc_id: int):
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to permanently delete this student verification record?\n\n"
            "This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            try:
                with get_db() as session:
                    target = session.query(Document).filter_by(id=doc_id).first()
                    if target:
                        session.delete(target)
                self.refresh_list()
            except Exception as e:
                QMessageBox.critical(
                    self, "Deletion Error",
                    f"Could not delete the student record:\n{e}",
                )

    def export_to_csv(self):
        """Exports the student verification register to CSV for NAAC/academic inspection."""
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Library Verification Register (CSV)",
            str(REPORTS_DIR / "IMRD_Library_Plagiarism_Register.csv"),
            "CSV Files (*.csv)",
        )
        if save_path:
            try:
                with open(save_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "Certificate No",
                        "PRN / Roll No",
                        "Student Full Name",
                        "Program",
                        "Academic Year",
                        "Semester",
                        "Faculty Supervisor",
                        "Dissertation Title",
                        "Verification Date",
                        "Word Count",
                        "Overall Similarity (%)",
                        "UGC Clearance Status",
                    ])
                    for d in self._all_docs:
                        writer.writerow([
                            d.get("certificate_no") or f"IMRD/LIB/{d['id']:04d}",
                            d.get("prn_number", "-"),
                            d.get("student_name", "-"),
                            d.get("course_name", "MCA"),
                            d.get("academic_year", "2025-2026"),
                            d.get("semester", "Semester IV"),
                            d.get("guide_name", "-"),
                            d.get("paper_title", d.get("filename", "")),
                            d.get("upload_date", "")[:10],
                            d.get("word_count", 0),
                            d.get("overall_similarity", 0.0),
                            d.get("clearance_status", "Approved (Level 0)"),
                        ])
                QMessageBox.information(
                    self, "Export Complete",
                    f"Library register successfully exported to:\n{save_path}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Could not export CSV: {e}")
