"""Structured academic reference and bibliography parser.
Identifies bibliography sections, parses individual entries across APA, MLA, IEEE,
Chicago, Harvard, Vancouver, and Numeric formats, extracting structured metadata.
"""

from dataclasses import dataclass, field
import re
from typing import Dict, List, Optional, Tuple


@dataclass
class ExtractedReference:
    ref_number: Optional[int]
    raw_text: str
    title: str = ""
    authors: str = ""
    journal: str = ""
    year: Optional[int] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    publisher: Optional[str] = None
    status: str = "NOT VERIFIED"  # VERIFIED, PARTIALLY VERIFIED, NOT VERIFIED, SUSPICIOUS, DUPLICATE, BROKEN LINK
    verification_source: Optional[str] = None
    matched_metadata: Optional[Dict] = None
    difference_notes: Optional[str] = None
    is_duplicate: bool = False


# Regex patterns for reference section headers
RE_REF_HEADERS = re.compile(
    r'^(?:references\s+and\s+bibliography|references|bibliography|works\s+cited|literature\s+cited|sources)\s*$',
    re.IGNORECASE | re.MULTILINE
)

# DOI and URL regexes
RE_DOI = re.compile(r'\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b')
RE_URL = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')

# Year pattern: 4 digits from 1900 to 2099
RE_YEAR = re.compile(r'\b(19\d\d|20\d\d)[a-z]?\b')

# Numbered prefix pattern, e.g. [1], [12], 1., 12.
RE_NUMBERED_PREFIX = re.compile(r'^(?:\[\s*(\d+)\s*\]|(\d+)\.\s+)')


class ReferenceParser:
    """Parses raw text into structured academic reference records."""

    def extract_references_section(self, full_text: str) -> Tuple[str, int]:
        """Finds the references/bibliography section in document text.
        Returns: (section_text, start_char_offset)
        """
        for m in RE_REF_HEADERS.finditer(full_text):
            start = m.end()
            return full_text[start:].strip(), start
        return "", -1

    def parse_references(self, full_text: str, ref_start_char: int = -1) -> List[ExtractedReference]:
        """Extracts and parses all references from the document."""
        if ref_start_char > 0:
            ref_text = full_text[ref_start_char:].strip()
        else:
            ref_text, _ = self.extract_references_section(full_text)

        if not ref_text:
            return []

        # Split reference block into raw individual entries
        raw_entries = self._split_reference_entries(ref_text)
        results: List[ExtractedReference] = []
        seen_titles = {}

        for idx, entry_str in enumerate(raw_entries, start=1):
            cleaned = " ".join(entry_str.split())
            if len(cleaned) < 15:
                continue

            parsed = self._parse_single_reference(cleaned, fallback_num=idx)
            
            # Check for duplicate bibliography entry
            norm_title = re.sub(r'[^a-zA-Z0-9]', '', parsed.title.lower())
            if norm_title and len(norm_title) > 10:
                if norm_title in seen_titles:
                    parsed.is_duplicate = True
                    parsed.status = "DUPLICATE"
                    parsed.difference_notes = f"Duplicate bibliography entry of Reference #{seen_titles[norm_title]}"
                else:
                    seen_titles[norm_title] = parsed.ref_number or idx

            results.append(parsed)

        return results

    def _split_reference_entries(self, ref_text: str) -> List[str]:
        """Splits multi-line reference text into distinct reference entries."""
        lines = ref_text.splitlines()
        entries: List[str] = []
        current_entry: List[str] = []

        is_numbered_style = bool(re.search(r'(?:^\s*\[\d+\]|^\s*\d+\.\s+)', ref_text, re.MULTILINE))

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                if current_entry:
                    entries.append(" ".join(current_entry))
                    current_entry = []
                continue

            if is_numbered_style:
                # Check if this line starts a new numbered reference
                if RE_NUMBERED_PREFIX.match(trimmed):
                    if current_entry:
                        entries.append(" ".join(current_entry))
                        current_entry = []
                    current_entry.append(trimmed)
                else:
                    if current_entry:
                        current_entry.append(trimmed)
                    else:
                        current_entry.append(trimmed)
            else:
                # Hanging indent or blank line separated style (APA, Harvard, Chicago)
                # If line starts with capital letters/author name and ends previous with period
                starts_author = bool(re.match(r'^[A-Z][a-zA-Z\s\.,\-&]{2,30}\s*\(?(?:19|20)\d{2}', trimmed))
                if starts_author and current_entry and (current_entry[-1].endswith(".") or current_entry[-1].endswith('"')):
                    entries.append(" ".join(current_entry))
                    current_entry = [trimmed]
                else:
                    current_entry.append(trimmed)

        if current_entry:
            entries.append(" ".join(current_entry))

        return entries

    def _parse_single_reference(self, text: str, fallback_num: int) -> ExtractedReference:
        """Extracts structured fields from an individual reference string."""
        ref_num = None
        work_text = text

        # 1. Number prefix
        m_num = RE_NUMBERED_PREFIX.match(work_text)
        if m_num:
            num_str = m_num.group(1) or m_num.group(2)
            if num_str and num_str.isdigit():
                ref_num = int(num_str)
            work_text = work_text[m_num.end():].strip()
        else:
            ref_num = fallback_num

        # 2. Extract DOI
        doi = None
        m_doi = RE_DOI.search(work_text)
        if m_doi:
            doi = m_doi.group(1).rstrip(".")
            # Clean doi from text for cleaner title parsing if at the end
            work_text = work_text[:m_doi.start()] + work_text[m_doi.end():]

        # 3. Extract URL
        url = None
        m_url = RE_URL.search(work_text)
        if m_url:
            url = m_url.group(0).rstrip(".")
            work_text = work_text[:m_url.start()] + work_text[m_url.end():]

        # 4. Extract Publication Year
        year = None
        year_matches = list(RE_YEAR.finditer(work_text))
        if year_matches:
            # Usually the first year in APA/Harvard or last year in IEEE
            year_candidate = year_matches[0].group(1)
            year = int(year_candidate)

        # 5. Extract Title and Authors
        authors = ""
        title = ""
        journal = ""

        # Case A: Title in Quotes, e.g. IEEE or MLA: Author, "Title of Paper", Journal...
        quote_match = re.search(r'["“]([^"”]+)["”]', work_text)
        if quote_match:
            title = quote_match.group(1).strip().rstrip(",")
            authors = work_text[:quote_match.start()].strip().rstrip(".,-")
            remainder = work_text[quote_match.end():].strip().lstrip(".,-")
            journal = remainder.split(",")[0].strip() if remainder else ""
        else:
            # Case B: APA Style: Authors (Year). Title. Journal...
            apa_match = re.search(r'^(.*?)\s*[\(\[]?\s*(19\d\d|20\d\d)[a-z]?\s*[\)\]]?\.?\s+(.*?)(?:\.|$)', work_text)
            if apa_match:
                authors = apa_match.group(1).strip().rstrip(".,")
                title = apa_match.group(3).strip().rstrip(".")
                rest = work_text[apa_match.end():].strip()
                if rest:
                    journal = rest.split(".")[0].strip()
            else:
                # Case C: Segment by period
                parts = [p.strip() for p in work_text.split(".") if p.strip()]
                if len(parts) >= 2:
                    authors = parts[0]
                    title = parts[1]
                    if len(parts) >= 3:
                        journal = parts[2]
                elif parts:
                    title = parts[0]

        # 6. Extract Volume / Pages if present (e.g. vol. 12, no. 3, pp. 45-60 or 12(3):45-60)
        volume = None
        issue = None
        pages = None

        vol_match = re.search(r'(?:vol(?:ume)?\.?\s*(\d+)|(\d+)\s*\(\s*(\d+)\s*\))', work_text, re.IGNORECASE)
        if vol_match:
            volume = vol_match.group(1) or vol_match.group(2)
            if vol_match.group(3):
                issue = vol_match.group(3)

        pages_match = re.search(r'(?:pp?\.?\s*(\d+[-–]\d+|\d+)|:\s*(\d+[-–]\d+))', work_text, re.IGNORECASE)
        if pages_match:
            pages = pages_match.group(1) or pages_match.group(2)

        return ExtractedReference(
            ref_number=ref_num,
            raw_text=text,
            title=title or text[:80],
            authors=authors or "Unknown Authors",
            journal=journal,
            year=year,
            volume=volume,
            issue=issue,
            pages=pages,
            doi=doi,
            url=url,
        )
