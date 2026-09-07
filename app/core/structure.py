"""Academic research paper structure detection.
Identifies standard research sections: Abstract, Introduction, Literature Review,
Methodology, Results, Discussion, Conclusion, and References/Bibliography.
"""

from dataclasses import dataclass
import re
from typing import Dict, List, Optional


@dataclass
class SectionBoundary:
    name: str
    detected: bool
    start_char: int = -1
    end_char: int = -1
    page_number: int = 1


STANDARD_SECTIONS = [
    ("Title", r'^(?:\s*title\s*[:\-]|\bpaper\s+title\b)', False),
    ("Abstract", r'^(?:\d+\.?\s*)?\b(?:abstract|summary)\b', True),
    ("Keywords", r'^(?:\d+\.?\s*)?\b(?:keywords|index\s+terms)\b', False),
    ("Introduction", r'^(?:\d+\.?\s*)?\b(?:introduction|overview|background)\b', True),
    ("Literature Review", r'^(?:\d+\.?\s*)?\b(?:literature\s+review|related\s+work|previous\s+work)\b', True),
    ("Methodology", r'^(?:\d+\.?\s*)?\b(?:methodology|materials\s+and\s+methods|proposed\s+(?:system|method|architecture|framework)|experimental\s+setup)\b', True),
    ("Results", r'^(?:\d+\.?\s*)?\b(?:results|experimental\s+results|findings|evaluation|performance\s+analysis)\b', True),
    ("Discussion", r'^(?:\d+\.?\s*)?\b(?:discussion|analysis)\b', True),
    ("Conclusion", r'^(?:\d+\.?\s*)?\b(?:conclusion|conclusions|concluding\s+remarks|summary\s+and\s+conclusion)\b', True),
    ("References", r'^(?:\d+\.?\s*)?\b(?:references|bibliography|works\s+cited|literature\s+cited)\b', True),
]


class StructureAnalyzer:
    """Analyzes text to detect standard academic sections and boundaries."""

    def analyze(self, text: str) -> Dict[str, SectionBoundary]:
        """Detects presence and character ranges of standard sections."""
        results: Dict[str, SectionBoundary] = {}
        lines = text.splitlines(keepends=True)

        found_sections: List[tuple[str, int, int]] = []
        cur_offset = 0

        for line_idx, line in enumerate(lines):
            line_str = line.strip()
            # Only consider short heading-like lines (< 80 chars)
            if 3 < len(line_str) < 80:
                for sec_name, pattern, _ in STANDARD_SECTIONS:
                    if re.search(pattern, line_str, re.IGNORECASE):
                        # Matched heading
                        found_sections.append((sec_name, cur_offset, line_idx + 1))
                        break
            cur_offset += len(line)

        # Build boundaries
        for sec_name, _, _ in STANDARD_SECTIONS:
            # Find in found_sections
            matches = [item for item in found_sections if item[0] == sec_name]
            if matches:
                first_match = matches[0]
                results[sec_name] = SectionBoundary(
                    name=sec_name,
                    detected=True,
                    start_char=first_match[1],
                    end_char=-1,
                )
            else:
                results[sec_name] = SectionBoundary(
                    name=sec_name,
                    detected=False,
                )

        # Populate end_char as start_char of subsequent detected section
        detected_ordered = [item for item in found_sections]
        detected_ordered.sort(key=lambda x: x[1])

        for i, (name, start, _) in enumerate(detected_ordered):
            if name in results:
                if i + 1 < len(detected_ordered):
                    results[name].end_char = detected_ordered[i + 1][1]
                else:
                    results[name].end_char = len(text)

        return results

    def is_in_references(self, char_offset: int, structure: Dict[str, SectionBoundary]) -> bool:
        """Determines if a given character offset is within the References section."""
        ref_boundary = structure.get("References")
        if ref_boundary and ref_boundary.detected and ref_boundary.start_char != -1:
            return char_offset >= ref_boundary.start_char
        return False
