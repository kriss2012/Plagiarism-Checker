"""Common academic phrase filtering.
Prevents false-positive similarity flags caused by generic scientific phrasing and academic boilerplate.
"""

from typing import Set

COMMON_ACADEMIC_PHRASES: Set[str] = {
    "the results of this study indicate",
    "the results of this study show",
    "this study aims to",
    "this research aims to",
    "the purpose of this study is to",
    "the purpose of this research is to",
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
}


def is_common_academic_phrase(text: str) -> bool:
    """Checks whether the given normalized text is or heavily contains a common academic phrase."""
    if not text:
        return False
    norm = " ".join(text.lower().split())
    # Exact match
    if norm in COMMON_ACADEMIC_PHRASES:
        return True
    # Substring match if text is short (< 8 words)
    words = norm.split()
    if len(words) <= 8:
        for phrase in COMMON_ACADEMIC_PHRASES:
            if phrase in norm or norm in phrase:
                return True
    return False
