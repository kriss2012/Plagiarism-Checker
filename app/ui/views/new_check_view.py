"""Librarian Student Paper Intake and Plagiarism Verification View.
Tailored for Central Library verification officers at SES's R. C. Patel IMRD Shirpur.
Captures student credentials, course, PRN, supervisor, dissertation title, and launches analysis.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from app.config import (
    CACHE_DIR,
    DEFAULT_SETTINGS,
    INSTITUTION_SHORT,
)
from app.core.engine import ComparisonSource
from app.core.extractor import DocumentExtractor
from app.database.models import Document, Source
from app.database.session import (
    generate_certificate_number,
    get_all_documents,
    get_all_sources,
    get_db,
)
from app.ui.widgets.file_drop import FileDropWidget
from app.ui.workers.analysis_worker import AnalysisWorker
from app.utils.logger import logger


class NewCheckView(QWidget):
    """View enabling the librarian to register student particulars and verify paper plagiarism."""

    analysis_completed = Signal(object)  # Emits (DetectionResult, saved_document_id)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._queue: List[Dict] = []
        self._active_worker: Optional[AnalysisWorker] = None
        self._init_ui()

    def _init_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(10)

        # 1. Header Banner
        header_box = QVBoxLayout()
        h_title = QLabel("Student Dissertation & Research Paper Verification Intake")
        h_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #002461;")
        h_sub = QLabel(
            f"Central Library • {INSTITUTION_SHORT} • Plagiarism Verification & UGC Compliance Clearance System"
        )
        h_sub.setStyleSheet("font-size: 12px; color: #64748B;")
        header_box.addWidget(h_title)
        header_box.addWidget(h_sub)
        layout.addLayout(header_box)

        # 2. Student Academic Credentials Form
        cred_card = QFrame()
        cred_card.setObjectName("card")
        cred_layout = QVBoxLayout(cred_card)
        cred_layout.setSpacing(10)

        cred_title = QLabel("STUDENT ACADEMIC PARTICULARS (FOR OFFICIAL CLEARANCE CERTIFICATE)")
        cred_title.setStyleSheet("color: #002461; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        cred_layout.addWidget(cred_title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)

        # Row 0: Student Name & PRN
        grid.addWidget(QLabel("Student Full Name:"), 0, 0)
        self.input_student_name = QLineEdit()
        self.input_student_name.setPlaceholderText("e.g. Patil Bhushan Dattatray")
        grid.addWidget(self.input_student_name, 0, 1)

        grid.addWidget(QLabel("PRN / Roll Number:"), 0, 2)
        self.input_prn = QLineEdit()
        self.input_prn.setPlaceholderText("e.g. 2024015400123456")
        grid.addWidget(self.input_prn, 0, 3)

        # Row 1: Course / Program & Academic Year / Sem
        grid.addWidget(QLabel("Program / Department:"), 1, 0)
        self.combo_course = QComboBox()
        self.combo_course.addItems([
            "MCA (Master of Computer Applications)",
            "MBA (Master of Business Administration)",
            "BCA (Bachelor of Computer Applications)",
            "BBA (Bachelor of Business Administration)",
            "Integrated MCA (5 Years)",
        ])
        grid.addWidget(self.combo_course, 1, 1)

        grid.addWidget(QLabel("Academic Year & Sem:"), 1, 2)
        self.combo_year_sem = QComboBox()
        self.combo_year_sem.addItems([
            "2025-2026 • Semester IV",
            "2025-2026 • Semester VI",
            "2025-2026 • Semester II",
            "2024-2025 • Semester IV",
        ])
        grid.addWidget(self.combo_year_sem, 1, 3)

        # Row 2: Research Guide & Paper Title
        grid.addWidget(QLabel("Research Guide / Supervisor:"), 2, 0)
        self.input_guide = QLineEdit()
        self.input_guide.setPlaceholderText("e.g. Dr. S. B. Patil / Prof. V. A. Pawar")
        grid.addWidget(self.input_guide, 2, 1)

        grid.addWidget(QLabel("Dissertation / Project Title:"), 2, 2)
        self.input_title = QLineEdit()
        self.input_title.setPlaceholderText("e.g. AI-Powered Medical Diagnosis Support System")
        grid.addWidget(self.input_title, 2, 3)

        cred_layout.addLayout(grid)
        layout.addWidget(cred_card)

        # 3. Document File Selection & Queue
        file_card = QFrame()
        file_card.setObjectName("card")
        f_layout = QVBoxLayout(file_card)
        f_layout.setSpacing(10)

        f_title = QLabel("DOCUMENT SUBMISSION FILE (PDF, DOCX, TXT)")
        f_title.setStyleSheet("color: #002461; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        f_layout.addWidget(f_title)

        self.tabs = QTabWidget()

        # Tab 1: File Drop / Browse
        tab_files = QWidget()
        tab_files_layout = QVBoxLayout(tab_files)
        self.drop_widget = FileDropWidget()
        self.drop_widget.files_selected.connect(self._add_files_to_queue)
        tab_files_layout.addWidget(self.drop_widget)
        self.tabs.addTab(tab_files, "Select Student Document (.PDF, .DOCX, .TXT)")

        # Tab 2: Manual Text Paste
        tab_text = QWidget()
        tab_text_layout = QVBoxLayout(tab_text)
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Paste raw dissertation text, chapter drafts, or literature review here...")
        tab_text_layout.addWidget(self.text_input)

        add_paste_btn = QPushButton("+ Queue Pasted Text")
        add_paste_btn.setObjectName("primaryBtn")
        add_paste_btn.clicked.connect(self._add_pasted_text_to_queue)
        tab_text_layout.addWidget(add_paste_btn, alignment=Qt.AlignRight)
        self.tabs.addTab(tab_text, "Direct Text Paste")

        f_layout.addWidget(self.tabs)

        # Queue Status Table
        self.queue_table = QTableWidget()
        self.queue_table.setColumnCount(6)
        self.queue_table.setHorizontalHeaderLabels([
            "File Name", "Size", "Pages", "Word Count", "Status", "Action"
        ])
        self.queue_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for c in range(1, 5):
            self.queue_table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeToContents)
        self.queue_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Fixed)
        self.queue_table.setColumnWidth(5, 115)
        self.queue_table.verticalHeader().setVisible(False)
        self.queue_table.verticalHeader().setDefaultSectionSize(40)
        self.queue_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.queue_table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.queue_table.setMinimumHeight(85)
        self.queue_table.setMaximumHeight(160)
        f_layout.addWidget(self.queue_table)

        layout.addWidget(file_card)

        # 4. Verification Parameters & UGC Compliance Options
        config_card = QFrame()
        config_card.setObjectName("card")
        c_layout = QHBoxLayout(config_card)
        c_layout.setSpacing(20)

        # UGC Exclusions
        excl_box = QVBoxLayout()
        excl_title = QLabel("UGC REGULATION 2018 EXCLUSIONS:")
        excl_title.setStyleSheet("font-weight: 700; font-size: 11px; color: #002461;")
        excl_box.addWidget(excl_title)

        self.chk_ex_refs = QCheckBox("Exclude References & Bibliography (UGC Sec 6.1)")
        self.chk_ex_refs.setChecked(True)
        self.chk_ex_quotes = QCheckBox("Exclude Quoted & Cited Passages (UGC Sec 6.1)")
        self.chk_ex_quotes.setChecked(True)
        self.chk_ex_phrases = QCheckBox("Filter Common Clichés & Formulae")
        self.chk_ex_phrases.setChecked(True)

        excl_box.addWidget(self.chk_ex_refs)
        excl_box.addWidget(self.chk_ex_quotes)
        excl_box.addWidget(self.chk_ex_phrases)
        c_layout.addLayout(excl_box, 1)

        # Comparison Corpora
        corp_box = QVBoxLayout()
        corp_title = QLabel("COMPARISON CORPORA:")
        corp_title.setStyleSheet("font-weight: 700; font-size: 11px; color: #002461;")
        corp_box.addWidget(corp_title)

        self.chk_local_lib = QCheckBox("Institutional Repository (Journals & Books)")
        self.chk_local_lib.setChecked(True)
        self.chk_past_docs = QCheckBox("Past Student Dissertations & Projects")
        self.chk_past_docs.setChecked(True)

        corp_box.addWidget(self.chk_local_lib)
        corp_box.addWidget(self.chk_past_docs)
        c_layout.addLayout(corp_box, 1)

        # Language Detection
        lang_box = QVBoxLayout()
        lang_title = QLabel("LANGUAGE & SENSITIVITY:")
        lang_title.setStyleSheet("font-weight: 700; font-size: 11px; color: #002461;")
        lang_box.addWidget(lang_title)

        h_lang = QHBoxLayout()
        h_lang.addWidget(QLabel("Language:"))
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["Auto-Detect", "English", "Hindi", "Marathi"])
        h_lang.addWidget(self.combo_lang)
        lang_box.addLayout(h_lang)

        self.depth_label = QLabel("Mode: Multi-pass Exact + Fuzzy + Semantic")
        self.depth_label.setStyleSheet("color: #005FEA; font-weight: 600; font-size: 11px;")
        lang_box.addWidget(self.depth_label)

        c_layout.addLayout(lang_box, 1)
        layout.addWidget(config_card)

        # 5. Verification Action Bar
        action_layout = QVBoxLayout()
        self.status_lbl = QLabel("Ready to verify student document against institutional repository.")
        self.status_lbl.setStyleSheet("color: #64748B; font-size: 12px; font-weight: 500;")
        action_layout.addWidget(self.status_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        action_layout.addWidget(self.progress_bar)

        btn_row = QHBoxLayout()
        self.clear_btn = QPushButton("Clear Form")
        self.clear_btn.setFixedHeight(34)
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self._clear_form)
        btn_row.addWidget(self.clear_btn)

        btn_row.addStretch()

        self.cancel_btn = QPushButton("Cancel Verification")
        self.cancel_btn.setObjectName("dangerBtn")
        self.cancel_btn.setFixedHeight(34)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setVisible(False)
        self.cancel_btn.clicked.connect(self._cancel_analysis)
        btn_row.addWidget(self.cancel_btn)

        self.analyze_btn = QPushButton("Verify Student Paper & Check UGC Compliance")
        self.analyze_btn.setObjectName("certBtn")
        self.analyze_btn.setFixedHeight(40)
        self.analyze_btn.setMinimumWidth(320)
        self.analyze_btn.setCursor(Qt.PointingHandCursor)
        self.analyze_btn.clicked.connect(self._start_analysis)
        btn_row.addWidget(self.analyze_btn)

        action_layout.addLayout(btn_row)
        layout.addLayout(action_layout)

        scroll.setWidget(container)
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll)

    def _add_files_to_queue(self, filepaths: List[str]):
        """Inspects selected file and queues it."""
        extractor = DocumentExtractor()
        for fp in filepaths:
            try:
                extracted = extractor.extract(fp)
                size_kb = round(os.path.getsize(fp) / 1024, 1)
                
                # Auto-fill title if empty
                if not self.input_title.text().strip():
                    self.input_title.setText(Path(fp).stem.replace("_", " ").title())

                self._queue.append({
                    "filepath": fp,
                    "filename": extracted.filename,
                    "size": f"{size_kb} KB",
                    "pages": extracted.page_count,
                    "words": extracted.word_count,
                    "status": "Ready for Verification",
                    "extracted": extracted,
                })
            except Exception as e:
                logger.error(f"Failed to extract document {fp}: {e}")
        self._refresh_queue_table()

    def _add_pasted_text_to_queue(self):
        raw = self.text_input.toPlainText().strip()
        if not raw:
            return

        scratch_file = CACHE_DIR / f"student_submission_{len(self._queue) + 1}.txt"
        with open(scratch_file, "w", encoding="utf-8") as f:
            f.write(raw)

        self._add_files_to_queue([str(scratch_file)])
        self.text_input.clear()
        self.tabs.setCurrentIndex(0)

    def _refresh_queue_table(self):
        self.queue_table.setRowCount(len(self._queue))
        for idx, item in enumerate(self._queue):
            self.queue_table.setRowHeight(idx, 38)
            self.queue_table.setItem(idx, 0, QTableWidgetItem(item["filename"]))
            self.queue_table.setItem(idx, 1, QTableWidgetItem(item["size"]))
            self.queue_table.setItem(idx, 2, QTableWidgetItem(str(item["pages"])))
            self.queue_table.setItem(idx, 3, QTableWidgetItem(f"{item['words']:,}"))
            self.queue_table.setItem(idx, 4, QTableWidgetItem(item["status"]))

            rm_btn = QPushButton("Remove")
            rm_btn.setObjectName("dangerBtn")
            rm_btn.setMinimumWidth(76)
            rm_btn.setFixedHeight(26)
            rm_btn.setCursor(Qt.PointingHandCursor)
            rm_btn.clicked.connect(lambda chk=False, row=idx: self._remove_from_queue(row))

            btn_box = QWidget()
            btn_box.setStyleSheet("background: transparent;")
            btn_layout = QHBoxLayout(btn_box)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setAlignment(Qt.AlignCenter)
            btn_layout.addWidget(rm_btn)
            self.queue_table.setCellWidget(idx, 5, btn_box)

    def _remove_from_queue(self, row: int):
        if 0 <= row < len(self._queue):
            self._queue.pop(row)
            self._refresh_queue_table()

    def _clear_form(self):
        self.input_student_name.clear()
        self.input_prn.clear()
        self.input_guide.clear()
        self.input_title.clear()
        self._queue.clear()
        self._refresh_queue_table()
        self.status_lbl.setText("Intake form cleared.")

    def _build_comparison_sources(self) -> List[ComparisonSource]:
        sources: List[ComparisonSource] = []

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

        if self.chk_past_docs.isChecked():
            past_docs = get_all_documents(limit=100)
            for d in past_docs:
                text = d.extracted_text or ""
                lines = [line.strip() for line in text.split("\n") if len(line.strip().split()) >= 4]
                sources.append(ComparisonSource(
                    source_id=None,
                    name=f"IMRD Archive: {d.student_name or d.filename} ({d.course_name or 'MCA'})",
                    text=text,
                    sentences=lines,
                    author=d.student_name or "IMRD Student",
                    source_type="Student Archive",
                ))

        return sources

    def _start_analysis(self):
        if not self._queue:
            self.status_lbl.setText("⚠ Please select or drop a student dissertation document first.")
            return

        target_item = self._queue[0]
        target_item["status"] = "Verifying..."
        self._refresh_queue_table()

        self.analyze_btn.setEnabled(False)
        self.cancel_btn.setVisible(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        comp_sources = self._build_comparison_sources()
        custom_settings = {
            "exclude_quotes": self.chk_ex_quotes.isChecked(),
            "exclude_references": self.chk_ex_refs.isChecked(),
            "filter_common_phrases": self.chk_ex_phrases.isChecked(),
        }

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
            self.status_lbl.setText("Cancelling verification...")

    def _on_worker_progress(self, pct: int, msg: str):
        self.progress_bar.setValue(pct)
        self.status_lbl.setText(f"Stage: {msg}")

    def _on_worker_finished(self, result):
        self.status_lbl.setText("Verification completed successfully. Generating clearance certificate...")
        self.progress_bar.setValue(100)
        self.analyze_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)

        # Attach student metadata to result object
        result.student_name = self.input_student_name.text().strip() or "Student Name"
        result.prn_number = self.input_prn.text().strip() or "-"
        course_sel = self.combo_course.currentText().split(" (")[0]
        result.course_name = course_sel
        year_sem_sel = self.combo_year_sem.currentText()
        parts = [p.strip() for p in year_sem_sel.split("•")]
        result.academic_year = parts[0] if len(parts) > 0 else "2025-2026"
        result.semester = parts[1] if len(parts) > 1 else "Semester IV"
        result.guide_name = self.input_guide.text().strip() or "Faculty Supervisor"
        result.paper_title = self.input_title.text().strip() or result.document_filename

        # Save to database and receive doc_id
        doc_id = self._save_results_to_database(result)
        result.certificate_no = generate_certificate_number()

        if self._queue:
            self._queue[0]["status"] = "Verified ✓"
            self._refresh_queue_table()

        self.analysis_completed.emit((result, doc_id))

    def _on_worker_failed(self, err_msg: str):
        self.status_lbl.setText(f"⚠ Verification failed: {err_msg}")
        self.analyze_btn.setEnabled(True)
        self.cancel_btn.setVisible(False)
        if self._queue:
            self._queue[0]["status"] = "Error ❌"
            self._refresh_queue_table()

    def _save_results_to_database(self, result) -> int:
        """Persists Document with student particulars and Match records to SQLite."""
        import json
        from app.database.models import Document, Match

        overall_sim = result.score_breakdown.overall_similarity
        if overall_sim <= 10.0:
            status = "Approved (Level 0)"
        elif overall_sim <= 40.0:
            status = "Revisions Required (Level 1)"
        elif overall_sim <= 60.0:
            status = "Major Revisions (Level 2)"
        else:
            status = "Rejected (Level 3)"

        cert_no = generate_certificate_number()

        with get_db() as session:
            doc = Document(
                filename=result.document_filename,
                filepath="",
                hash=result.file_hash,
                word_count=result.word_count,
                page_count=result.page_count,
                language=result.language,
                status="Completed",
                student_name=getattr(result, "student_name", "Student Name"),
                prn_number=getattr(result, "prn_number", "-"),
                course_name=getattr(result, "course_name", "MCA"),
                academic_year=getattr(result, "academic_year", "2025-2026"),
                semester=getattr(result, "semester", "Semester IV"),
                guide_name=getattr(result, "guide_name", "-"),
                paper_title=getattr(result, "paper_title", result.document_filename),
                clearance_status=status,
                certificate_no=cert_no,
                overall_similarity=overall_sim,
                risk_level=result.score_breakdown.risk_level,
                exact_matches_count=result.score_breakdown.exact_count,
                fuzzy_matches_count=result.score_breakdown.fuzzy_count,
                semantic_matches_count=result.score_breakdown.semantic_count,
                quoted_matches_count=result.score_breakdown.quoted_count,
                ai_likelihood=getattr(result.ai_writing, "likelihood", "Low"),
                direct_match_score=result.score_breakdown.direct_match_score,
                semantic_similarity_score=result.score_breakdown.semantic_similarity_score,
                citation_coverage_score=result.score_breakdown.citation_coverage_score,
                reference_verification_score=result.score_breakdown.reference_verification_score,
                high_risk_similarity=result.score_breakdown.high_risk_similarity,
                academic_verdict=result.score_breakdown.academic_verdict,
                references_count=len(getattr(result, "references", [])),
                verified_references_count=sum(1 for r in getattr(result, "references", []) if r.status in ["VERIFIED", "PARTIALLY VERIFIED"]),
                citation_issues_count=len(getattr(result.citations, "citation_issues", [])),
                extracted_text=result.extracted_text,
                structure_json=json.dumps({
                    k: {"detected": v.detected, "start_char": v.start_char, "end_char": v.end_char}
                    for k, v in result.structure.items()
                }),
            )
            session.add(doc)
            session.flush()

            # Save Matches with full verification attributes
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
                    confidence=m.get("confidence", "High"),
                    match_category=m.get("match_category", "Copied + No Citation"),
                    source_url=m.get("source_url"),
                    source_domain=m.get("source_domain", ""),
                    source_type=m.get("source_type", "Journal"),
                    source_reliability=m.get("source_reliability", "High"),
                    review_decision=m.get("review_decision", "Pending Review"),
                    review_notes=m.get("review_notes", ""),
                )
                session.add(match_rec)

            # Save References
            from app.database.models import CitationIssue, Reference
            for r in getattr(result, "references", []):
                ref_rec = Reference(
                    document_id=doc.id,
                    ref_number=r.ref_number,
                    raw_text=r.raw_text,
                    title=r.title,
                    authors=r.authors,
                    journal=r.journal,
                    year=r.year,
                    volume=r.volume,
                    issue=r.issue,
                    pages=r.pages,
                    doi=r.doi,
                    url=r.url,
                    publisher=r.publisher,
                    status=r.status,
                    verification_source=r.verification_source,
                    matched_metadata_json=json.dumps(r.matched_metadata) if r.matched_metadata else None,
                    difference_notes=r.difference_notes,
                    is_duplicate=r.is_duplicate,
                )
                session.add(ref_rec)

            # Save Citation Issues
            for ci in getattr(result.citations, "citation_issues", []):
                ci_rec = CitationIssue(
                    document_id=doc.id,
                    issue_type=ci.issue_type,
                    citation_text=ci.citation_text,
                    page_number=ci.page_number,
                    details=ci.details,
                    ref_number=ci.ref_number,
                )
                session.add(ci_rec)

            session.commit()
            return doc.id
