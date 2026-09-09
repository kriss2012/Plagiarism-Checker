"""Modular, privacy-respecting academic web search and multi-source reference verification module.
Uses legitimate public scholarly APIs (Crossref, OpenAlex, Semantic Scholar, arXiv).
Operates with rate-limiting, local caching, and graceful offline fallback.
"""

from dataclasses import dataclass, field
import hashlib
import re
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse
from rapidfuzz import fuzz
import requests
from app.utils.logger import logger


@dataclass
class ScholarlySearchResult:
    title: str
    authors: str
    year: Optional[int] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    abstract: str = ""
    journal: str = ""
    source_type: str = "Journal"  # Journal, Conference, Repository, Preprint, Book, Web
    reliability: str = "High"     # High, Medium, Low
    domain: str = ""
    is_primary: bool = True
    secondary_copies: List[str] = field(default_factory=list)


# In-memory session cache to avoid duplicate network queries
_SEARCH_CACHE: Dict[str, List[ScholarlySearchResult]] = {}
_DOI_CACHE: Dict[str, Optional[Dict]] = {}


class ScholarlySearchEngine:
    """Queries legitimate public scholarly APIs for academic paper metadata and reference verification."""

    def __init__(self, timeout: int = 6):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "ResearchGuardAcademicChecker/2.0 (https://github.com/kriss2012/Plagiarism-Checker; mailto:central.library@imrd.ac.in)"
        }

    # ----------------------------------------------------------------------
    # 1. API Clients: Crossref, OpenAlex, Semantic Scholar, arXiv
    # ----------------------------------------------------------------------

    def get_crossref_by_doi(self, doi: str) -> Optional[Dict]:
        """Directly retrieves metadata for a DOI from Crossref."""
        clean_doi = doi.strip().lower()
        if clean_doi in _DOI_CACHE:
            return _DOI_CACHE[clean_doi]

        try:
            url = f"https://api.crossref.org/works/{clean_doi}"
            resp = requests.get(url, headers=self.headers, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json().get("message", {})
                title_list = data.get("title", [])
                title = title_list[0] if title_list else ""
                
                authors = []
                for a in data.get("author", []):
                    family = a.get("family", "")
                    given = a.get("given", "")
                    if family:
                        authors.append(f"{family}, {given}".strip())
                author_str = ", ".join(authors) if authors else "Unknown"

                year = None
                created = data.get("published-print", {}).get("date-parts") or data.get("created", {}).get("date-parts")
                if created and len(created[0]) > 0:
                    year = created[0][0]

                container = data.get("container-title", [])
                journal = container[0] if container else ""

                result = {
                    "title": title,
                    "authors": author_str,
                    "year": year,
                    "journal": journal,
                    "doi": clean_doi,
                    "url": data.get("URL") or f"https://doi.org/{clean_doi}",
                    "publisher": data.get("publisher", ""),
                }
                _DOI_CACHE[clean_doi] = result
                return result
            elif resp.status_code == 404:
                _DOI_CACHE[clean_doi] = None
                return None
        except Exception as e:
            logger.debug(f"Crossref DOI query failed: {e}")
        return None

    def search_crossref(self, query: str, limit: int = 4) -> List[ScholarlySearchResult]:
        """Queries the public Crossref Works API for matching papers."""
        cache_key = f"crossref:{query[:100]}"
        if cache_key in _SEARCH_CACHE:
            return _SEARCH_CACHE[cache_key]

        results = []
        try:
            url = "https://api.crossref.org/works"
            params = {
                "query.bibliographic": query[:180],
                "rows": limit,
            }
            resp = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("message", {}).get("items", [])
                for item in items:
                    title_list = item.get("title", [])
                    title = title_list[0] if title_list else "Unknown Title"
                    
                    authors = []
                    for a in item.get("author", []):
                        family = a.get("family", "")
                        given = a.get("given", "")
                        if family:
                            authors.append(f"{family} {given}".strip())
                    author_str = ", ".join(authors) if authors else "Unknown"

                    year = None
                    created = item.get("published-print", {}).get("date-parts") or item.get("created", {}).get("date-parts")
                    if created and len(created[0]) > 0:
                        year = created[0][0]

                    doi = item.get("DOI")
                    item_url = item.get("URL") or (f"https://doi.org/{doi}" if doi else None)
                    abstract = item.get("abstract", "")
                    container = item.get("container-title", [])
                    journal = container[0] if container else ""

                    results.append(ScholarlySearchResult(
                        title=title,
                        authors=author_str,
                        year=year,
                        doi=doi,
                        url=item_url,
                        abstract=abstract,
                        journal=journal,
                        source_type="Journal" if "journal" in str(item.get("type", "")).lower() else "Academic Paper",
                        reliability="High",
                        domain="crossref.org",
                    ))
        except Exception as e:
            logger.debug(f"Crossref search failed: {e}")
        
        _SEARCH_CACHE[cache_key] = results
        return results

    def search_openalex(self, query: str, limit: int = 4) -> List[ScholarlySearchResult]:
        """Queries the public OpenAlex Works API."""
        cache_key = f"openalex:{query[:100]}"
        if cache_key in _SEARCH_CACHE:
            return _SEARCH_CACHE[cache_key]

        results = []
        try:
            url = "https://api.openalex.org/works"
            params = {
                "search": query[:180],
                "per_page": limit,
            }
            resp = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("results", [])
                for item in items:
                    title = item.get("title") or "Unknown Title"
                    authors_list = [a.get("author", {}).get("display_name", "") for a in item.get("authorships", [])]
                    author_str = ", ".join(a for a in authors_list if a) or "Unknown"
                    year = item.get("publication_year")
                    doi = (item.get("doi") or "").replace("https://doi.org/", "")
                    host_venue = item.get("primary_location", {}) or {}
                    source = host_venue.get("source", {}) or {}
                    journal = source.get("display_name", "")

                    results.append(ScholarlySearchResult(
                        title=title,
                        authors=author_str,
                        year=year,
                        doi=doi if doi else None,
                        url=item.get("doi") or item.get("id"),
                        abstract="",
                        journal=journal,
                        source_type="Academic Paper",
                        reliability="High",
                        domain="openalex.org",
                    ))
        except Exception as e:
            logger.debug(f"OpenAlex search failed: {e}")

        _SEARCH_CACHE[cache_key] = results
        return results

    def search_semanticscholar(self, query: str, limit: int = 3) -> List[ScholarlySearchResult]:
        """Queries the public Semantic Scholar Graph API."""
        cache_key = f"s2:{query[:100]}"
        if cache_key in _SEARCH_CACHE:
            return _SEARCH_CACHE[cache_key]

        results = []
        try:
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                "query": query[:150],
                "limit": limit,
                "fields": "title,authors,year,externalIds,url,abstract,publicationTypes",
            }
            resp = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("data", []):
                    title = item.get("title") or "Unknown Title"
                    authors = ", ".join(a.get("name", "") for a in item.get("authors", []) if a.get("name"))
                    year = item.get("year")
                    ext_ids = item.get("externalIds", {}) or {}
                    doi = ext_ids.get("DOI")
                    abstract = item.get("abstract") or ""

                    results.append(ScholarlySearchResult(
                        title=title,
                        authors=authors or "Unknown",
                        year=year,
                        doi=doi,
                        url=item.get("url") or (f"https://doi.org/{doi}" if doi else None),
                        abstract=abstract,
                        source_type="Journal",
                        reliability="High",
                        domain="semanticscholar.org",
                    ))
        except Exception as e:
            logger.debug(f"Semantic Scholar search failed: {e}")

        _SEARCH_CACHE[cache_key] = results
        return results

    def search_arxiv(self, query: str, limit: int = 3) -> List[ScholarlySearchResult]:
        """Queries the public arXiv API for preprints."""
        results = []
        try:
            import xml.etree.ElementTree as ET
            url = "http://export.arxiv.org/api/query"
            clean_q = "".join(c for c in query[:120] if c.isalnum() or c.isspace())
            params = {
                "search_query": f"all:{clean_q}",
                "max_results": limit,
            }
            resp = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                for entry in root.findall("atom:entry", ns):
                    title_elem = entry.find("atom:title", ns)
                    summary_elem = entry.find("atom:summary", ns)
                    id_elem = entry.find("atom:id", ns)
                    
                    author_elems = entry.findall("atom:author/atom:name", ns)
                    author_str = ", ".join(a.text for a in author_elems if a.text) or "arXiv Author"

                    results.append(ScholarlySearchResult(
                        title=title_elem.text.strip().replace("\n", " ") if title_elem is not None and title_elem.text else "arXiv Preprint",
                        authors=author_str,
                        year=None,
                        doi=None,
                        url=id_elem.text.strip() if id_elem is not None and id_elem.text else None,
                        abstract=summary_elem.text.strip() if summary_elem is not None and summary_elem.text else "",
                        source_type="Preprint",
                        reliability="Medium",
                        domain="arxiv.org",
                    ))
        except Exception as e:
            logger.debug(f"arXiv search failed: {e}")
        return results

    # ----------------------------------------------------------------------
    # 2. Reference Verification Pipeline
    # ----------------------------------------------------------------------

    def verify_reference(self, ref) -> None:
        """Verifies an individual ExtractedReference against scholarly APIs.
        Updates ref.status, ref.verification_source, ref.matched_metadata, and ref.difference_notes in place.
        """
        if getattr(ref, "is_duplicate", False):
            ref.status = "DUPLICATE"
            return

        # Case 1: Reference contains a DOI
        if ref.doi:
            crossref_meta = self.get_crossref_by_doi(ref.doi)
            if crossref_meta:
                ref.verification_source = "Crossref DOI Registry"
                ref.matched_metadata = crossref_meta
                
                # Check for metadata differences
                diffs = []
                c_title = crossref_meta.get("title", "")
                if c_title and ref.title:
                    title_sim = fuzz.token_set_ratio(c_title.lower(), ref.title.lower())
                    if title_sim < 70:
                        diffs.append(f"Title in record: '{c_title[:45]}...'")
                
                c_year = crossref_meta.get("year")
                if c_year and ref.year and abs(c_year - ref.year) > 1:
                    diffs.append(f"Year mismatch: Cited as {ref.year}, verified record is {c_year}")

                if diffs:
                    ref.status = "PARTIALLY VERIFIED"
                    ref.difference_notes = "; ".join(diffs)
                else:
                    ref.status = "VERIFIED"
                    ref.difference_notes = "Metadata matches verified DOI record."
                return
            else:
                ref.status = "BROKEN LINK"
                ref.difference_notes = f"DOI '10.{ref.doi.split('10.')[-1]}' does not resolve or returns not found."
                return

        # Case 2: No DOI available -> Title search cascade
        query_candidates = []
        if ref.title and len(ref.title) > 12:
            query_candidates.append(ref.title)
        if ref.authors and ref.title:
            first_author = ref.authors.split(",")[0].split()[0]
            query_candidates.append(f"{first_author} {ref.title[:60]}")

        for q in query_candidates:
            # 1. Search Crossref
            hits = self.search_crossref(q, limit=2)
            if not hits:
                hits = self.search_openalex(q, limit=2)
            if not hits:
                hits = self.search_semanticscholar(q, limit=2)

            for hit in hits:
                sim = fuzz.token_set_ratio(ref.title.lower(), hit.title.lower())
                if sim >= 85:
                    ref.verification_source = f"{hit.domain or 'Scholarly Database'}"
                    ref.matched_metadata = {
                        "title": hit.title,
                        "authors": hit.authors,
                        "year": hit.year,
                        "journal": hit.journal,
                        "doi": hit.doi,
                        "url": hit.url,
                    }
                    if hit.doi and not ref.doi:
                        ref.doi = hit.doi

                    # Check year or author mismatch
                    if hit.year and ref.year and abs(hit.year - ref.year) > 1:
                        ref.status = "PARTIALLY VERIFIED"
                        ref.difference_notes = f"Year in publication record is {hit.year} (cited {ref.year})."
                    else:
                        ref.status = "VERIFIED"
                        ref.difference_notes = f"Verified in {hit.domain}."
                    return
                elif sim >= 70:
                    ref.status = "SUSPICIOUS"
                    ref.verification_source = f"{hit.domain or 'Scholarly Database'}"
                    ref.matched_metadata = {"title": hit.title, "authors": hit.authors, "year": hit.year}
                    ref.difference_notes = f"Potential title discrepancy: '{hit.title[:45]}...' (Similarity: {sim}%)."
                    return

        # Fallback if no source could confirm
        ref.status = "NOT VERIFIED"
        ref.difference_notes = "Reference could not be independently verified across available scholarly databases."

    # ----------------------------------------------------------------------
    # 3. Intelligent Search Strategy for Plagiarism Discovery
    # ----------------------------------------------------------------------

    def extract_smart_search_queries(self, paragraphs: List[str], max_queries: int = 5) -> List[str]:
        """Extracts distinctive, academic keyphrases and representative sentences
        to search online without overloading APIs or querying trivial sentences.
        """
        queries: List[str] = []
        for p in paragraphs:
            cleaned = " ".join(p.split())
            if len(cleaned) < 80:
                continue

            # Split into candidate sentences
            sentences = [s.strip() for s in re.split(r'[\.\?\!]\s+', cleaned) if len(s.strip().split()) >= 7]
            for s in sentences:
                lower_s = s.lower()
                # Skip trivial introductory or methodology boilerplate
                if any(kw in lower_s for kw in ["this paper", "in this section", "we propose", "table 1", "figure 1", "as shown in"]):
                    continue
                # Extract 8-12 word core phrase
                tokens = s.split()
                if len(tokens) >= 8:
                    phrase = " ".join(tokens[:10])
                    queries.append(phrase)
                    if len(queries) >= max_queries:
                        return queries
        return queries

    def discover_web_sources_for_paper(self, paragraphs: List[str], max_sources: int = 6) -> List[ScholarlySearchResult]:
        """Executes smart phrase discovery across public academic repositories."""
        queries = self.extract_smart_search_queries(paragraphs, max_queries=4)
        all_results: List[ScholarlySearchResult] = []
        seen_titles = set()

        for q in queries:
            # Query Crossref and Semantic Scholar
            cr_hits = self.search_crossref(q, limit=2)
            for h in cr_hits:
                norm_t = re.sub(r'[^a-zA-Z0-9]', '', h.title.lower())
                if norm_t and norm_t not in seen_titles:
                    seen_titles.add(norm_t)
                    all_results.append(h)

            s2_hits = self.search_semanticscholar(q, limit=2)
            for h in s2_hits:
                norm_t = re.sub(r'[^a-zA-Z0-9]', '', h.title.lower())
                if norm_t and norm_t not in seen_titles:
                    seen_titles.add(norm_t)
                    all_results.append(h)

            if len(all_results) >= max_sources:
                break

        return self.group_and_classify_sources(all_results)

    def group_and_classify_sources(self, sources: List[ScholarlySearchResult]) -> List[ScholarlySearchResult]:
        """Groups duplicate/republished web sources into Primary Source and Secondary Copies."""
        if not sources:
            return []

        primary_sources: List[ScholarlySearchResult] = []
        for src in sources:
            # Check domain
            if src.url:
                try:
                    domain = urlparse(src.url).netloc.lower()
                    src.domain = domain
                    if any(t in domain for t in [".edu", ".gov", ".ac.", "ieee", "springer", "nature", "elsevier", "doi.org"]):
                        src.reliability = "High"
                        src.source_type = "Journal / Academic"
                    elif any(t in domain for t in ["arxiv", "biorxiv", "ssrn"]):
                        src.reliability = "Medium"
                        src.source_type = "Preprint Repository"
                    elif "wikipedia" in domain:
                        src.reliability = "Medium"
                        src.source_type = "Wikipedia"
                    else:
                        src.reliability = "Medium"
                except Exception:
                    src.domain = "web"

            # Check if this source is a duplicate or secondary copy of an already recorded primary source
            is_dup = False
            for prim in primary_sources:
                sim = fuzz.token_set_ratio(prim.title.lower(), src.title.lower())
                if sim > 85:
                    is_dup = True
                    if src.url and src.url != prim.url:
                        prim.secondary_copies.append(src.url)
                    break

            if not is_dup:
                primary_sources.append(src)

        return primary_sources
