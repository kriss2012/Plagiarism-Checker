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
class CitationIssue:
    issue_type: str  # "Missing Reference", "Unused Reference", "Citation Mismatch", "Citation Numbering Error", "Duplicate Citation", "Broken Citation"
    citation_text: str
    page_number: int = 1
    details: str = ""
    ref_number: Optional[int] = None


@dataclass
class CitationAnalysisResult:
    citation_count: int
    reference_count: int
    citations: List[CitationMatch] = field(default_factory=list)
    quotes: List[QuoteMatch] = field(default_factory=list)
    citation_issues: List[CitationIssue] = field(default_factory=list)
    missing_citations_count: int = 0
    unused_references_count: int = 0
    mismatched_citations_count: int = 0
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

    def cross_check_citations_with_references(
        self,
        citations: List[CitationMatch],
        references: list,
        body_text: str = "",
    ) -> Tuple[List[CitationIssue], int, int, int]:
        """Audits in-text citations against extracted bibliography references.
        Returns: (issues, missing_count, unused_count, mismatch_count)
        """
        issues: List[CitationIssue] = []
        if not references and not citations:
            return issues, 0, 0, 0

        ref_nums_available = {r.ref_number for r in references if getattr(r, 'ref_number', None) is not None}
        ref_authors_years = []
        for r in references:
            auth_token = r.authors.split(",")[0].split()[0].lower() if getattr(r, 'authors', None) else ""
            ref_authors_years.append((auth_token, getattr(r, 'year', None), getattr(r, 'ref_number', None), getattr(r, 'title', '')))

        cited_ref_nums = set()
        cited_authors = set()

        for cit in citations:
            if cit.citation_type == "IEEE":
                inner = cit.text.strip("[] \t")
                parts = re.split(r'[,;]', inner)
                for p in parts:
                    p = p.strip()
                    if "-" in p or "–" in p:
                        dash = "-" if "-" in p else "–"
                        subparts = p.split(dash)
                        if len(subparts) == 2 and subparts[0].strip().isdigit() and subparts[1].strip().isdigit():
                            start_n, end_n = int(subparts[0].strip()), int(subparts[1].strip())
                            for n in range(start_n, end_n + 1):
                                cited_ref_nums.add(n)
                                if ref_nums_available and n not in ref_nums_available:
                                    issues.append(CitationIssue(
                                        issue_type="Missing Reference",
                                        citation_text=f"[{n}]",
                                        details=f"In-text citation [{n}] has no matching entry in the reference list.",
                                        ref_number=n,
                                    ))
                    elif p.isdigit():
                        n = int(p)
                        cited_ref_nums.add(n)
                        if ref_nums_available and n not in ref_nums_available:
                            issues.append(CitationIssue(
                                issue_type="Missing Reference",
                                citation_text=f"[{n}]",
                                details=f"In-text citation [{n}] has no matching entry in the reference list.",
                                ref_number=n,
                            ))

            elif cit.citation_type == "Author-Year":
                m = RE_AUTHOR_YEAR.match(cit.text)
                if m:
                    auth_match = m.group(1) or m.group(3)
                    yr_match = m.group(2) or m.group(4)
                    first_author = auth_match.split()[0].lower().rstrip(".,") if auth_match else ""
                    yr_int = int(yr_match) if yr_match and yr_match.isdigit() else None
                    cited_authors.add(first_author)

                    matched = False
                    for r_auth, r_yr, r_num, _ in ref_authors_years:
                        if first_author and r_auth and (first_author in r_auth or r_auth in first_author):
                            if yr_int is None or r_yr is None or abs(yr_int - r_yr) <= 1:
                                matched = True
                                if r_num:
                                    cited_ref_nums.add(r_num)
                                break
                    if not matched and ref_authors_years:
                        issues.append(CitationIssue(
                            issue_type="Citation Mismatch",
                            citation_text=cit.text,
                            details=f"Author-year citation '{cit.text}' does not match any entry in the bibliography.",
                        ))

        # Check for unused references
        for r in references:
            r_num = getattr(r, 'ref_number', None)
            if r_num and r_num not in cited_ref_nums:
                auth_tok = r.authors.split(",")[0].split()[0] if getattr(r, 'authors', None) else ""
                if len(auth_tok) > 3 and auth_tok.lower() in body_text.lower():
                    continue
                r_title = getattr(r, 'title', '')
                issues.append(CitationIssue(
                    issue_type="Unused Reference",
                    citation_text=f"Ref #{r_num}: {r_title[:45]}...",
                    details="Publication appears in bibliography but is not cited anywhere in document body.",
                    ref_number=r_num,
                ))

        missing_count = sum(1 for i in issues if i.issue_type == "Missing Reference")
        unused_count = sum(1 for i in issues if i.issue_type == "Unused Reference")
        mismatch_count = sum(1 for i in issues if i.issue_type == "Citation Mismatch")

        return issues, missing_count, unused_count, mismatch_count
