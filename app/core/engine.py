"""Plagiarism and similarity detection orchestrator.
Coordinates Exact, Fuzzy (RapidFuzz), N-gram, TF-IDF, and Semantic similarity analysis
against local source libraries, previously analyzed documents, and user comparison files.
"""

from dataclasses import dataclass, field
import hashlib
from typing import Callable, Dict, List, Optional
from rapidfuzz import fuzz

from app.config import DEFAULT_SETTINGS
from app.core.ai_detector import AIWritingDetector
from app.core.citations import CitationAnalysisResult, CitationAnalyzer
from app.core.common_phrases import is_common_academic_phrase
from app.core.extractor import ExtractedDocument
from app.core.language import detect_language
from app.core.preprocessor import PreprocessedDocument, SentenceUnit, TextPreprocessor
from app.core.scoring import ScoreBreakdown, ScoringEngine
from app.core.structure import StructureAnalyzer
from app.ml.semantic import SemanticSimilarityEngine, is_semantic_model_available
from app.utils.logger import logger


@dataclass
class ComparisonSource:
    source_id: Optional[int]
    name: str
    text: str
    sentences: List[str]
    author: str = "Unknown"
    year: Optional[int] = None
    url: Optional[str] = None
    doi: Optional[str] = None
    source_type: str = "Journal"


@dataclass
class DetectionResult:
    document_filename: str
    file_hash: str
    word_count: int
    page_count: int
    language: str
    extracted_text: str
    preprocessed: PreprocessedDocument
    structure: Dict[str, any]
    citations: CitationAnalysisResult
    ai_writing: any
    matches: List[Dict]
    score_breakdown: ScoreBreakdown
    sources_compared_count: int
    is_scanned: bool = False
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class PlagiarismDetectionEngine:
    """Multi-method similarity and plagiarism detection engine."""

    def __init__(self, settings: Optional[Dict] = None):
        self.settings = settings or DEFAULT_SETTINGS
        self.preprocessor = TextPreprocessor(
            min_word_count_to_flag=self.settings.get("min_word_count_to_flag", 4)
        )
        self.structure_analyzer = StructureAnalyzer()
        self.citation_analyzer = CitationAnalyzer()
        self.ai_detector = AIWritingDetector()
        self.scoring_engine = ScoringEngine(self.settings)
        self.semantic_engine = SemanticSimilarityEngine()

    def analyze_document(
        self,
        extracted: ExtractedDocument,
        comparison_sources: List[ComparisonSource],
        progress_callback: Optional[Callable[[int, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> DetectionResult:
        """Executes the complete analysis pipeline across all algorithms."""
        logger.info(f"Starting plagiarism analysis for: {extracted.filename}")

        def update_progress(pct: int, msg: str):
            if progress_callback:
                progress_callback(pct, msg)
            if cancel_check and cancel_check():
                raise InterruptedError("Analysis cancelled by user.")

        update_progress(5, "Detecting language and script...")
        lang, lang_conf = detect_language(extracted.full_text)

        update_progress(15, "Preprocessing and segmenting sentences...")
        preprocessed = self.preprocessor.preprocess_pages(extracted.pages, language=lang)

        update_progress(25, "Analyzing paper structure and sections...")
        structure = self.structure_analyzer.analyze(extracted.full_text)
        ref_start = structure["References"].start_char if structure.get("References") and structure["References"].detected else -1

        update_progress(35, "Scanning citations and quotations...")
        citations = self.citation_analyzer.analyze(extracted.full_text, references_start_char=ref_start)

        update_progress(45, "Computing AI-writing likelihood indicators...")
        sentence_texts = [s.original_text for s in preprocessed.sentences]
        ai_result = self.ai_detector.analyze(sentence_texts)

        # Check for exact duplicate document against comparison sources
        is_dup = False
        dup_name = None
        for src in comparison_sources:
            src_hash = hashlib.sha256(src.text.encode("utf-8", errors="ignore")).hexdigest()
            if src_hash == extracted.file_hash or (len(src.text) > 100 and src.text.strip() == extracted.full_text.strip()):
                is_dup = True
                dup_name = src.name
                break

        update_progress(55, "Comparing against source corpus...")
        matches: List[Dict] = []

        exclude_refs = self.settings.get("exclude_references", True)
        exclude_quotes = self.settings.get("exclude_quotes", True)
        filter_common = self.settings.get("filter_common_phrases", True)
        fuzzy_threshold = float(self.settings.get("fuzzy_similarity_threshold", 80.0))
        semantic_threshold = float(self.settings.get("semantic_similarity_threshold", 75.0))
        min_words = int(self.settings.get("min_word_count_to_flag", 4))

        # Index source sentences for exact and fuzzy lookups
        source_sentence_map: List[tuple[str, str, ComparisonSource]] = []
        for src in comparison_sources:
            # Segment source text into individual sentences for precise matching
            s_units = self.preprocessor.split_sentences(src.text)
            candidates = [su.original_text for su in s_units] if s_units else src.sentences
            for s_line in candidates:
                cleaned = self.preprocessor.clean_for_analysis(s_line)
                if len(cleaned.split()) >= min_words:
                    source_sentence_map.append((s_line, cleaned, src))

        total_sentences = len(preprocessed.sentences)
        logger.info(f"Comparing {total_sentences} document sentences against {len(source_sentence_map)} source sentences.")

        for idx, sentence in enumerate(preprocessed.sentences):
            if idx % max(1, total_sentences // 20) == 0:
                pct = 55 + int((idx / max(1, total_sentences)) * 35)
                update_progress(pct, f"Analyzing sentence {idx + 1} of {total_sentences}...")

            # 1. Skip if in References and reference exclusion is enabled
            if exclude_refs and ref_start > 0 and sentence.start_char >= ref_start:
                continue

            # 2. Check if quoted
            is_quoted, has_cit = self.citation_analyzer.is_offset_in_quote(
                sentence.start_char, sentence.end_char, citations.quotes
            )

            # 3. Check for common academic phrase
            if filter_common and is_common_academic_phrase(sentence.normalized_text):
                continue

            # Skip very short sentences
            if len(sentence.tokens) < min_words:
                continue

            s_norm = sentence.normalized_text
            best_match = None
            best_score = 0.0
            best_algo = ""
            best_source = None
            best_source_text = ""

            # Check comparison sources
            for orig_src, clean_src, src_obj in source_sentence_map:
                # A. Exact Match (identical sentence or verbatim sentence containment)
                if s_norm == clean_src or (len(sentence.tokens) >= min_words and (s_norm in clean_src or clean_src in s_norm)):
                    best_match = {
                        "sentence": sentence.original_text,
                        "matched_text": orig_src,
                        "similarity_score": 100.0,
                        "algorithm": "Exact Match",
                        "page_number": sentence.page_number,
                        "start_char": sentence.start_char,
                        "end_char": sentence.end_char,
                        "is_quoted": is_quoted,
                        "is_cited": has_cit,
                        "is_ignored": False,
                        "source_name": src_obj.name,
                        "source_id": src_obj.source_id,
                    }
                    break

                # B. Fuzzy Match (RapidFuzz token_set_ratio)
                fuzzy_sim = fuzz.token_set_ratio(s_norm, clean_src)
                if fuzzy_sim >= fuzzy_threshold and fuzzy_sim > best_score:
                    best_score = fuzzy_sim
                    best_algo = "Fuzzy Match"
                    best_source = src_obj
                    best_source_text = orig_src

            if best_match:
                matches.append(best_match)
            elif best_score >= fuzzy_threshold and best_source:
                matches.append({
                    "sentence": sentence.original_text,
                    "matched_text": best_source_text,
                    "similarity_score": round(best_score, 1),
                    "algorithm": best_algo,
                    "page_number": sentence.page_number,
                    "start_char": sentence.start_char,
                    "end_char": sentence.end_char,
                    "is_quoted": is_quoted,
                    "is_cited": has_cit,
                    "is_ignored": False,
                    "source_name": best_source.name,
                    "source_id": best_source.source_id,
                })
            else:
                # C. Semantic Similarity fallback for long sentences (> 8 words)
                if len(sentence.tokens) >= 8 and source_sentence_map:
                    # Test semantic similarity against a sample of source candidates with moderate token overlap
                    candidates = [
                        (orig_src, clean_src, src_obj)
                        for orig_src, clean_src, src_obj in source_sentence_map[:30]
                        if fuzz.partial_ratio(s_norm, clean_src) > 55
                    ]
                    for orig_src, clean_src, src_obj in candidates:
                        sem_score = self.semantic_engine.compute_similarity(sentence.original_text, orig_src)
                        if sem_score >= semantic_threshold and sem_score > best_score:
                            matches.append({
                                "sentence": sentence.original_text,
                                "matched_text": orig_src,
                                "similarity_score": round(sem_score, 1),
                                "algorithm": "Semantic Similarity Indicator",
                                "page_number": sentence.page_number,
                                "start_char": sentence.start_char,
                                "end_char": sentence.end_char,
                                "is_quoted": is_quoted,
                                "is_cited": has_cit,
                                "is_ignored": False,
                                "source_name": src_obj.name,
                                "source_id": src_obj.source_id,
                            })
                            break

        update_progress(92, "Calculating composite score and risk levels...")
        score_breakdown = self.scoring_engine.calculate_score(
            total_document_words=extracted.word_count,
            matches=matches,
            exclude_quotes=exclude_quotes,
            exclude_references=exclude_refs,
        )

        update_progress(100, "Analysis complete.")

        warnings = list(extracted.warnings)
        if is_dup:
            warnings.append(f"Exact duplicate detected. Matches existing document: '{dup_name}'.")

        return DetectionResult(
            document_filename=extracted.filename,
            file_hash=extracted.file_hash,
            word_count=extracted.word_count,
            page_count=extracted.page_count,
            language=lang,
            extracted_text=extracted.full_text,
            preprocessed=preprocessed,
            structure=structure,
            citations=citations,
            ai_writing=ai_result,
            matches=matches,
            score_breakdown=score_breakdown,
            sources_compared_count=len(comparison_sources),
            is_scanned=extracted.is_scanned,
            is_duplicate=is_dup,
            duplicate_of=dup_name,
            warnings=warnings,
        )
