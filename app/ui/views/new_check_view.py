"""New plagiarism check document queue and configuration view."""

import os
from pathlib import Path
from typing import Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from app.core.engine import ComparisonSource
from app.core.extractor import DocumentExtractor
from app.database.models import Document, Source
from app.database.session import get_all_documents, get_all_sources, get_db
from app.ui.widgets.file_drop import FileDropWidget
from app.ui.workers.analysis_worker import AnalysisWorker
from app.utils.logger import logger


class NewCheckView(QWidget):
    """View allowing users to queue multiple documents, set analysis parameters, and launch detection."""

    analysis_completed = Signal(object)  # Emits (DetectionResult, saved_document_id)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._queue: List[Dict] = []
        self._active_worker: Optional[AnalysisWorker] = None
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header
        header_box = QVBoxLayout()
        h_title = QLabel("New Plagiarism & Textual Similarity Audit")
        h_title.setStyleSheet("font-size: 22px; font-weight: 800; color: #FFFFFF;")
        h_sub = QLabel("Queue research papers, configure similarity parameters, and cross-examine academic corpora")
        h_sub.setStyleSheet("font-size: 13px; color: #94A3B8;")
        header_box.addWidget(h_title)
        header_box.addWidget(h_sub)
        main_layout.addLayout(header_box)

        # Input Tabs: File Upload vs Direct Text Paste
        self.tabs = QTabWidget()

        # Tab 1: File Upload
        tab_files = QWidget()
        files_layout = QVBoxLayout(tab_files)
        self.drop_widget = FileDropWidget()
        self.drop_widget.files_selected.connect(self._add_files_to_queue)
        files_layout.addWidget(self.drop_widget)
        self.tabs.addTab(tab_files, "📁 Document Files (PDF, DOCX, TXT)")

        # Tab 2: Manual Text Paste
        tab_text = QWidget()
        text_layout = QVBoxLayout(tab_text)
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Paste raw academic text, abstract, or draft paper sections here...")
        text_layout.addWidget(self.text_input)

        add_text_btn = QPushButton("+ Add Pasted Text to Analysis Queue")
        add_text_btn.setObjectName("primaryBtn")
        add_text_btn.clicked.connect(self._add_pasted_text_to_queue)
        text_layout.addWidget(add_text_btn, alignment=Qt.AlignRight)
        self.tabs.addTab(tab_text, "📝 Direct Text Paste")

        main_layout.addWidget(self.tabs)

        # Queue Table Section
        queue_card = QFrame()
        queue_card.setObjectName("card")
        q_box = QVBoxLayout(queue_card)

        q_hdr = QHBoxLayout()
        q_title = QLabel("Document Queue")
        q_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #FFFFFF;")
        q_hdr.addWidget(q_title)
        q_hdr.addStretch()

        self.clear_btn = QPushButton("Clear Queue")
        self.clear_btn.clicked.connect(self._clear_queue)
        q_hdr.addWidget(self.clear_btn)
        q_box.addLayout(q_hdr)

        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(6)
        self.queue_table.setHorizontalHeaderLabels([
            "Filename", "Size", "Pages", "Words", "Status", "Action"
        ])
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for c in range(1, 6):
            self.queue_table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.queue_table.verticalHeader().setVisible(False)
        self.queue_table.setMinimumHeight(120)
        q_box.addWidget(self.queue_table)

        main_layout.addWidget(queue_card)

        # Analysis Configuration Settings
        config_card = QFrame()
        config_card.setObjectName("card")
        c_layout = QHBoxLayout(config_card)
        c_layout.setSpacing(20)

        # Comparison Sources
        src_box = QVBoxLayout()
        src_box.addWidget(QLabel("COMPARISON CORPORA:"))
        self.chk_local_lib = QCheckBox("Local Source Library (Journals & Books)")
        self.chk_local_lib.setChecked(True)
        self.chk_past_docs = QCheckBox("Previously Analyzed Submissions")
        self.chk_past_docs.setChecked(True)
        self.chk_web = QCheckBox("Scholarly Web APIs (Crossref/arXiv) [Opt-in]")
        self.chk_web.setChecked(False)
        src_box.addWidget(self.chk_local_lib)
        src_box.addWidget(self.chk_past_docs)
        src_box.addWidget(self.chk_web)
        c_layout.addLayout(src_box)

        # Language & Exclusions
        lang_box = QVBoxLayout()
        lang_box.addWidget(QLabel("LANGUAGE & EXCLUSIONS:"))
        h_lang = QHBoxLayout()
        h_lang.addWidget(QLabel("Language:"))
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Auto-Detect", "English", "Hindi", "Marathi"])
        h_lang.addWidget(self.combo_lang)
        lang_box.addLayout(h_lang)

        self.chk_ex_quotes = QCheckBox("Exclude Quoted Text")
        self.chk_ex_quotes.setChecked(True)
        self.chk_ex_refs = QCheckBox("Exclude References / Bibliography")
        self.chk_ex_refs.setChecked(True)
        lang_box.addWidget(self.chk_ex_quotes)
        lang_box.addWidget(self.chk_ex_refs)
        c_layout.addLayout(lang_box)

        # Depth Slider
        depth_box = QVBoxLayout()
        depth_box.addWidget(QLabel("ANALYSIS DEPTH:"))
        self.depth_label = QLabel("Balanced (Exact + Fuzzy + Semantic)")
        self.depth_label.setStyleSheet("color: #818CF8; font-weight: 600;")
        depth_box.addWidget(self.depth_label)

        self.depth_slider = QSlider(Qt.Horizontal)
        self.depth_slider.setRange(1, 3)
        self.depth_slider.setValue(2)
        self.depth_slider.valueChanged.connect(self._on_depth_changed)
        depth_box.addWidget(self.depth_slider)
        c_layout.addLayout(depth_box)

        main_layout.addWidget(config_card)

        # Progress and Action Controls
        action_layout = QVBoxLayout()
        self.status_lbl = QLabel("Ready to analyze queued documents.")
        self.status_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")
        action_layout.addWidget(self.status_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        action_layout.addWidget(self.progress_bar)

        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_analysis)
        btn_row.addWidget(self.cancel_btn)

        self.analyze_btn = QPushButton("Analyze Document")
        self.analyze_btn.setObjectName("primaryBtn")
        self.analyze_btn.setMinimumHeight(42)
        self.analyze_btn.setMinimumWidth(180)
        self.analyze_btn.clicked.connect(self._start_analysis)
        btn_row.addWidget(self.analyze_btn)

        action_layout.addLayout(btn_row)
        main_layout.addLayout(action_layout)

    def _on_depth_changed(self, val: int):
        if val == 1:
            self.depth_label.setText("Fast (Exact Hash + RapidFuzz)")
        elif val == 2:
            self.depth_label.setText("Balanced (Exact + Fuzzy + Semantic)")
        else:
            self.depth_label.setText("Deep (Multi-pass N-gram + Neural Embeddings)")

    def _add_files_to_queue(self, filepaths: List[str]):
        """Inspects files and adds them to queue."""
        extractor = DocumentExtractor()
        for fp in filepaths:
            try:
                # Pre-scan basic metrics
                extracted = extractor.extract(fp)
                size_kb = round(os.path.getsize(fp) / 1024, 1)
                self._queue.append({
                    "filepath": fp,
                    "filename": extracted.filename,
                    "size": f"{size_kb} KB",
                    "pages": extracted.page_count,
                    "words": extracted.word_count,
                    "status": "Ready",
                    "extracted": extracted,
                })
            except Exception as e:
                logger.error(f"Failed to inspect file {fp}: {e}")
        self._refresh_queue_table()

    def _add_pasted_text_to_queue(self):
        raw = self.text_input.toPlainText().strip()
        if not raw:
            return

        # Save to temporary scratch text file
        from app.config import CACHE_DIR
        scratch_file = CACHE_DIR / f"pasted_text_{len(self._queue) + 1}.txt"
        with open(scratch_file, "w", encoding="utf-8") as f:
            f.write(raw)

        self._add_files_to_queue([str(scratch_file)])
        self.text_input.clear()
        self.tabs.setCurrentIndex(0)

    def _refresh_queue_table(self):
        self.queue_table.setRowCount(len(self._queue))
        for idx, item in enumerate(self._queue):
            self.queue_table.setItem(idx, 0, QTableWidgetItem(item["filename"]))
            self.queue_table.setItem(idx, 1, QTableWidgetItem(item["size"]))
            self.queue_table.setItem(idx, 2, QTableWidgetItem(str(item["pages"])))
            self.queue_table.setItem(idx, 3, QTableWidgetItem(f"{item['words']:,}"))
            self.queue_table.setItem(idx, 4, QTableWidgetItem(item["status"]))

            rm_btn = QPushButton("Remove")
            rm_btn.setFixedHeight(24)
            rm_btn.clicked.connect(lambda chk=False, row=idx: self._remove_from_queue(row))
            self.queue_table.setCellWidget(idx, 5, rm_btn)

    def _remove_from_queue(self, row: int):
        if 0 <= row < len(self._queue):
            self._queue.pop(row)
            self._refresh_queue_table()

    def _clear_queue(self):
        self._queue.clear()
        self._refresh_queue_table()

    def _build_comparison_sources(self) -> List[ComparisonSource]:
        """Loads comparison sources from database and past documents."""
        sources: List[ComparisonSource] = []

        # 1. Local Source Library
        if self.chk_local_lib.isChecked():
            db_sources = get_all_sources()
            for s in db_sources:
                text = s.text_content or ""
                lines = [line.strip() for line in text.split("\n") if len(line.strip().split()) >= 4]
                sources.append(ComparisonSource(
                    source_id=s.id,
                    name=s.title,
                    text=text,
                    sentences=lines,
                    author=s.author or "Unknown",
                    year=s.publication_year,
                    url=s.url,
                    doi=s.doi,
                    source_type=s.source_type or "Journal",
                ))

        # 2. Previously Analyzed Documents
        if self.chk_past_docs.isChecked():
            past_docs = get_all_documents(limit=50)
            for d in past_docs:
                text = d.extracted_text or ""
                lines = [line.strip() for line in text.split("\n") if len(line.strip().split()) >= 4]
                sources.append(ComparisonSource(
                    source_id=None,
                    name=f"Previous Submission: {d.filename}",
                    text=text,
                    sentences=lines,
                    author="Internal Repository",
                    source_type="Past Paper",
                ))

        return sources

    def _start_analysis(self):
        if not self._queue:
            self.status_lbl.setText("Please add at least one document to the queue.")
            return

        target_item = self._queue[0]
        target_item["status"] = "Analyzing..."
        self._refresh_queue_table()

        self.analyze_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # Build comparison sources
        comp_sources = self._build_comparison_sources()

        # Build settings overrides
        custom_settings = {
            "exclude_quotes": self.chk_ex_quotes.isChecked(),
            "exclude_references": self.chk_ex_refs.isChecked(),
        }

        # Launch background worker
        self._active_worker = AnalysisWorker(
            filepath=target_item["filepath"],
            comparison_sources=comp_sources,
            settings=custom_settings,
        )
        self._active_worker.progress_changed.connect(self._on_worker_progress)
        self._active_worker.analysis_finished.connect(self._on_worker_finished)
        self._active_worker.analysis_failed.connect(self._on_worker_failed)
        self._active_worker.start()

    def _cancel_analysis(self):
        if self._active_worker:
            self._active_worker.cancel()
            self.status_lbl.setText("Cancelling analysis...")

    def _on_worker_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.status_lbl.setText(msg)

    def _on_worker_finished(self, result):
        self.status_lbl.setText("Analysis successfully completed.")
        self.progress_bar.setValue(100)
        self.analyze_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)

        # Save to database
        doc_id = self._save_results_to_database(result)

        if self._queue:
            self._queue[0]["status"] = "Completed ✓"
            self._refresh_queue_table()

        # Emit completion signal
        self.analysis_completed.emit((result, doc_id))

    def _on_worker_failed(self, err_msg: str):
        self.status_lbl.setText(f"Analysis failed: {err_msg}")
        self.analyze_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        if self._queue:
            self._queue[0]["status"] = "Error ❌"
            self._refresh_queue_table()

    def _save_results_to_database(self, result) -> int:
        """Persists Document and Match records to SQLite."""
        import json
        from app.database.models import Document, Match

        with get_db() as session:
            doc = Document(
                filename=result.document_filename,
                filepath="",
                hash=result.file_hash,
                word_count=result.word_count,
                page_count=result.page_count,
                language=result.language,
                status="Completed",
                overall_similarity=result.score_breakdown.overall_similarity,
                risk_level=result.score_breakdown.risk_level,
                exact_matches_count=result.score_breakdown.exact_count,
                fuzzy_matches_count=result.score_breakdown.fuzzy_count,
                semantic_matches_count=result.score_breakdown.semantic_count,
                quoted_matches_count=result.score_breakdown.quoted_count,
                ai_likelihood=getattr(result.ai_writing, "likelihood", "Low"),
                extracted_text=result.extracted_text,
                structure_json=json.dumps({
                    k: {"detected": v.detected, "start_char": v.start_char, "end_char": v.end_char}
                    for k, v in result.structure.items()
                }),
            )
            session.add(doc)
            session.flush()

            # Add matches
            for m in result.matches:
                match_rec = Match(
                    document_id=doc.id,
                    sentence=m.get("sentence", ""),
                    matched_text=m.get("matched_text", ""),
                    similarity_score=m.get("similarity_score", 0.0),
                    algorithm=m.get("algorithm", "Fuzzy"),
                    page_number=m.get("page_number", 1),
                    start_char=m.get("start_char", 0),
                    end_char=m.get("end_char", 0),
                    is_quoted=m.get("is_quoted", False),
                    is_cited=m.get("is_cited", False),
                    is_ignored=m.get("is_ignored", False),
                    source_name=m.get("source_name", "Unknown Source"),
                )
                session.add(match_rec)

            session.commit()
            return doc.id
