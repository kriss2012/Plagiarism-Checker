"""Plagiarism and similarity detection orchestrator.
Coordinates Exact, Fuzzy (RapidFuzz), N-gram, TF-IDF, Semantic similarity analysis,
structured reference verification, and in-text citation auditing.
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
from app.core.reference_parser import ExtractedReference, ReferenceParser
from app.core.scoring import ScoreBreakdown, ScoringEngine
from app.core.structure import StructureAnalyzer
from app.ml.semantic import SemanticSimilarityEngine, is_semantic_model_available
from app.web.search import ScholarlySearchEngine
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
    reliability: str = "High"


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
    references: List[ExtractedReference]
    ai_writing: any
    matches: List[Dict]
    score_breakdown: ScoreBreakdown
    sources_compared_count: int
    is_scanned: bool = False
    ocr_confidence: Optional[float] = None
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class PlagiarismDetectionEngine:
    """Multi-method similarity, reference verification, and citation audit engine."""

    def __init__(self, settings: Optional[Dict] = None):
        self.settings = settings or DEFAULT_SETTINGS
        self.preprocessor = TextPreprocessor(
            min_word_count_to_flag=self.settings.get("min_word_count_to_flag", 4)
        )
        self.structure_analyzer = StructureAnalyzer()
        self.citation_analyzer = CitationAnalyzer()
        self.reference_parser = ReferenceParser()
        self.search_engine = ScholarlySearchEngine()
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
        """Executes the complete research paper verification pipeline."""
        logger.info(f"Starting research paper verification for: {extracted.filename}")

        def update_progress(pct: int, msg: str):
            if progress_callback:
                progress_callback(pct, msg)
            if cancel_check and cancel_check():
                raise InterruptedError("Analysis cancelled by user.")

        update_progress(5, "Detecting language and script...")
        lang, lang_conf = detect_language(extracted.full_text)

        update_progress(12, "Preprocessing and segmenting sentences...")
        preprocessed = self.preprocessor.preprocess_pages(extracted.pages, language=lang)

        update_progress(20, "Analyzing paper structure and sections...")
        structure = self.structure_analyzer.analyze(extracted.full_text)
        ref_start = structure["References"].start_char if structure.get("References") and structure["References"].detected else -1

        update_progress(28, "Extracting and parsing bibliography references...")
        parsed_refs = self.reference_parser.parse_references(extracted.full_text, ref_start_char=ref_start)

        update_progress(36, "Scanning in-text citations and quotations...")
        citations = self.citation_analyzer.analyze(extracted.full_text, references_start_char=ref_start)

        # Cross-check in-text citations with parsed bibliography
        c_issues, missing_cnt, unused_cnt, mismatch_cnt = self.citation_analyzer.cross_check_citations_with_references(
            citations.citations, parsed_refs, extracted.full_text
        )
        citations.citation_issues = c_issues
        citations.missing_citations_count = missing_cnt
        citations.unused_references_count = unused_cnt
        citations.mismatched_citations_count = mismatch_cnt

        # Link in-text citations and quotations to SentenceUnits
        total_sents = len(preprocessed.sentences)
        for s_i, sent in enumerate(preprocessed.sentences):
            is_q, q_has_c = self.citation_analyzer.is_offset_in_quote(
                sent.start_char, sent.end_char, citations.quotes
            )
            sent.is_quoted = is_q
            next_sent_start = preprocessed.sentences[s_i + 1].start_char if s_i + 1 < total_sents else len(extracted.full_text)
            
            # Check for in-sentence or trailing citations (e.g. "...identification. [1]")
            has_c = q_has_c or any(
                (sent.start_char <= c.start_char <= sent.end_char) or
                (sent.start_char <= c.end_char <= sent.end_char) or
                (sent.end_char <= c.start_char <= next_sent_start and (c.start_char - sent.end_char) <= 50) or
                abs(c.start_char - sent.end_char) <= 40
                for c in citations.citations
            )
            sent.is_cited = has_c

        update_progress(45, "Verifying references over academic registries (Crossref/OpenAlex)...")
        enable_web = self.settings.get("enable_web_search", True)
        if enable_web and parsed_refs:
            # Verify top references without blocking excessively
            for r_idx, ref_obj in enumerate(parsed_refs[:15]):
                try:
                    self.search_engine.verify_reference(ref_obj)
                except Exception as e:
                    logger.debug(f"Reference verification error for #{ref_obj.ref_number}: {e}")

        update_progress(52, "Computing stylometric AI-writing indicators...")
        sentence_texts = [s.original_text for s in preprocessed.sentences]
        ai_result = self.ai_detector.analyze(sentence_texts)

        # Duplicate check against local comparison sources
        is_dup = False
        dup_name = None
        for src in comparison_sources:
            src_hash = hashlib.sha256(src.text.encode("utf-8", errors="ignore")).hexdigest()
            if src_hash == extracted.file_hash or (len(src.text) > 100 and src.text.strip() == extracted.full_text.strip()):
                is_dup = True
                dup_name = src.name
                break

        # Discover web sources for the document if web search is enabled
        combined_sources = list(comparison_sources)
        if enable_web:
            update_progress(58, "Querying public academic repositories for matching literature...")
            try:
                para_texts = [p.text for p in getattr(extracted, "paragraphs", [])] or [extracted.full_text]
                web_hits = self.search_engine.discover_web_sources_for_paper(para_texts, max_sources=4)
                for h in web_hits:
                    h_sentences = [su.original_text for su in self.preprocessor.split_sentences(h.abstract or h.title)]
                    combined_sources.append(ComparisonSource(
                        source_id=None,
                        name=h.title,
                        text=h.abstract or h.title,
                        sentences=h_sentences,
                        author=h.authors,
                        year=h.year,
                        url=h.url,
                        doi=h.doi,
                        source_type=h.source_type,
                        reliability=h.reliability,
                    ))
            except Exception as e:
                logger.warning(f"Web source discovery notice: {e}")

        update_progress(65, f"Comparing against {len(combined_sources)} comparison & web literature sources...")
        matches: List[Dict] = []

        exclude_refs = self.settings.get("exclude_references", True)
        exclude_quotes = self.settings.get("exclude_quotes", True)
        filter_common = self.settings.get("filter_common_phrases", True)
        fuzzy_threshold = float(self.settings.get("fuzzy_similarity_threshold", 80.0))
        semantic_threshold = float(self.settings.get("semantic_similarity_threshold", 75.0))
        min_words = int(self.settings.get("min_word_count_to_flag", 4))

        # Index source sentences
        source_sentence_map: List[tuple[str, str, ComparisonSource]] = []
        for src in combined_sources:
            s_units = self.preprocessor.split_sentences(src.text)
            candidates = [su.original_text for su in s_units] if s_units else src.sentences
            for s_line in candidates:
                cleaned = self.preprocessor.clean_for_analysis(s_line)
                if len(cleaned.split()) >= min_words:
                    source_sentence_map.append((s_line, cleaned, src))

        total_sentences = len(preprocessed.sentences)
        logger.info(f"Comparing {total_sentences} sentences against {len(source_sentence_map)} source sentences.")

        for idx, sentence in enumerate(preprocessed.sentences):
            if idx % max(1, total_sentences // 20) == 0:
                pct = 65 + int((idx / max(1, total_sentences)) * 25)
                update_progress(pct, f"Analyzing passage {idx + 1} of {total_sentences}...")

            # 1. Skip if in References and reference exclusion is enabled
            if exclude_refs and ref_start > 0 and sentence.start_char >= ref_start:
                continue

            # 2. Check if quoted & cited
            is_quoted = sentence.is_quoted
            has_cit = sentence.is_cited

            # 3. Check for common academic phrase
            is_common = is_common_academic_phrase(sentence.normalized_text)

            if len(sentence.tokens) < min_words:
                continue

            s_norm = sentence.normalized_text
            best_match = None
            best_score = 0.0
            best_algo = ""
            best_source: Optional[ComparisonSource] = None
            best_source_text = ""

            # Check comparison sources
            for orig_src, clean_src, src_obj in source_sentence_map:
                # A. Exact Match
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
                        "source_url": src_obj.url,
                        "source_domain": src_obj.url.split("/")[2] if src_obj.url and "/" in src_obj.url else "Local Library",
                        "source_type": src_obj.source_type,
                        "source_reliability": src_obj.reliability,
                        "confidence": "High",
                        "review_decision": "Pending Review",
                        "review_notes": "",
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
                # Assign citation-aware classification
                if is_quoted and has_cit:
                    best_match["match_category"] = "Quoted + Cited"
                elif is_quoted:
                    best_match["match_category"] = "Quoted (Uncited)"
                elif has_cit:
                    best_match["match_category"] = "Copied + Cited Without Quotation"
                elif is_common:
                    best_match["match_category"] = "Common Knowledge"
                    if filter_common:
                        best_match["is_ignored"] = True
                else:
                    best_match["match_category"] = "Copied + No Citation"
                matches.append(best_match)

            elif best_score >= fuzzy_threshold and best_source:
                # Categorize fuzzy match
                category = "Paraphrased + Cited" if has_cit else ("Common Knowledge" if is_common else "Copied + No Citation")
                confidence = "High" if best_score >= 90 else "Medium"
                is_ign = bool(filter_common and is_common and not has_cit and not is_quoted)
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
                    "is_ignored": is_ign,
                    "source_name": best_source.name,
                    "source_id": best_source.source_id,
                    "source_url": best_source.url,
                    "source_domain": best_source.url.split("/")[2] if best_source.url and "/" in best_source.url else "Local Library",
                    "source_type": best_source.source_type,
                    "source_reliability": best_source.reliability,
                    "confidence": confidence,
                    "match_category": category,
                    "review_decision": "Pending Review",
                    "review_notes": "",
                })

            else:
                # C. Semantic Similarity fallback for long sentences (> 8 words)
                if len(sentence.tokens) >= 8 and source_sentence_map:
                    candidates = [
                        (orig_src, clean_src, src_obj)
                        for orig_src, clean_src, src_obj in source_sentence_map[:25]
                        if fuzz.partial_ratio(s_norm, clean_src) > 55
                    ]
                    for orig_src, clean_src, src_obj in candidates:
                        sem_score = self.semantic_engine.compute_similarity(sentence.original_text, orig_src)
                        if sem_score >= semantic_threshold and sem_score > best_score:
                            category = "Paraphrased + Cited" if has_cit else ("Common Knowledge" if is_common else "Paraphrased (Uncited)")
                            is_ign = bool(filter_common and is_common and not has_cit and not is_quoted)
                            matches.append({
                                "sentence": sentence.original_text,
                                "matched_text": orig_src,
                                "similarity_score": round(sem_score, 1),
                                "algorithm": "Semantic Similarity",
                                "page_number": sentence.page_number,
                                "start_char": sentence.start_char,
                                "end_char": sentence.end_char,
                                "is_quoted": is_quoted,
                                "is_cited": has_cit,
                                "is_ignored": is_ign,
                                "source_name": src_obj.name,
                                "source_id": src_obj.source_id,
                                "source_url": src_obj.url,
                                "source_domain": src_obj.url.split("/")[2] if src_obj.url and "/" in src_obj.url else "Local Library",
                                "source_type": src_obj.source_type,
                                "source_reliability": src_obj.reliability,
                                "confidence": "Medium",
                                "match_category": category,
                                "review_decision": "Pending Review",
                                "review_notes": "",
                            })
                            break

        update_progress(92, "Synthesizing multidimensional scores and research clearance verdict...")
        verified_refs_cnt = sum(1 for r in parsed_refs if r.status in ["VERIFIED", "PARTIALLY VERIFIED"])
        score_breakdown = self.scoring_engine.calculate_score(
            total_document_words=extracted.word_count,
            matches=matches,
            exclude_quotes=exclude_quotes,
            exclude_references=exclude_refs,
            references_total=len(parsed_refs),
            references_verified=verified_refs_cnt,
            citation_issues_count=len(citations.citation_issues),
            structure_dict=structure,
            sources_compared_count=len(combined_sources),
        )

        update_progress(100, "Verification complete.")

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
            references=parsed_refs,
            ai_writing=ai_result,
            matches=matches,
            score_breakdown=score_breakdown,
            sources_compared_count=len(combined_sources),
            is_scanned=extracted.is_scanned,
            ocr_confidence=getattr(extracted, "ocr_confidence", None),
            is_duplicate=is_dup,
            duplicate_of=dup_name,
            warnings=warnings,
        )
