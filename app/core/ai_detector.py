"""AI-Generated Writing Likelihood Indicator.
Uses linguistic heuristics (sentence length variation, burstiness, type-token ratio,
and repetition entropy) to compute a probabilistic AI-writing likelihood indicator.

IMPORTANT: AI detection is strictly heuristic and probabilistic.
It does NOT claim definitive proof of AI generation.
"""

from dataclasses import dataclass
import math
import re
from typing import List


@dataclass
class AIDetectionResult:
    likelihood: str  # "Low", "Medium", "High"
    score: float  # 0.0 to 100.0%
    burstiness_score: float
    perplexity_proxy: float
    sentence_length_std: float
    type_token_ratio: float
    disclaimer: str = (
        "AI-generated text detection is probabilistic and can produce false positives. "
        "It reflects statistical writing uniformity rather than definitive proof of AI usage."
    )


class AIWritingDetector:
    """Heuristic stylometric analyzer for estimating AI-writing likelihood."""

    def analyze(self, sentences: List[str]) -> AIDetectionResult:
        """Analyzes a list of sentences for stylometric uniformity and burstiness."""
        if not sentences or len(sentences) < 5:
            return AIDetectionResult(
                likelihood="Low",
                score=10.0,
                burstiness_score=0.5,
                perplexity_proxy=0.5,
                sentence_length_std=5.0,
                type_token_ratio=0.7,
            )

        # 1. Sentence length variance & standard deviation
        lengths = [len(s.split()) for s in sentences if len(s.split()) > 0]
        if not lengths:
            return AIDetectionResult("Low", 0.0, 0.0, 0.0, 0.0, 0.0)

        mean_len = sum(lengths) / len(lengths)
        variance = sum((x - mean_len) ** 2 for x in lengths) / len(lengths)
        std_len = math.sqrt(variance)

        # AI text typically has lower sentence-length variance (around 4-8 words std)
        # Human academic writing typically has higher variance (10-20 words std, mixing very short and very long compound sentences)
        length_uniformity_score = max(0.0, min(1.0, 1.0 - (std_len / 14.0)))

        # 2. Burstiness: standard deviation / mean of sentence lengths
        burstiness = std_len / (mean_len + 1e-5)
        # Low burstiness (< 0.35) often correlates with LLM generation
        burstiness_indicator = max(0.0, min(1.0, 1.0 - (burstiness / 0.6)))

        # 3. Type-Token Ratio (Lexical Diversity)
        all_words = []
        for s in sentences:
            words = re.findall(r'\b[a-zA-Z]{3,}\b', s.lower())
            all_words.extend(words)

        if len(all_words) > 50:
            unique_words = len(set(all_words))
            ttr = unique_words / len(all_words)
            # High TTR with very uniform sentence structure is common in LLMs
            lexical_uniformity = 1.0 - abs(ttr - 0.55) * 1.5
            lexical_uniformity = max(0.0, min(1.0, lexical_uniformity))
        else:
            ttr = 0.6
            lexical_uniformity = 0.5

        # 4. Composite probabilistic score (0 - 100)
        composite = (
            0.40 * length_uniformity_score +
            0.35 * burstiness_indicator +
            0.25 * lexical_uniformity
        ) * 100.0

        # Discretion thresholds
        if composite < 40.0:
            likelihood = "Low"
        elif composite < 65.0:
            likelihood = "Medium"
        else:
            likelihood = "High"

        return AIDetectionResult(
            likelihood=likelihood,
            score=round(composite, 1),
            burstiness_score=round(burstiness, 2),
            perplexity_proxy=round(length_uniformity_score * 100, 1),
            sentence_length_std=round(std_len, 2),
            type_token_ratio=round(ttr, 2),
        )
