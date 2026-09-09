"""Comprehensive Test Suite for Research Paper Plagiarism & Reference Verification System.
Validates all 12 core academic scenarios:
1. Completely original paper
2. Exact copied paragraph
3. Copied paragraph with citation
4. Proper quotation (Quoted + Cited)
5. Paraphrased copied paragraph
6. Common academic language filtering
7. Fake / unverifiable reference
8. Correct DOI verification
9. Wrong DOI / Metadata mismatch
10. Unused reference detection
11. Missing citation detection
12. Offline mode execution
"""

import pytest
from app.core.citations import CitationAnalyzer, CitationMatch
from app.core.common_phrases import is_common_academic_phrase
from app.core.engine import ComparisonSource, PlagiarismDetectionEngine
from app.core.extractor import ExtractedDocument, PageData, ParagraphUnit
from app.core.reference_parser import ExtractedReference, ReferenceParser
from app.core.scoring import ScoringEngine
from app.web.search import ScholarlySearchEngine


def make_doc(text: str, filename: str = "paper.pdf") -> ExtractedDocument:
    words = text.split()
    page = PageData(page_number=1, text=text, char_start=0, char_end=len(text), word_count=len(words))
    para = ParagraphUnit(paragraph_id=1, page_number=1, text=text, char_start=0, char_end=len(text))
    return ExtractedDocument(
        filepath=filename,
        filename=filename,
        file_hash="hash_" + str(abs(hash(text))),
        full_text=text,
        pages=[page],
        paragraphs=[para],
        word_count=len(words),
        page_count=1,
    )


# --------------------------------------------------------------------------
# TEST 1: Completely Original Paper
# --------------------------------------------------------------------------
def test_1_completely_original_paper():
    text = (
        "In this innovative study, we present a distinct empirical method for measuring "
        "energy harvesting efficiency in micro-scale piezoelectric cantilevers under "
        "ambient rotational oscillations. The proposed design features non-linear mechanical "
        "coupling and novel multi-frequency resonant tuning mechanisms."
    )
    doc = make_doc(text)
    sources = [
        ComparisonSource(
            source_id=1,
            name="Existing Paper on Solar Panels",
            text="Solar photovoltaic cells convert solar irradiation directly into electrical energy through silicon p-n junctions.",
            sentences=["Solar photovoltaic cells convert solar irradiation directly into electrical energy through silicon p-n junctions."],
        )
    ]
    engine = PlagiarismDetectionEngine(settings={"enable_web_search": False})
    result = engine.analyze_document(doc, sources)

    assert result.score_breakdown.overall_similarity < 5.0
    assert result.score_breakdown.risk_level in ["Very Low", "Low"]
    assert result.score_breakdown.academic_verdict == "LOW CONCERN"


# --------------------------------------------------------------------------
# TEST 2: Exact Copied Paragraph
# --------------------------------------------------------------------------
def test_2_exact_copied_paragraph():
    copied_passage = (
        "Artificial intelligence has significantly transformed modern healthcare systems "
        "by enabling early diagnosis of chronic ailments and optimizing hospital clinical workflows."
    )
    doc = make_doc(copied_passage)
    sources = [
        ComparisonSource(
            source_id=2,
            name="Smith et al. 2023",
            text=copied_passage,
            sentences=[copied_passage],
            url="https://doi.org/10.1000/182",
        )
    ]
    engine = PlagiarismDetectionEngine(settings={"enable_web_search": False})
    result = engine.analyze_document(doc, sources)

    assert len(result.matches) >= 1
    m = result.matches[0]
    assert m["algorithm"] == "Exact Match"
    assert m["similarity_score"] == 100.0
    assert m["confidence"] == "High"
    assert "No Citation" in m["match_category"]


# --------------------------------------------------------------------------
# TEST 3: Copied Paragraph with Citation
# --------------------------------------------------------------------------
def test_3_copied_paragraph_with_citation():
    source_sentence = (
        "Convolutional neural networks achieve state-of-the-art performance in complex radiological pattern identification."
    )
    paper_text = f"{source_sentence} [1]"
    doc = make_doc(paper_text)
    sources = [
        ComparisonSource(
            source_id=3,
            name="RadNet 2022",
            text=source_sentence,
            sentences=[source_sentence],
        )
    ]
    engine = PlagiarismDetectionEngine(settings={"enable_web_search": False})
    result = engine.analyze_document(doc, sources)

    assert len(result.matches) >= 1
    m = result.matches[0]
    # Recognizes presence of citation
    assert m.get("is_cited", False) is True
    assert "Cited" in m["match_category"]


# --------------------------------------------------------------------------
# TEST 4: Proper Quotation (Quoted + Cited)
# --------------------------------------------------------------------------
def test_4_proper_quotation():
    quoted_text = (
        'According to the lead investigator, "quantum computing architectures will revolutionize cryptographic resilience within the next decade" [2].'
    )
    doc = make_doc(quoted_text)
    sources = [
        ComparisonSource(
            source_id=4,
            name="Quantum Review",
            text="Quantum computing architectures will revolutionize cryptographic resilience within the next decade.",
            sentences=["Quantum computing architectures will revolutionize cryptographic resilience within the next decade."],
        )
    ]
    engine = PlagiarismDetectionEngine(settings={"enable_web_search": False, "exclude_quotes": True})
    result = engine.analyze_document(doc, sources)

    # Quotations are excluded from uncredited plagiarism
    assert result.score_breakdown.quoted_count >= 1
    assert result.score_breakdown.overall_similarity < 10.0


# --------------------------------------------------------------------------
# TEST 5: Paraphrased Copied Paragraph
# --------------------------------------------------------------------------
def test_5_paraphrased_paragraph():
    original_source = (
        "Machine learning models can assist medical practitioners in identifying hidden tumors within diagnostic scans."
    )
    paraphrased_paper = (
        "Machine learning models assist medical doctors in identifying hidden tumors in diagnostic scans."
    )
    doc = make_doc(paraphrased_paper)
    sources = [
        ComparisonSource(
            source_id=5,
            name="Diagnostic ML",
            text=original_source,
            sentences=[original_source],
        )
    ]
    engine = PlagiarismDetectionEngine(settings={"enable_web_search": False, "fuzzy_similarity_threshold": 75.0})
    result = engine.analyze_document(doc, sources)

    assert len(result.matches) >= 1
    m = result.matches[0]
    assert m["algorithm"] in ["Fuzzy Match", "Semantic Similarity", "Exact Match"]
    assert m["similarity_score"] >= 75.0


# --------------------------------------------------------------------------
# TEST 6: Common Academic Language
# --------------------------------------------------------------------------
def test_6_common_academic_language():
    phrases = [
        "In this study, the results indicate that the experimental hypothesis is validated.",
        "The purpose of this research is to investigate the parameters.",
        "As shown in Table 1, the data reveals significant trends.",
    ]
    for p in phrases:
        cleaned = " ".join(p.lower().split())
        assert is_common_academic_phrase(cleaned) is True


# --------------------------------------------------------------------------
# TEST 7: Fake / Unverifiable Reference
# --------------------------------------------------------------------------
def test_7_fake_unverifiable_reference():
    searcher = ScholarlySearchEngine()
    fake_ref = ExtractedReference(
        ref_number=99,
        raw_text="FakeAuthorXYZ, Z. (2099). Impossible Nonexistent Teleportation Paper 99999. Imaginary Journal.",
        title="Impossible Nonexistent Teleportation Paper 99999",
        authors="FakeAuthorXYZ, Z.",
        year=2099,
    )
    searcher.verify_reference(fake_ref)
    assert fake_ref.status == "NOT VERIFIED"
    assert "could not be independently verified" in fake_ref.difference_notes


# --------------------------------------------------------------------------
# TEST 8: Correct DOI Verification
# --------------------------------------------------------------------------
def test_8_correct_doi_verification(monkeypatch):
    searcher = ScholarlySearchEngine()

    # Mock Crossref DOI lookup to test verification pipeline without external network latency
    def mock_get_doi(doi):
        return {
            "title": "Deep Residual Learning for Image Recognition",
            "authors": "He, Kaiming",
            "year": 2016,
            "journal": "CVPR",
            "doi": "10.1109/cvpr.2016.90",
        }

    monkeypatch.setattr(searcher, "get_crossref_by_doi", mock_get_doi)

    ref = ExtractedReference(
        ref_number=1,
        raw_text="K. He et al., Deep Residual Learning for Image Recognition, 2016, DOI: 10.1109/CVPR.2016.90",
        title="Deep Residual Learning for Image Recognition",
        authors="He, K.",
        year=2016,
        doi="10.1109/cvpr.2016.90",
    )
    searcher.verify_reference(ref)
    assert ref.status == "VERIFIED"
    assert "Crossref" in ref.verification_source


# --------------------------------------------------------------------------
# TEST 9: Wrong DOI / Metadata Mismatch
# --------------------------------------------------------------------------
def test_9_metadata_mismatch(monkeypatch):
    searcher = ScholarlySearchEngine()

    def mock_get_doi(doi):
        return {
            "title": "Deep Residual Learning for Image Recognition",
            "authors": "He, Kaiming",
            "year": 2016,
            "journal": "CVPR",
            "doi": "10.1109/cvpr.2016.90",
        }

    monkeypatch.setattr(searcher, "get_crossref_by_doi", mock_get_doi)

    # User cites year 2024 instead of 2016
    ref = ExtractedReference(
        ref_number=2,
        raw_text="K. He, Deep Residual Learning, 2024, DOI: 10.1109/CVPR.2016.90",
        title="Deep Residual Learning",
        authors="He, K.",
        year=2024,
        doi="10.1109/cvpr.2016.90",
    )
    searcher.verify_reference(ref)
    assert ref.status in ["PARTIALLY VERIFIED", "SUSPICIOUS"]
    assert "Year mismatch" in ref.difference_notes or "mismatch" in ref.difference_notes.lower()


# --------------------------------------------------------------------------
# TEST 10: Unused Reference Detection
# --------------------------------------------------------------------------
def test_10_unused_reference_detection():
    analyzer = CitationAnalyzer()
    body_text = "We evaluate the neural model on the benchmark dataset [1]."
    citations = [CitationMatch(text="[1]", citation_type="IEEE", start_char=54, end_char=57)]
    references = [
        ExtractedReference(ref_number=1, raw_text="[1] Cited Source A", title="Cited Source A"),
        ExtractedReference(ref_number=2, raw_text="[2] Completely Unused Source B", title="Completely Unused Source B"),
    ]

    issues, missing, unused, mismatch = analyzer.cross_check_citations_with_references(
        citations=citations,
        references=references,
        body_text=body_text,
    )
    assert unused >= 1
    unused_issues = [i for i in issues if i.issue_type == "Unused Reference"]
    assert len(unused_issues) == 1
    assert unused_issues[0].ref_number == 2


# --------------------------------------------------------------------------
# TEST 11: Missing Citation Detection
# --------------------------------------------------------------------------
def test_11_missing_citation_detection():
    analyzer = CitationAnalyzer()
    body_text = "Prior research by investigators [15] demonstrates rapid convergence."
    citations = [CitationMatch(text="[15]", citation_type="IEEE", start_char=32, end_char=36)]
    # Only references 1 through 5 exist
    references = [
        ExtractedReference(ref_number=i, raw_text=f"[{i}] Source {i}", title=f"Source {i}")
        for i in range(1, 6)
    ]

    issues, missing, unused, mismatch = analyzer.cross_check_citations_with_references(
        citations=citations,
        references=references,
        body_text=body_text,
    )
    assert missing >= 1
    missing_issues = [i for i in issues if i.issue_type == "Missing Reference"]
    assert len(missing_issues) == 1
    assert missing_issues[0].ref_number == 15


# --------------------------------------------------------------------------
# TEST 12: Offline Mode Execution
# --------------------------------------------------------------------------
def test_12_offline_mode_execution():
    text = "This paper presents autonomous drone navigation using onboard optical sensors."
    doc = make_doc(text)
    engine = PlagiarismDetectionEngine(settings={"enable_web_search": False})
    
    # Run with empty comparison sources in offline mode
    result = engine.analyze_document(doc, comparison_sources=[])
    assert result.sources_compared_count == 0
    assert result.score_breakdown.academic_verdict == "INCONCLUSIVE"
    assert "Insufficient" in result.score_breakdown.verdict_summary
