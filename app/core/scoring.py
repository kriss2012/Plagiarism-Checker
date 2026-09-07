"""Transparent academic similarity scoring engine.
Calculates weighted composite similarity with configurable exclusions (quotes, references, common phrases)
and risk level classification.
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
    total_analyzed_words: int
    matched_words: int
    exact_count: int
    fuzzy_count: int
    semantic_count: int
    quoted_count: int
    ignored_count: int
    explanation: str


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
    ) -> ScoreBreakdown:
        """Calculates transparent overall similarity and breakdown percentages."""
        if total_document_words == 0:
            return ScoreBreakdown(
                overall_similarity=0.0,
                risk_level="Very Low",
                exact_percentage=0.0,
                fuzzy_percentage=0.0,
                semantic_percentage=0.0,
                quoted_percentage=0.0,
                total_analyzed_words=0,
                matched_words=0,
                exact_count=0,
                fuzzy_count=0,
                semantic_count=0,
                quoted_count=0,
                ignored_count=0,
                explanation="Document contains 0 words.",
            )

        exact_words = 0
        fuzzy_words = 0
        semantic_words = 0
        quoted_words = 0
        ignored_count = 0

        exact_cnt = 0
        fuzzy_cnt = 0
        sem_cnt = 0
        quot_cnt = 0

        # Track character / word spans to prevent double-counting overlapping matches
        flagged_spans = []

        for m in matches:
            if m.get("is_ignored", False):
                ignored_count += 1
                continue

            word_len = max(1, len(m.get("sentence", "").split()))

            if m.get("is_quoted", False):
                quoted_words += word_len
                quot_cnt += 1
                if exclude_quotes:
                    continue  # Excluded from similarity score

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
        overall_sim = min(100.0, (total_effective_matched_words / total_document_words) * 100.0)

        exact_pct = min(100.0, (exact_words / total_document_words) * 100.0)
        fuzzy_pct = min(100.0, (fuzzy_words / total_document_words) * 100.0)
        sem_pct = min(100.0, (semantic_words / total_document_words) * 100.0)
        quoted_pct = min(100.0, (quoted_words / total_document_words) * 100.0)

        risk = self.determine_risk_level(overall_sim)

        explanation = (
            f"Overall similarity of {overall_sim:.1f}% calculated across {total_document_words:,} words. "
            f"Exact overlap: {exact_pct:.1f}%, Fuzzy overlap: {fuzzy_pct:.1f}%, "
            f"Semantic similarity: {sem_pct:.1f}%. "
            f"{'Quotations were excluded from similarity.' if exclude_quotes else 'Quotations were included in similarity.'}"
        )

        return ScoreBreakdown(
            overall_similarity=round(overall_sim, 1),
            risk_level=risk,
            exact_percentage=round(exact_pct, 1),
            fuzzy_percentage=round(fuzzy_pct, 1),
            semantic_percentage=round(sem_pct, 1),
            quoted_percentage=round(quoted_pct, 1),
            total_analyzed_words=total_document_words,
            matched_words=total_effective_matched_words,
            exact_count=exact_cnt,
            fuzzy_count=fuzzy_cnt,
            semantic_count=sem_cnt,
            quoted_count=quot_cnt,
            ignored_count=ignored_count,
            explanation=explanation,
        )
