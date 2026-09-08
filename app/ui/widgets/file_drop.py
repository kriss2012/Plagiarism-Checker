"""Drag and drop file upload target widget for student papers and dissertations."""

from pathlib import Path
from typing import List
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class FileDropWidget(QFrame):
    """Clean desktop drag & drop zone for uploading student PDF, DOCX, and TXT files."""

    files_selected = Signal(list)  # Emits list of file paths (List[str])

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(140)
        self._init_ui()

    def _init_ui(self):
        self._reset_style()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)
        layout.setContentsMargins(16, 16, 16, 16)

        self.main_text = QLabel("Drag & Drop Student Dissertation or Research Paper Here")
        self.main_text.setStyleSheet("font-size: 13.5px; font-weight: 700; color: #002461; background: transparent; border: none;")
        self.main_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.main_text)

        self.sub_text = QLabel("Supported formats: PDF (.pdf), Microsoft Word (.docx), Plain Text (.txt)")
        self.sub_text.setStyleSheet("font-size: 11px; color: #64748B; background: transparent; border: none;")
        self.sub_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.sub_text)

        # Browse button
        self.browse_btn = QPushButton("Browse Files...")
        self.browse_btn.setObjectName("primaryBtn")
        self.browse_btn.setFixedWidth(140)
        self.browse_btn.setFixedHeight(34)
        self.browse_btn.setCursor(Qt.PointingHandCursor)
        self.browse_btn.clicked.connect(self._open_file_dialog)
        layout.addWidget(self.browse_btn, alignment=Qt.AlignCenter)

    def _reset_style(self):
        self.setStyleSheet("""
            FileDropWidget {
                background-color: #F8FAFC;
                border: 2px dashed #CBD5E1;
                border-radius: 8px;
            }
            FileDropWidget:hover {
                border-color: #005FEA;
                background-color: #EFF6FF;
            }
        """)

    def _open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Student Dissertation / Research Paper",
            "",
            "Academic Documents (*.pdf *.docx *.txt);;PDF Documents (*.pdf);;Word Documents (*.docx);;Text Files (*.txt);;All Files (*.*)",
        )
        if files:
            self.files_selected.emit(files)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                FileDropWidget {
                    background-color: #EFF6FF;
                    border: 2px dashed #005FEA;
                    border-radius: 8px;
                }
            """)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._reset_style()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        valid_paths = []
        allowed_exts = {".pdf", ".docx", ".doc", ".txt", ".rtf", ".md"}

        for url in urls:
            local_path = url.toLocalFile()
            if local_path and Path(local_path).suffix.lower() in allowed_exts:
                valid_paths.append(local_path)

        self._reset_style()
        if valid_paths:
            self.files_selected.emit(valid_paths)

