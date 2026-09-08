"""Source Library view for managing reference papers, textbooks, and comparison corpora."""

from pathlib import Path
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from app.core.extractor import DocumentExtractor
from app.database.models import Source
from app.database.session import get_all_sources, get_db
from app.utils.logger import logger
from app.utils.security import compute_text_sha256


class AddSourceDialog(QDialog):
    """Dialog allowing user to add a source manually or via file extraction."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Reference Document to Library")
        self.setMinimumWidth(480)
        self.extracted_text = ""
        self.file_path = ""
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # File browse option
        f_box = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Select PDF, Word (DOCX), or TXT file...")
        self.path_input.setReadOnly(True)
        f_box.addWidget(self.path_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_file)
        f_box.addWidget(browse_btn)
        layout.addLayout(f_box)

        # Metadata form
        form = QFormLayout()
        self.title_input = QLineEdit()
        form.addRow("Title *:", self.title_input)

        self.author_input = QLineEdit()
        form.addRow("Author(s):", self.author_input)

        self.year_input = QLineEdit()
        self.year_input.setPlaceholderText("e.g. 2024")
        form.addRow("Publication Year:", self.year_input)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Journal", "Conference", "Book", "Thesis", "Website", "Internal Document", "Other"])
        form.addRow("Source Type:", self.type_combo)

        self.doi_input = QLineEdit()
        self.doi_input.setPlaceholderText("10.xxxx/...")
        form.addRow("DOI:", self.doi_input)

        self.url_input = QLineEdit()
        form.addRow("URL:", self.url_input)

        layout.addLayout(form)

        # Direct text or abstract
        layout.addWidget(QLabel("Text Content / Abstract:"))
        self.text_content = QTextEdit()
        self.text_content.setPlaceholderText("Paste paper content, abstract, or chapter text...")
        layout.addWidget(self.text_content)

        # Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)

        save_btn = QPushButton("Save to Library")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._save_source)
        btn_box.addWidget(save_btn)

        layout.addLayout(btn_box)

    def _browse_file(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Reference Source Document", "", "Documents (*.pdf *.docx *.txt)"
        )
        if file:
            self.file_path = file
            self.path_input.setText(file)
            try:
                ext = DocumentExtractor()
                res = ext.extract(file)
                self.title_input.setText(Path(file).stem.replace("_", " "))
                self.extracted_text = res.full_text
                self.text_content.setPlainText(res.full_text[:3000] + ("..." if len(res.full_text) > 3000 else ""))
            except Exception as e:
                QMessageBox.warning(self, "Extraction Warning", f"Could not extract file text: {e}")

    def _save_source(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Validation Error", "Please provide a title for the reference source.")
            return

        year_val = None
        if self.year_input.text().strip().isdigit():
            year_val = int(self.year_input.text().strip())

        full_content = self.extracted_text or self.text_content.toPlainText().strip()
        content_hash = compute_text_sha256(full_content) if full_content else ""

        with get_db() as session:
            new_src = Source(
                title=title,
                author=self.author_input.text().strip() or "Unknown",
                publication_year=year_val,
                source_type=self.type_combo.currentText(),
                doi=self.doi_input.text().strip(),
                url=self.url_input.text().strip(),
                filepath=self.file_path,
                text_content=full_content,
                content_hash=content_hash,
                word_count=len(full_content.split()),
            )
            session.add(new_src)
            session.commit()

        self.accept()


from app.ui.widgets.cards import EmptyStateWidget


class SourceLibraryView(QWidget):
    """View presenting repository of reference books, journals, and previous publications."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self.refresh_list()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 20)
        layout.setSpacing(14)

        # Header
        h_box = QHBoxLayout()
        v_title = QVBoxLayout()
        v_title.setSpacing(2)
        title = QLabel("Central Library Reference Source Repository")
        title.setStyleSheet("font-size: 18px; font-weight: 800; color: #002461;")
        sub = QLabel("Institutional repository of academic journals, textbooks, syllabus materials, and past dissertations")
        sub.setStyleSheet("font-size: 11.5px; color: #64748B;")
        v_title.addWidget(title)
        v_title.addWidget(sub)
        h_box.addLayout(v_title, 1)

        add_btn = QPushButton("+ Add Reference Source")
        add_btn.setObjectName("primaryBtn")
        add_btn.setFixedHeight(34)
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self._open_add_dialog)
        h_box.addWidget(add_btn)

        layout.addLayout(h_box)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Title", "Author", "Year", "Type", "Words", "Date Added", "Actions"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 6):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        self.table.setColumnWidth(6, 90)
        self.table.horizontalHeader().setMinimumSectionSize(75)
        self.table.verticalHeader().setVisible(False)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(self.table)

        # Empty State
        self.empty_state = EmptyStateWidget(
            title="No Reference Sources in Library",
            message="Add reference textbooks, academic journals, syllabus guides, or past student dissertations to expand the institutional comparison corpus.",
            action_text="+ Add First Reference Source",
            action_callback=self._open_add_dialog,
        )
        self.empty_state.setVisible(False)
        layout.addWidget(self.empty_state)

    def refresh_list(self):
        """Loads and updates table with sources from database."""
        try:
            sources = get_all_sources()
            if not sources:
                self.table.setVisible(False)
                self.empty_state.setVisible(True)
            else:
                self.table.setVisible(True)
                self.empty_state.setVisible(False)
                self.table.setRowCount(len(sources))
                for r_idx, s in enumerate(sources):
                    self.table.setItem(r_idx, 0, QTableWidgetItem(s.title))
                    self.table.setItem(r_idx, 1, QTableWidgetItem(s.author or "Unknown"))
                    self.table.setItem(r_idx, 2, QTableWidgetItem(str(s.publication_year or "-")))
                    self.table.setItem(r_idx, 3, QTableWidgetItem(s.source_type or "Journal"))
                    self.table.setItem(r_idx, 4, QTableWidgetItem(f"{s.word_count:,}"))
                    self.table.setItem(r_idx, 5, QTableWidgetItem(s.created_at.strftime("%Y-%m-%d") if s.created_at else "-"))

                    del_btn = QPushButton("Delete")
                    del_btn.setObjectName("dangerBtn")
                    del_btn.setFixedHeight(24)
                    del_btn.setStyleSheet("font-size: 11px; padding: 2px 8px;")
                    del_btn.setCursor(Qt.PointingHandCursor)
                    del_btn.clicked.connect(lambda chk=False, s_id=s.id: self._delete_source(s_id))
                    self.table.setCellWidget(r_idx, 6, del_btn)
        except Exception:
            pass

    def _open_add_dialog(self):
        dlg = AddSourceDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self.refresh_list()

    def _delete_source(self, source_id: int):
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            "Are you sure you want to remove this source from your reference library?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if confirm == QMessageBox.Yes:
            with get_db() as session:
                target = session.query(Source).filter_by(id=source_id).first()
                if target:
                    session.delete(target)
            self.refresh_list()
