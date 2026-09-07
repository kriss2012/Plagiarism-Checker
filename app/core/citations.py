"""Citation and quotation detection engine.
Identifies in-text citations (APA, Harvard, IEEE), DOIs, URLs, and quoted text blocks.
Classifies text as 'Quoted / Cited Content' to prevent false plagiarism flags.
"""

from dataclasses import dataclass, field
import re
from typing import List, Optional, Tuple


@dataclass
class CitationMatch:
    text: str
    citation_type: str  # "IEEE", "Author-Year", "DOI", "URL"
    start_char: int
    end_char: int


@dataclass
class QuoteMatch:
    text: str
    quote_type: str  # "Double", "Single", "Block"
    start_char: int
    end_char: int
    has_adjacent_citation: bool = False


@dataclass
class CitationAnalysisResult:
    citation_count: int
    reference_count: int
    citations: List[CitationMatch] = field(default_factory=list)
    quotes: List[QuoteMatch] = field(default_factory=list)
    uncited_claims: int = 0
    warnings: List[str] = field(default_factory=list)


# Regular expressions for citations
# IEEE numbered citations e.g. [1], [12], [1-3], [4, 5]
RE_IEEE = re.compile(r'\[\s*(\d+(?:\s*[-–,\s]\s*\d+)*)\s*\]')

# Author-Year citations e.g. (Smith, 2024), (Johnson & Doe, 2021), Smith et al. (2020)
RE_AUTHOR_YEAR = re.compile(
    r'(?:\b([A-Z][a-zA-Z]+(?:\s+et\s+al\.)?)\s*,?\s*\((19\d{2}|20\d{2})[a-z]?\)|'
    r'\(\s*([A-Z][a-zA-Z]+(?:(?:\s+(?:and|&)\s+|\s*,\s*)[A-Z][a-zA-Z]+)?(?:\s+et\s+al\.)?)\s*,\s*(19\d{2}|20\d{2})[a-z]?\s*(?:,\s*p{1,2}\.?\s*\d+)?\s*\))'
)

# DOI regex e.g. 10.1000/182, 10.1109/5.771073
RE_DOI = re.compile(r'\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b')

# URL regex
RE_URL = re.compile(r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)')

# Quotations regex: text within double quotes or single quotes with at least 3 words
RE_DOUBLE_QUOTES = re.compile(r'"([^"\n]{10,500})"')
RE_SINGLE_QUOTES = re.compile(r"'([^'\n]{15,500})'")


class CitationAnalyzer:
    """Detects citations, bibliography entries, and quotations."""

    def analyze(self, text: str, references_start_char: int = -1) -> CitationAnalysisResult:
        """Analyzes text for citations, quotes, and references."""
        citations: List[CitationMatch] = []
        quotes: List[QuoteMatch] = []

        # Only analyze citations in the body text (before References section)
        body_text = text[:references_start_char] if references_start_char > 0 else text
        ref_text = text[references_start_char:] if references_start_char > 0 else ""

        # 1. IEEE citations
        for m in RE_IEEE.finditer(body_text):
            citations.append(CitationMatch(
                text=m.group(0),
                citation_type="IEEE",
                start_char=m.start(),
                end_char=m.end(),
            ))

        # 2. Author-Year citations
        for m in RE_AUTHOR_YEAR.finditer(body_text):
            citations.append(CitationMatch(
                text=m.group(0),
                citation_type="Author-Year",
                start_char=m.start(),
                end_char=m.end(),
            ))

        # 3. DOIs
        for m in RE_DOI.finditer(body_text):
            citations.append(CitationMatch(
                text=m.group(0),
                citation_type="DOI",
                start_char=m.start(),
                end_char=m.end(),
            ))

        # 4. URLs
        for m in RE_URL.finditer(body_text):
            citations.append(CitationMatch(
                text=m.group(0),
                citation_type="URL",
                start_char=m.start(),
                end_char=m.end(),
            ))

        # 5. Double quotes
        for m in RE_DOUBLE_QUOTES.finditer(body_text):
            # Check if there is an adjacent citation within 100 characters
            q_start = m.start()
            q_end = m.end()
            has_cit = any(
                abs(c.start_char - q_end) < 100 or abs(c.end_char - q_start) < 40
                for c in citations
            )
            quotes.append(QuoteMatch(
                text=m.group(1),
                quote_type="Double",
                start_char=q_start,
                end_char=q_end,
                has_adjacent_citation=has_cit,
            ))

        # 6. Single quotes
        for m in RE_SINGLE_QUOTES.finditer(body_text):
            q_start = m.start()
            q_end = m.end()
            has_cit = any(
                abs(c.start_char - q_end) < 100 or abs(c.end_char - q_start) < 40
                for c in citations
            )
            quotes.append(QuoteMatch(
                text=m.group(1),
                quote_type="Single",
                start_char=q_start,
                end_char=q_end,
                has_adjacent_citation=has_cit,
            ))

        # 7. Estimate reference count in the references section
        ref_count = 0
        if ref_text:
            ref_lines = [l.strip() for l in ref_text.splitlines() if len(l.strip()) > 20]
            # Look for numbered references [1] or bulleted lines
            numbered_refs = len(re.findall(r'(?:^\s*\[\d+\]|^\s*\d+\.\s+)', ref_text, re.MULTILINE))
            ref_count = max(numbered_refs, len(ref_lines))

        # 8. Uncited claims heuristic: substantial body paragraphs with no citations
        paragraphs = [p.strip() for p in body_text.split("\n\n") if len(p.strip()) > 150]
        uncited = 0
        for p in paragraphs:
            has_cit_in_p = bool(RE_IEEE.search(p) or RE_AUTHOR_YEAR.search(p))
            if not has_cit_in_p and not any(kw in p.lower() for kw in ["in this section", "we propose", "we present", "our model"]):
                uncited += 1

        warnings = []
        if len(citations) == 0 and len(body_text.split()) > 300:
            warnings.append("No standard academic citations detected in document body.")
        if references_start_char > 0 and ref_count == 0:
            warnings.append("References section detected but appears to have few or unparsed entries.")

        return CitationAnalysisResult(
            citation_count=len(citations),
            reference_count=ref_count,
            citations=citations,
            quotes=quotes,
            uncited_claims=uncited,
            warnings=warnings,
        )

    def is_offset_in_quote(self, start_char: int, end_char: int, quotes: List[QuoteMatch]) -> Tuple[bool, bool]:
        """Checks if a span overlaps with a quote.
        Returns (is_quoted, has_adjacent_citation).
        """
        for q in quotes:
            # Overlap check
            if not (end_char <= q.start_char or start_char >= q.end_char):
                return True, q.has_adjacent_citation
        return False, False
