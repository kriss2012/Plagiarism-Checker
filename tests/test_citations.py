"""Tests for citation detection, quotation parsing, and exclusion boundaries."""

from app.core.citations import CitationAnalyzer


def test_ieee_and_author_year_citations():
    text = (
        "Previous algorithms suffered from memory constraints [1]. "
        "As established by Vaswani et al. (2017), self-attention mitigates this limitation. "
        "For additional details, see DOI: 10.1109/5.771073 and (Johnson & Smith, 2022)."
    )

    analyzer = CitationAnalyzer()
    res = analyzer.analyze(text)

    assert res.citation_count >= 3
    types = [c.citation_type for c in res.citations]
    assert "IEEE" in types
    assert "Author-Year" in types
    assert "DOI" in types


def test_quote_extraction():
    text = (
        'The authors explicitly stated: "Our proposed architecture calculates attention weights '
        'using scaled dot-product formulation" (Vaswani et al., 2017).'
    )

    analyzer = CitationAnalyzer()
    res = analyzer.analyze(text)

    assert len(res.quotes) >= 1
    assert "scaled dot-product" in res.quotes[0].text
    # Should detect adjacent citation
    assert res.quotes[0].has_adjacent_citation is True
