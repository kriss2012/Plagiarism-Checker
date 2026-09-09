"""Transparent academic similarity scoring engine.
Calculates multidimensional verification scores:
- Overall Similarity
- Direct Text Match
- Semantic Similarity
- Citation Coverage
- Reference Verification Score
- High-Risk Unattributed Similarity
- Section-by-Section Similarity Breakdown
- Academic Verdict (LOW CONCERN, MODERATE CONCERN, HIGH CONCERN, INCONCLUSIVE)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from app.config import DEFAULT_SETTINGS


@dataclass
class ScoreBreakdown:
    overall_similarity: float
    risk_level: str
    exact_percentage: float
    fuzzy_percentage: float
    semantic_percentage: float
    quoted_percentage: float
    direct_match_score: float = 0.0
    semantic_similarity_score: float = 0.0
    citation_coverage_score: float = 100.0
    reference_verification_score: float = 100.0
    high_risk_similarity: float = 0.0
    cited_matches_percentage: float = 0.0
    common_matches_percentage: float = 0.0
    total_analyzed_words: int = 0
    matched_words: int = 0
    exact_count: int = 0
    fuzzy_count: int = 0
    semantic_count: int = 0
    quoted_count: int = 0
    ignored_count: int = 0
    academic_verdict: str = "LOW CONCERN"  # LOW CONCERN, MODERATE CONCERN, HIGH CONCERN, INCONCLUSIVE
    verdict_summary: str = ""
    section_scores: Dict[str, float] = field(default_factory=dict)
    explanation: str = ""


class ScoringEngine:
    """Computes similarity scores and risk levels with transparent accounting."""

    def __init__(self, settings: Optional[Dict] = None):
        self.settings = settings or DEFAULT_SETTINGS

    def determine_risk_level(self, similarity_pct: float) -> str:
        """Maps similarity score to academic risk level based on configured thresholds."""
        vl_max = self.settings.get("risk_very_low_max", 10.0)
        l_max = self.settings.get("risk_low_max", 25.0)
        m_max = self.settings.get("risk_moderate_max", 40.0)
        h_max = self.settings.get("risk_high_max", 60.0)

        if similarity_pct <= vl_max:
            return "Very Low"
        elif similarity_pct <= l_max:
            return "Low"
        elif similarity_pct <= m_max:
            return "Moderate"
        elif similarity_pct <= h_max:
            return "High"
        else:
            return "Very High"

    def calculate_score(
        self,
        total_document_words: int,
        matches: List[Dict],
        exclude_quotes: bool = True,
        exclude_references: bool = True,
        references_total: int = 0,
        references_verified: int = 0,
        citation_issues_count: int = 0,
        structure_dict: Optional[Dict] = None,
        sources_compared_count: int = 1,
    ) -> ScoreBreakdown:
        """Calculates transparent overall similarity, multi-dimensional scores, and academic verdict."""
        if total_document_words == 0:
            return ScoreBreakdown(
                overall_similarity=0.0,
                risk_level="Very Low",
                exact_percentage=0.0,
                fuzzy_percentage=0.0,
                semantic_percentage=0.0,
                quoted_percentage=0.0,
                direct_match_score=0.0,
                semantic_similarity_score=0.0,
                citation_coverage_score=100.0,
                reference_verification_score=100.0,
                high_risk_similarity=0.0,
                academic_verdict="INCONCLUSIVE" if sources_compared_count == 0 else "LOW CONCERN",
                verdict_summary="Document contains 0 words.",
                explanation="Document contains 0 words.",
            )

        exact_words = 0
        fuzzy_words = 0
        semantic_words = 0
        quoted_words = 0
        high_risk_words = 0
        cited_match_words = 0
        common_words = 0
        ignored_count = 0

        exact_cnt = 0
        fuzzy_cnt = 0
        sem_cnt = 0
        quot_cnt = 0

        for m in matches:
            if m.get("is_ignored", False):
                ignored_count += 1
                continue

            word_len = max(1, len(m.get("sentence", "").split()))
            is_quoted = m.get("is_quoted", False)
            is_cited = m.get("is_cited", False)
            category = m.get("match_category", "")

            if is_quoted:
                quoted_words += word_len
                quot_cnt += 1
                if exclude_quotes:
                    continue  # Excluded from overall similarity

            if is_cited:
                cited_match_words += word_len

            # Categorize match risk
            if "no citation" in category.lower() or (not is_quoted and not is_cited):
                high_risk_words += word_len
            elif "common" in category.lower():
                common_words += word_len

            algo = m.get("algorithm", "").lower()
            if "exact" in algo:
                exact_words += word_len
                exact_cnt += 1
            elif "fuzzy" in algo:
                fuzzy_words += word_len
                fuzzy_cnt += 1
            elif "semantic" in algo:
                semantic_words += word_len
                sem_cnt += 1
            else:
                fuzzy_words += word_len
                fuzzy_cnt += 1

        total_effective_matched_words = exact_words + int(fuzzy_words * 0.85) + int(semantic_words * 0.70)
        overall_pct = min(100.0, (total_effective_matched_words / max(1, total_document_words)) * 100.0)
        
        exact_pct = min(100.0, (exact_words / max(1, total_document_words)) * 100.0)
        fuzzy_pct = min(100.0, (fuzzy_words / max(1, total_document_words)) * 100.0)
        semantic_pct = min(100.0, (semantic_words / max(1, total_document_words)) * 100.0)
        quoted_pct = min(100.0, (quoted_words / max(1, total_document_words)) * 100.0)
        high_risk_pct = min(100.0, (high_risk_words / max(1, total_document_words)) * 100.0)
        cited_pct = min(100.0, (cited_match_words / max(1, total_document_words)) * 100.0)
        common_pct = min(100.0, (common_words / max(1, total_document_words)) * 100.0)

        # Reference Verification Score
        if references_total > 0:
            ref_verif_score = round((references_verified / references_total) * 100.0, 1)
        else:
            ref_verif_score = 100.0

        # Citation Coverage Score (penalized by citation issues like missing / unused)
        citation_penalty = min(80.0, citation_issues_count * 5.0)
        citation_cov_score = max(0.0, round(100.0 - citation_penalty, 1))

        risk = self.determine_risk_level(overall_pct)

        # Section-by-section breakdown
        section_scores = self.calculate_section_breakdown(structure_dict, matches, total_document_words)

        # Academic Verdict Determination
        if sources_compared_count == 0:
            verdict = "INCONCLUSIVE"
            verdict_summary = "Insufficient internet or comparison source coverage to make a definitive assessment."
        elif high_risk_pct > 15.0 or exact_pct > 25.0:
            verdict = "HIGH CONCERN"
            verdict_summary = "Multiple passages exhibit strong unattributed similarity to published sources. Significant revision and supervisor consultation required."
        elif high_risk_pct > 5.0 or overall_pct > 18.0 or citation_issues_count > 3:
            verdict = "MODERATE CONCERN"
            verdict_summary = "The scan identified passages with substantial similarity. Some citations and references require manual review before submission."
        else:
            verdict = "LOW CONCERN"
            verdict_summary = "No significant unattributed similarity detected. Natural overlaps appear properly cited or derived from common academic terminology."

        explanation = (
            f"Overall similarity of {overall_pct:.1f}% calculated from {total_effective_matched_words} effective "
            f"matched words out of {total_document_words} total words. "
            f"Exact: {exact_cnt} matches ({exact_pct:.1f}%), "
            f"Fuzzy: {fuzzy_cnt} matches ({fuzzy_pct:.1f}%), "
            f"Semantic: {sem_cnt} matches ({semantic_pct:.1f}%)."
        )

        return ScoreBreakdown(
            overall_similarity=round(overall_pct, 1),
            risk_level=risk,
            exact_percentage=round(exact_pct, 1),
            fuzzy_percentage=round(fuzzy_pct, 1),
            semantic_percentage=round(semantic_pct, 1),
            quoted_percentage=round(quoted_pct, 1),
            direct_match_score=round(exact_pct, 1),
            semantic_similarity_score=round(semantic_pct, 1),
            citation_coverage_score=citation_cov_score,
            reference_verification_score=ref_verif_score,
            high_risk_similarity=round(high_risk_pct, 1),
            cited_matches_percentage=round(cited_pct, 1),
            common_matches_percentage=round(common_pct, 1),
            total_analyzed_words=total_document_words,
            matched_words=total_effective_matched_words,
            exact_count=exact_cnt,
            fuzzy_count=fuzzy_cnt,
            semantic_count=sem_cnt,
            quoted_count=quot_cnt,
            ignored_count=ignored_count,
            academic_verdict=verdict,
            verdict_summary=verdict_summary,
            section_scores=section_scores,
            explanation=explanation,
        )

    def calculate_section_breakdown(
        self,
        structure_dict: Optional[Dict],
        matches: List[Dict],
        total_document_words: int,
    ) -> Dict[str, float]:
        """Calculates similarity percentages individually for academic sections."""
        standard_sections = [
            "Title", "Abstract", "Introduction", "Literature Review",
            "Methodology", "Results", "Discussion", "Conclusion"
        ]
        breakdown: Dict[str, float] = {}

        if not structure_dict:
            for s in standard_sections:
                breakdown[s] = 0.0
            return breakdown

        for s_name in standard_sections:
            sec_info = structure_dict.get(s_name)
            if sec_info and getattr(sec_info, "detected", False):
                s_start = sec_info.start_char
                s_end = sec_info.end_char
                sec_text = sec_info.text if hasattr(sec_info, "text") else ""
                sec_words = max(1, len(sec_text.split()))

                matched_in_sec = 0
                for m in matches:
                    if m.get("is_ignored", False):
                        continue
                    m_start = m.get("start_char", 0)
                    if s_start <= m_start < s_end:
                        matched_in_sec += len(m.get("sentence", "").split())

                pct = min(100.0, (matched_in_sec / max(1, sec_words)) * 100.0)
                breakdown[s_name] = round(pct, 1)
            else:
                breakdown[s_name] = 0.0

        return breakdown
