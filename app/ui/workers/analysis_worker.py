"""Background worker thread for asynchronous plagiarism analysis.
Ensures the UI never freezes during heavy PDF extraction, NLP preprocessing, and vector matching.
"""

from typing import Dict, List, Optional
from PySide6.QtCore import QThread, Signal
from app.core.engine import ComparisonSource, DetectionResult, PlagiarismDetectionEngine
from app.core.extractor import DocumentExtractor, ExtractedDocument
from app.utils.logger import logger


class AnalysisWorker(QThread):
    """Executes document extraction and plagiarism detection in a non-blocking background thread."""

    progress_changed = Signal(int, str)  # percent (0-100), status_message
    analysis_finished = Signal(object)    # DetectionResult
    analysis_failed = Signal(str)         # error message

    def __init__(
        self,
        filepath: str,
        comparison_sources: List[ComparisonSource],
        settings: Optional[Dict] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.filepath = filepath
        self.comparison_sources = comparison_sources
        self.settings = settings
        self._is_cancelled = False

    def cancel(self):
        """Requests early cancellation of the background analysis."""
        self._is_cancelled = True

    def run(self):
        try:
            logger.info(f"Analysis worker started for: {self.filepath}")
            self.progress_changed.emit(2, "Opening document and validating file structure...")

            # 1. Extract document text
            extractor = DocumentExtractor()
            extracted = extractor.extract(self.filepath)

            if self._is_cancelled:
                return

            self.progress_changed.emit(10, f"Extracted {extracted.word_count:,} words across {extracted.page_count} page(s)...")

            # 2. Run detection engine
            engine = PlagiarismDetectionEngine(settings=self.settings)

            def on_progress(pct: int, msg: str):
                self.progress_changed.emit(pct, msg)

            def check_cancelled() -> bool:
                return self._is_cancelled

            result = engine.analyze_document(
                extracted=extracted,
                comparison_sources=self.comparison_sources,
                progress_callback=on_progress,
                cancel_check=check_cancelled,
            )

            if not self._is_cancelled:
                self.analysis_finished.emit(result)

        except InterruptedError:
            logger.info("Analysis was cancelled by the user.")
        except Exception as e:
            logger.error(f"Analysis failed with exception: {e}", exc_info=True)
            self.analysis_failed.emit(str(e))
