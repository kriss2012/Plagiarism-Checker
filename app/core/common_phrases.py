"""Common academic phrase filtering.
Prevents false-positive similarity flags caused by generic scientific phrasing and academic boilerplate.
"""

from typing import Set, List
import re

COMMON_ACADEMIC_PHRASES: Set[str] = {
    "the results of this study indicate",
    "the results of this study show",
    "the results indicate that",
    "this study aims to",
    "this research aims to",
    "the purpose of this study is to",
    "the purpose of this research is to",
    "the purpose of this research is",
    "in this paper we propose",
    "in this paper we present",
    "to the best of our knowledge",
    "as shown in figure",
    "as shown in table",
    "it is widely accepted that",
    "it is well known that",
    "has attracted significant attention",
    "plays a crucial role in",
    "plays an important role in",
    "in recent years there has been",
    "in recent years extensive research",
    "according to the results",
    "the experimental results demonstrate",
    "the experimental results show",
    "the rest of this paper is organized as follows",
    "further research is needed to",
    "future work will focus on",
    "in conclusion the proposed",
    "in summary our contributions",
    "a wide range of applications",
    "state of the art performance",
    "on the other hand",
    "in contrast to previous work",
    "compared with existing methods",
    "as depicted in",
    "can be seen from the table",
    "in this study",
    "the data reveals",
    "the findings indicate",
    "the findings suggest that",
    "this paper presents",
    "this paper investigates",
    "the objective of this study",
    "the aim of this research",
    "in conclusion",
    "the proposed method",
    "statistically significant",
    "results indicate that",
}

# Regex patterns matching common academic formulaic language and variations
COMMON_ACADEMIC_PATTERNS: List[re.Pattern] = [
    re.compile(r'\bin this study\b', re.IGNORECASE),
    re.compile(r'\bthe results (?:of this study )?(?:indicate|show|demonstrate) that\b', re.IGNORECASE),
    re.compile(r'\bresults indicate that\b', re.IGNORECASE),
    re.compile(r'\bthe purpose of this (?:study|research) is (?:to )?\b', re.IGNORECASE),
    re.compile(r'\bthis (?:study|research) aims to\b', re.IGNORECASE),
    re.compile(r'\bthis (?:study|paper) investigates\b', re.IGNORECASE),
    re.compile(r'\b(?:as )?(?:shown|depicted) in (?:table|fig(?:ure)?)\s*\d*\b', re.IGNORECASE),
    re.compile(r'\bcan be seen from (?:table|fig(?:ure)?)\s*\d*\b', re.IGNORECASE),
    re.compile(r'\bthe data reveals\b', re.IGNORECASE),
    re.compile(r'\bthe findings (?:indicate|suggest) that\b', re.IGNORECASE),
    re.compile(r'\bthe experimental results (?:show|demonstrate)\b', re.IGNORECASE),
    re.compile(r'\bthis paper (?:presents|investigates|proposes)\b', re.IGNORECASE),
    re.compile(r'\bin this paper we (?:propose|present)\b', re.IGNORECASE),
    re.compile(r'\bthe objective of this study\b', re.IGNORECASE),
    re.compile(r'\bthe aim of this (?:research|study)\b', re.IGNORECASE),
    re.compile(r'\bin conclusion\b', re.IGNORECASE),
    re.compile(r'\baccording to the results\b', re.IGNORECASE),
    re.compile(r'\bthe proposed (?:method|approach|framework)\b', re.IGNORECASE),
    re.compile(r'\bstatistically significant\b', re.IGNORECASE),
    re.compile(r'\bto the best of our knowledge\b', re.IGNORECASE),
    re.compile(r'\bit is (?:widely accepted|well known) that\b', re.IGNORECASE),
    re.compile(r'\bhas attracted significant attention\b', re.IGNORECASE),
    re.compile(r'\bplays (?:a crucial|an important) role in\b', re.IGNORECASE),
    re.compile(r'\bin recent years (?:there has been|extensive research)\b', re.IGNORECASE),
    re.compile(r'\bfurther research is needed to\b', re.IGNORECASE),
    re.compile(r'\bfuture work will focus on\b', re.IGNORECASE),
    re.compile(r'\ba wide range of applications\b', re.IGNORECASE),
    re.compile(r'\bstate of the art performance\b', re.IGNORECASE),
    re.compile(r'\bon the other hand\b', re.IGNORECASE),
    re.compile(r'\bin contrast to previous work\b', re.IGNORECASE),
    re.compile(r'\bcompared with existing methods\b', re.IGNORECASE),
    re.compile(r'\bthe rest of this paper is organized as follows\b', re.IGNORECASE),
    re.compile(r'\bexperimental hypothesis is validated\b', re.IGNORECASE),
    re.compile(r'\bsignificant trends\b', re.IGNORECASE),
    re.compile(r'\binvestigate the parameters\b', re.IGNORECASE),
]

GENERIC_STOPWORDS = {
    "the", "a", "an", "in", "of", "to", "that", "is", "are", "was", "were",
    "and", "or", "by", "for", "with", "on", "as", "at", "from", "be", "this",
    "our", "we", "it", "its", "their", "all"
}


def is_common_academic_phrase(text: str) -> bool:
    """Checks whether the given text is generic scientific phrasing / academic boilerplate.
    
    Distinguishes generic academic language from distinctive technical claims:
    - Sentences composed primarily of formulaic academic constructions return True.
    - Sentences containing a brief boilerplate phrase but substantial distinctive technical material return False.
    """
    if not text:
        return False

    norm = " ".join(re.sub(r'[^\w\s]', ' ', text.lower()).split())
    if not norm:
        return False

    # Exact match with known phrases
    if norm in COMMON_ACADEMIC_PHRASES:
        return True

    words = norm.split()
    total_words = len(words)
    if total_words == 0:
        return False

    # Check against regex patterns and calculate coverage
    matched_spans = []
    patterns_matched_count = 0
    for pat in COMMON_ACADEMIC_PATTERNS:
        m = pat.search(norm)
        if m:
            patterns_matched_count += 1
            matched_spans.append((m.start(), m.end()))

    if not matched_spans:
        return False

    # Mask matched spans to inspect remainder
    char_list = list(norm)
    for start, end in matched_spans:
        for i in range(start, end):
            char_list[i] = " "
    remainder = "".join(char_list)
    remaining_tokens = [w for w in remainder.split() if w not in GENERIC_STOPWORDS and not w.isdigit()]

    distinctive_count = len(remaining_tokens)
    common_ratio = (total_words - distinctive_count) / total_words

    # If the remaining non-generic tokens are very few, it is boilerplate
    if distinctive_count <= 2 and common_ratio >= 0.50:
        return True

    # If multiple academic patterns matched and distinctive words are minimal
    if patterns_matched_count >= 2 and distinctive_count <= 4:
        return True

    # If high proportion (>= 75%) is generic phrasing
    if common_ratio >= 0.75:
        return True

    return False

