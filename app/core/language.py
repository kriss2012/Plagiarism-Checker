"""Multi-language detection and script profiling supporting English, Hindi, Marathi, and more."""

import re
from typing import Dict, Tuple

# Devanagari character ranges
DEV_START = 0x0900
DEV_END = 0x097F

# Common language stopwords/clues
HINDI_MARKERS = {"है", "हैं", "था", "थी", "थे", "का", "के", "की", "में", "से", "को", "पर", "और", "या", "यह", "वह", "किया", "गया"}
MARATHI_MARKERS = {"आहे", "आहेत", "होते", "होती", "नाही", "च्या", "चे", "ची", "मध्ये", "आणि", "किंवा", "हे", "ती", "झाले", "केले", "यात", "त्यांच्या"}


def detect_language(text: str) -> Tuple[str, float]:
    """Detects the primary language of the text.
    Returns (language_name, confidence_score_between_0_and_1).
    """
    if not text or not text.strip():
        return "English", 1.0

    devanagari_count = 0
    latin_count = 0
    total_alpha = 0

    for char in text:
        cp = ord(char)
        if DEV_START <= cp <= DEV_END:
            devanagari_count += 1
            total_alpha += 1
        elif ('A' <= char <= 'Z') or ('a' <= char <= 'z'):
            latin_count += 1
            total_alpha += 1

    if total_alpha == 0:
        return "English", 0.5

    # Check script dominance
    dev_ratio = devanagari_count / total_alpha
    latin_ratio = latin_count / total_alpha

    if dev_ratio > 0.4:
        # Distinguish between Marathi and Hindi using vocabulary markers
        words = set(re.findall(r'[\u0900-\u097F]+', text))
        
        # Check specifically for Marathi exclusive character 'ळ' (U+0933)
        has_marathi_lla = any('\u0933' in w for w in words)
        
        marathi_hits = len(words.intersection(MARATHI_MARKERS)) + (3 if has_marathi_lla else 0)
        hindi_hits = len(words.intersection(HINDI_MARKERS))

        if marathi_hits > hindi_hits:
            confidence = min(0.95, 0.6 + (marathi_hits / max(1, len(words)) * 2))
            return "Marathi", confidence
        else:
            confidence = min(0.95, 0.6 + (hindi_hits / max(1, len(words)) * 2))
            return "Hindi", confidence

    return "English", min(0.99, max(0.7, latin_ratio))
