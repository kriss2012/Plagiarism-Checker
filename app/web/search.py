"""Modular, privacy-respecting academic web search module.
Uses legitimate public scholarly APIs (Crossref, arXiv) with explicit user consent.
Strictly disabled by default in Offline Mode.
"""

from dataclasses import dataclass
from typing import List, Optional
import requests
from app.utils.logger import logger


@dataclass
class ScholarlySearchResult:
    title: str
    authors: str
    year: Optional[int]
    doi: Optional[str]
    url: Optional[str]
    abstract: str
    source_type: str = "Web Academic"


class ScholarlySearchEngine:
    """Queries legitimate public scholarly APIs for academic paper metadata and abstracts."""

    def __init__(self, timeout: int = 8):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "ResearchGuardAcademicChecker/1.0 (mailto:support@researchguard.local)"
        }

    def search_crossref(self, query: str, limit: int = 5) -> List[ScholarlySearchResult]:
        """Queries the public Crossref Works API for matching papers."""
        results = []
        try:
            url = "https://api.crossref.org/works"
            params = {
                "query.bibliographic": query[:200],
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
                            authors.append(f"{given} {family}".strip())
                    author_str = ", ".join(authors) if authors else "Unknown"

                    year = None
                    created = item.get("published-print", {}).get("date-parts") or item.get("created", {}).get("date-parts")
                    if created and len(created[0]) > 0:
                        year = created[0][0]

                    doi = item.get("DOI")
                    item_url = item.get("URL") or (f"https://doi.org/{doi}" if doi else None)
                    abstract = item.get("abstract", "")

                    results.append(ScholarlySearchResult(
                        title=title,
                        authors=author_str,
                        year=year,
                        doi=doi,
                        url=item_url,
                        abstract=abstract,
                        source_type="Crossref Journal/Conference",
                    ))
        except Exception as e:
            logger.warning(f"Crossref search query failed or timed out: {e}")
        return results

    def search_arxiv(self, query: str, limit: int = 5) -> List[ScholarlySearchResult]:
        """Queries the public arXiv API for matching preprints."""
        results = []
        try:
            import xml.etree.ElementTree as ET
            url = "http://export.arxiv.org/api/query"
            clean_q = "".join(c for c in query[:150] if c.isalnum() or c.isspace())
            params = {
                "search_query": f"all:{clean_q}",
                "max_results": limit,
            }
            resp = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                for entry in root.findall("atom:entry", ns):
                    title = entry.find("atom:title", ns)
                    summary = entry.find("atom:summary", ns)
                    id_elem = entry.find("atom:id", ns)
                    
                    author_elems = entry.findall("atom:author/atom:name", ns)
                    author_str = ", ".join(a.text for a in author_elems if a.text) or "arXiv Author"

                    results.append(ScholarlySearchResult(
                        title=title.text.strip().replace("\n", " ") if title is not None and title.text else "arXiv Preprint",
                        authors=author_str,
                        year=None,
                        doi=None,
                        url=id_elem.text.strip() if id_elem is not None and id_elem.text else None,
                        abstract=summary.text.strip() if summary is not None and summary.text else "",
                        source_type="arXiv Preprint",
                    ))
        except Exception as e:
            logger.warning(f"arXiv search query failed or timed out: {e}")
        return results
