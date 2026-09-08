"""Interactive highlighted text viewer for inspected research papers.
Colors matches by algorithm type (Exact, Fuzzy, Semantic, Quoted) and supports click-to-inspect.
"""

from typing import Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout


class HighlightEditorWidget(QFrame):
    """Rich text viewer that renders document text with interactive color-coded plagiarism highlights."""

    match_selected = Signal(dict)  # Emitted when user clicks on a matched span

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._matches: List[Dict] = []
        self._raw_text: str = ""
        self._active_filter: str = "All"
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Top Filter Toolbar
        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(6)

        lbl = QLabel("Filter Highlights:")
        lbl.setStyleSheet("color: #64748B; font-weight: 700; font-size: 11px;")
        filter_bar.addWidget(lbl)

        self.filter_buttons = {}
        filters = ["All", "Exact", "Fuzzy", "Semantic", "Quoted"]
        for f in filters:
            btn = QPushButton(f)
            btn.setObjectName("filterBtn")
            btn.setCheckable(True)
            btn.setFixedHeight(26)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, name=f: self._set_filter(name))
            self.filter_buttons[f] = btn
            filter_bar.addWidget(btn)

        self.filter_buttons["All"].setChecked(True)
        filter_bar.addStretch()

        layout.addLayout(filter_bar)

        # Document Text Display
        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("highlightEditorText")
        self.text_edit.setReadOnly(True)
        self.text_edit.cursorPositionChanged.connect(self._on_cursor_changed)
        layout.addWidget(self.text_edit)

    def load_document(self, text: str, matches: List[Dict]):
        """Populates text and applies highlighting based on matches."""
        self._raw_text = text
        self._matches = matches
        self._render_highlights()

    def _set_filter(self, filter_name: str):
        self._active_filter = filter_name
        for name, btn in self.filter_buttons.items():
            btn.setChecked(name == filter_name)
        self._render_highlights()

    def _render_highlights(self):
        """Renders plain text and overlays background highlight spans."""
        self.text_edit.clear()
        self.text_edit.setPlainText(self._raw_text)

        cursor = self.text_edit.textCursor()

        for m in self._matches:
            if m.get("is_ignored", False):
                continue

            algo = m.get("algorithm", "").lower()
            is_quoted = m.get("is_quoted", False)

            # Check filter
            if self._active_filter == "Exact" and "exact" not in algo:
                continue
            if self._active_filter == "Fuzzy" and "fuzzy" not in algo:
                continue
            if self._active_filter == "Semantic" and "semantic" not in algo:
                continue
            if self._active_filter == "Quoted" and not is_quoted:
                continue

            # Color formatting
            fmt = QTextCharFormat()
            if is_quoted:
                fmt.setBackground(QColor(2, 132, 199, 80))  # Semi-transparent Blue
                fmt.setUnderlineColor(QColor("#0284C7"))
                fmt.setUnderlineStyle(QTextCharFormat.DashUnderline)
            elif "exact" in algo:
                fmt.setBackground(QColor(239, 68, 68, 95))  # Semi-transparent Red
                fmt.setUnderlineColor(QColor("#EF4444"))
                fmt.setUnderlineStyle(QTextCharFormat.SingleUnderline)
            elif "semantic" in algo:
                fmt.setBackground(QColor(139, 92, 246, 85))  # Semi-transparent Purple
                fmt.setUnderlineColor(QColor("#8B5CF6"))
                fmt.setUnderlineStyle(QTextCharFormat.DotLine)
            else:  # Fuzzy
                fmt.setBackground(QColor(245, 158, 11, 85))  # Semi-transparent Amber
                fmt.setUnderlineColor(QColor("#F59E0B"))
                fmt.setUnderlineStyle(QTextCharFormat.SingleUnderline)

            # Apply span formatting
            start = m.get("start_char", 0)
            end = m.get("end_char", start + len(m.get("sentence", "")))

            cursor.setPosition(min(start, len(self._raw_text)))
            cursor.setPosition(min(end, len(self._raw_text)), QTextCursor.KeepAnchor)
            cursor.mergeCharFormat(fmt)

    def _on_cursor_changed(self):
        """Detects if user clicked inside a matched segment."""
        pos = self.text_edit.textCursor().position()
        for m in self._matches:
            start = m.get("start_char", 0)
            end = m.get("end_char", start + len(m.get("sentence", "")))
            if start <= pos <= end:
                self.match_selected.emit(m)
                break

    def highlight_specific_match(self, match_data: Dict):
        """Scrolls to and focuses the cursor on the requested match."""
        start = match_data.get("start_char", 0)
        cursor = self.text_edit.textCursor()
        cursor.setPosition(min(start, len(self._raw_text)))
        self.text_edit.setTextCursor(cursor)
        self.text_edit.ensureCursorVisible()
