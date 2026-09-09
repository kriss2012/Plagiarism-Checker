"""Split-screen interactive match inspector view.
Displays original paper text with color-coded highlights alongside source comparison details.
"""

from typing import Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from app.ui.widgets.cards import RiskBadge
from app.ui.widgets.highlight_editor import HighlightEditorWidget


class MatchViewerView(QWidget):
    """Side-by-side inspection view for detailed comparison between analyzed paper and matched sources."""

    back_to_results = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._matches: List[Dict] = []
        self._current_index: int = 0
        self._data: Optional[Dict] = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # Top Header Bar
        top_bar = QHBoxLayout()
        self.back_btn = QPushButton("◄ Back to Summary")
        self.back_btn.setFixedHeight(34)
        self.back_btn.setToolTip("Return to the similarity results and certificate summary")
        self.back_btn.setAccessibleName("Back to similarity summary")
        self.back_btn.clicked.connect(self.back_to_results.emit)
        top_bar.addWidget(self.back_btn)

        self.title_lbl = QLabel("Interactive Match Inspector")
        self.title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #002461;")
        top_bar.addWidget(self.title_lbl)
        top_bar.addStretch()

        self.match_counter_lbl = QLabel("Match 0 of 0")
        self.match_counter_lbl.setStyleSheet("color: #475569; font-weight: 600;")
        top_bar.addWidget(self.match_counter_lbl)

        self.prev_btn = QPushButton("◄ Previous")
        self.prev_btn.setFixedHeight(34)
        self.prev_btn.setToolTip("Go to the previous match")
        self.prev_btn.setAccessibleName("Previous match")
        self.prev_btn.clicked.connect(self._prev_match)
        top_bar.addWidget(self.prev_btn)

        self.next_btn = QPushButton("Next ►")
        self.next_btn.setFixedHeight(34)
        self.next_btn.setToolTip("Go to the next match")
        self.next_btn.setAccessibleName("Next match")
        self.next_btn.clicked.connect(self._next_match)
        top_bar.addWidget(self.next_btn)

        main_layout.addLayout(top_bar)

        # Splitter: Left (Original Paper) vs Right (Source Inspector)
        splitter = QSplitter(Qt.Horizontal)

        # Left Panel: Original Document Text
        left_container = QWidget()
        l_box = QVBoxLayout(left_container)
        l_box.setContentsMargins(0, 0, 0, 0)
        l_lbl = QLabel("ORIGINAL STUDENT DISSERTATION (HIGHLIGHTED)")
        l_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #002461;")
        l_box.addWidget(l_lbl)

        self.highlight_editor = HighlightEditorWidget()
        self.highlight_editor.match_selected.connect(self._on_span_clicked)
        l_box.addWidget(self.highlight_editor)
        splitter.addWidget(left_container)

        # Right Panel: Source Details Card
        right_container = QWidget()
        r_box = QVBoxLayout(right_container)
        r_box.setContentsMargins(0, 0, 0, 0)
        r_lbl = QLabel("MATCHED COMPARISON REPOSITORY SOURCE")
        r_lbl.setStyleSheet("font-size: 11px; font-weight: 700; color: #002461;")
        r_box.addWidget(r_lbl)

        self.inspector_card = QFrame()
        self.inspector_card.setObjectName("card")
        ins_layout = QVBoxLayout(self.inspector_card)
        ins_layout.setSpacing(10)

        # Top Inspector Header
        ins_hdr = QHBoxLayout()
        self.ins_id_lbl = QLabel("MATCH #--")
        self.ins_id_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #005FEA;")
        ins_hdr.addWidget(self.ins_id_lbl)
        ins_hdr.addStretch()

        self.ins_sim_lbl = QLabel("Similarity: --%")
        self.ins_sim_lbl.setStyleSheet("font-size: 15px; font-weight: 700; color: #DC2626;")
        ins_hdr.addWidget(self.ins_sim_lbl)
        ins_layout.addLayout(ins_hdr)

        self.ins_algo_lbl = QLabel("Algorithm: -")
        self.ins_algo_lbl.setStyleSheet("color: #475569; font-size: 12px;")
        ins_layout.addWidget(self.ins_algo_lbl)

        self.ins_page_lbl = QLabel("Page: -")
        self.ins_page_lbl.setStyleSheet("color: #475569; font-size: 12px;")
        ins_layout.addWidget(self.ins_page_lbl)

        # Source Title / Origin
        ins_layout.addWidget(QLabel("Matched Source:"))
        self.ins_source_title = QLabel("Source Name")
        self.ins_source_title.setStyleSheet("color: #002461; font-weight: 700; font-size: 14px;")
        self.ins_source_title.setWordWrap(True)
        ins_layout.addWidget(self.ins_source_title)

        # Source Matched Text Excerpt
        ins_layout.addWidget(QLabel("Source Excerpt:"))
        self.ins_source_text = QTextEdit()
        self.ins_source_text.setReadOnly(True)
        self.ins_source_text.setObjectName("matchSourceText")
        self.ins_source_text.setMaximumHeight(150)
        ins_layout.addWidget(self.ins_source_text)

        # Action Buttons
        ins_btn_row = QHBoxLayout()
        self.ignore_btn = QPushButton("Ignore Match")
        self.ignore_btn.setFixedHeight(34)
        self.ignore_btn.setCursor(Qt.PointingHandCursor)
        self.ignore_btn.clicked.connect(self._toggle_ignore_match)
        ins_btn_row.addWidget(self.ignore_btn)

        self.copy_btn = QPushButton("Copy Excerpt")
        self.copy_btn.setFixedHeight(34)
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.clicked.connect(self._copy_excerpt)
        ins_btn_row.addWidget(self.copy_btn)

        ins_layout.addLayout(ins_btn_row)
        ins_layout.addStretch()

        r_box.addWidget(self.inspector_card)
        splitter.addWidget(right_container)

        # Initial ratio: 60% left, 40% right
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

    def load_data(self, data: Dict):
        """Loads document text and match items."""
        self._data = data
        self._matches = data.get("matches", [])
        self._current_index = 0

        self.highlight_editor.load_document(
            text=data.get("extracted_text", ""),
            matches=self._matches,
        )
        self._update_inspector()

    def _update_inspector(self):
        """Refreshes the right inspector panel for the current match index."""
        if not self._matches:
            self.ins_id_lbl.setText("NO MATCHES")
            self.ins_sim_lbl.setText("0%")
            self.ins_source_title.setText("No matches detected in document.")
            self.ins_source_text.clear()
            self.match_counter_lbl.setText("0 of 0")
            return

        idx = self._current_index
        m = self._matches[idx]

        self.match_counter_lbl.setText(f"Match {idx + 1} of {len(self._matches)}")
        self.ins_id_lbl.setText(f"MATCH #{idx + 1}")
        sim_val = m.get("similarity_score", 0.0)
        self.ins_sim_lbl.setText(f"{sim_val:.0f}% Similarity")

        algo = m.get("algorithm", "Fuzzy Match")
        self.ins_algo_lbl.setText(f"Detection Method: {algo}")
        self.ins_page_lbl.setText(f"Page Number: {m.get('page_number', 1)}")
        self.ins_source_title.setText(m.get("source_name", "Comparison Source"))
        self.ins_source_text.setPlainText(m.get("matched_text", ""))

        is_ignored = m.get("is_ignored", False)
        self.ignore_btn.setText("Restore Match" if is_ignored else "Ignore Match")

        # Focus in highlight editor
        self.highlight_editor.highlight_specific_match(m)

    def _prev_match(self):
        if self._matches and self._current_index > 0:
            self._current_index -= 1
            self._update_inspector()

    def _next_match(self):
        if self._matches and self._current_index < len(self._matches) - 1:
            self._current_index += 1
            self._update_inspector()

    def _on_span_clicked(self, match_dict: Dict):
        """Triggered when user clicks a highlighted text span in the left editor."""
        for idx, m in enumerate(self._matches):
            if m.get("start_char") == match_dict.get("start_char"):
                self._current_index = idx
                self._update_inspector()
                break

    def _toggle_ignore_match(self):
        if self._matches:
            cur = self._matches[self._current_index]
            cur["is_ignored"] = not cur.get("is_ignored", False)
            self._update_inspector()
            self.highlight_editor.load_document(self._data.get("extracted_text", ""), self._matches)

    def _copy_excerpt(self):
        if self._matches:
            cur = self._matches[self._current_index]
            text = f"Document: \"{cur.get('sentence', '')}\"\n\nMatched Source ({cur.get('source_name', '')}): \"{cur.get('matched_text', '')}\""
            QGuiApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copied", "Match text copied to clipboard.")
