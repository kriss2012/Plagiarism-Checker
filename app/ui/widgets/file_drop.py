"""Drag and drop file upload target widget for research papers."""

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
    """Modern drag & drop zone for uploading PDF, DOCX, and TXT files."""

    files_selected = Signal(list)  # Emits list of file paths (List[str])

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.StyledPanel)
        self.setMinimumHeight(170)
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 41, 59, 0.5);
                border: 2px dashed #475569;
                border-radius: 12px;
            }
            QFrame:hover {
                border-color: #6366F1;
                background-color: rgba(99, 102, 241, 0.05);
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(10)

        # Upload icon / text
        self.icon_label = QLabel("📄")
        self.icon_label.setStyleSheet("font-size: 32px; background: transparent; border: none;")
        self.icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.icon_label)

        self.main_text = QLabel("Drag & drop research papers here")
        self.main_text.setStyleSheet("font-size: 15px; font-weight: 600; color: #F8FAFC; background: transparent; border: none;")
        self.main_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.main_text)

        self.sub_text = QLabel("Supported formats: PDF, Word (DOCX), Plain Text (TXT) • Up to 50MB")
        self.sub_text.setStyleSheet("font-size: 12px; color: #94A3B8; background: transparent; border: none;")
        self.sub_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.sub_text)

        # Browse button
        self.browse_btn = QPushButton("Browse Files...")
        self.browse_btn.setObjectName("primaryBtn")
        self.browse_btn.setFixedWidth(150)
        self.browse_btn.clicked.connect(self._open_file_dialog)
        layout.addWidget(self.browse_btn, alignment=Qt.AlignCenter)

    def _open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Research Papers for Plagiarism Analysis",
            "",
            "Academic Documents (*.pdf *.docx *.doc *.txt);;PDF Documents (*.pdf);;Word Documents (*.docx);;Text Files (*.txt);;All Files (*.*)",
        )
        if files:
            self.files_selected.emit(files)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("""
                QFrame {
                    background-color: rgba(99, 102, 241, 0.15);
                    border: 2px dashed #818CF8;
                    border-radius: 12px;
                }
            """)
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._init_ui()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        valid_paths = []
        allowed_exts = {".pdf", ".docx", ".doc", ".txt", ".rtf", ".md"}

        for url in urls:
            local_path = url.toLocalFile()
            if local_path and Path(local_path).suffix.lower() in allowed_exts:
                valid_paths.append(local_path)

        self._init_ui()
        if valid_paths:
            self.files_selected.emit(valid_paths)
