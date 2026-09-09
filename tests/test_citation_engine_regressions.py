"""Additional Regression Tests for Plagiarism Detection & Citation Engine.
Validates the 10 critical regression requirements specified in the verification specification:
1. Exact copied text without citation (Match exists + high risk).
2. Exact copied text with citation (Match exists + cited status).
3. Exact copied text with quotation + citation (Match exists + quotation/citation recognized).
4. Paraphrased text with citation (Semantic match exists + cited status).
5. Common phrase with unique technical content (Not completely ignored).
6. Citation after sentence (Citation associated with preceding sentence).
7. Multiple citations (Correct citation extraction).
8. Citation range (e.g., [1–4]).
9. Author-year citation (e.g., (Smith et al., 2024)).
10. No citation (No false citation detection).
"""

import pytest
from app.core.citations import CitationAnalyzer
from app.core.common_phrases import is_common_academic_phrase
from app.core.engine import ComparisonSource, PlagiarismDetectionEngine
from app.core.extractor import ExtractedDocument, PageData, ParagraphUnit


def make_doc(text: str, filename: str = "test_paper.pdf") -> ExtractedDocument:
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


# 1. Exact copied text without citation -> Match exists + high risk
def test_reg_1_exact_copied_no_citation():
    text = "Deep learning architectures have revolutionized image classification and feature discovery."
    doc = make_doc(text)
    sources = [
        ComparisonSource(
            source_id=101,
            name="DL Benchmark",
            text=text,
            sentences=[text],
        )
    ]
    engine = PlagiarismDetectionEngine(settings={"enable_web_search": False})
    result = engine.analyze_document(doc, sources)

    assert len(result.matches) >= 1
    m = result.matches[0]
    assert m["algorithm"] == "Exact Match"
    assert m.get("is_cited", False) is False
    assert "No Citation" in m["match_category"]
    assert result.score_breakdown.high_risk_similarity > 0


# 2. Exact copied text with citation -> Match exists + cited status
def test_reg_2_exact_copied_with_citation():
    source_text = "Transformers utilize self-attention mechanisms to dynamically capture long-range contextual relationships."
    paper_text = f"{source_text} [1]"
    doc = make_doc(paper_text)
    sources = [
        ComparisonSource(
            source_id=102,
            name="Attention Is All You Need",
            text=source_text,
            sentences=[source_text],
        )
    ]
    engine = PlagiarismDetectionEngine(settings={"enable_web_search": False})
    result = engine.analyze_document(doc, sources)

    assert len(result.matches) >= 1
    m = result.matches[0]
    assert m["algorithm"] == "Exact Match"
    assert m.get("is_cited", False) is True
    assert "Cited" in m["match_category"]


# 3. Exact copied text with quotation + citation -> Match exists + quotation/citation recognized
def test_reg_3_exact_copied_with_quotation_and_citation():
    source_text = "Quantum superposition enables exponential speedups in solving complex combinatoric optimization problems."
    paper_text = f'According to modern physics, "{source_text}" [4].'
    doc = make_doc(paper_text)
    sources = [
        ComparisonSource(
            source_id=103,
            name="Quantum Computing 101",
            text=source_text,
            sentences=[source_text],
        )
    ]
    engine = PlagiarismDetectionEngine(settings={"enable_web_search": False, "exclude_quotes": True})
    result = engine.analyze_document(doc, sources)

    assert len(result.matches) >= 1
    m = result.matches[0]
    assert m.get("is_quoted", False) is True
    assert m.get("is_cited", False) is True
    assert "Quoted + Cited" in m["match_category"]


# 4. Paraphrased text with citation -> Semantic match exists + cited status
def test_reg_4_paraphrased_text_with_citation():
    source_text = "Reinforcement learning from human feedback significantly enhances the safety and conversational alignment of large language models."
    paraphrased = "RL from human feedback greatly improves conversational safety and alignment in language models. [5]"
    doc = make_doc(paraphrased)
    sources = [
        ComparisonSource(
            source_id=104,
            name="RLHF Alignment Paper",
            text=source_text,
            sentences=[source_text],
        )
    ]
    engine = PlagiarismDetectionEngine(settings={"enable_web_search": False, "fuzzy_similarity_threshold": 70.0})
    result = engine.analyze_document(doc, sources)

    assert len(result.matches) >= 1
    m = result.matches[0]
    assert m.get("is_cited", False) is True
    assert "Cited" in m["match_category"]


# 5. Common phrase with unique technical content -> Not completely ignored
def test_reg_5_common_phrase_with_unique_technical_content():
    unique_claim = (
        "In this study, we introduce our proprietary algorithm called RadNet-X900, "
        "which achieves 97.3% accuracy on the XYZ radiological benchmark dataset."
    )
    # The detector must recognize that despite "In this study", substantial unique material is present
    assert is_common_academic_phrase(unique_claim) is False

    doc = make_doc(unique_claim)
    sources = [
        ComparisonSource(
            source_id=105,
            name="RadNet-X900 Report",
            text=unique_claim,
            sentences=[unique_claim],
        )
    ]
    engine = PlagiarismDetectionEngine(settings={"enable_web_search": False, "filter_common_phrases": True})
    result = engine.analyze_document(doc, sources)

    # Must NOT be skipped as common boilerplate
    assert len(result.matches) >= 1
    assert result.matches[0]["similarity_score"] == 100.0


# 6. Citation after sentence -> Citation associated with preceding sentence
def test_reg_6_citation_after_sentence():
    sentence = "CRISPR-Cas9 enables precise genome editing across diverse mammalian cell lines."
    doc_text = f"{sentence}. [12] Following this, subsequent tests confirmed targeting fidelity."
    doc = make_doc(doc_text)
    sources = [
        ComparisonSource(
            source_id=106,
            name="Gene Editing Journal",
            text=sentence,
            sentences=[sentence],
        )
    ]
    engine = PlagiarismDetectionEngine(settings={"enable_web_search": False})
    result = engine.analyze_document(doc, sources)

    assert len(result.matches) >= 1
    m = result.matches[0]
    assert m.get("is_cited", False) is True


# 7. Multiple citations -> Correct citation extraction
def test_reg_7_multiple_citations():
    text = "Several prior studies have explored this exact mechanism [1, 2, 7]."
    analyzer = CitationAnalyzer()
    res = analyzer.analyze(text)

    assert res.citation_count >= 1
    c_texts = [c.text for c in res.citations]
    assert any("[1, 2, 7]" in ct for ct in c_texts)


# 8. Citation range -> Example: [1–4]
def test_reg_8_citation_range():
    text = "Comprehensive overviews are provided in several surveys [1-4] and monographs [5–8]."
    analyzer = CitationAnalyzer()
    res = analyzer.analyze(text)

    assert res.citation_count >= 2
    c_texts = [c.text for c in res.citations]
    assert any("[1-4]" in ct for ct in c_texts)
    assert any("[5–8]" in ct or "[5-8]" in ct for ct in c_texts)


# 9. Author-year citation -> Example: (Smith et al., 2024)
def test_reg_9_author_year_citation():
    text = "Earlier work demonstrated this effect in high-latitude environments (Smith et al., 2024)."
    analyzer = CitationAnalyzer()
    res = analyzer.analyze(text)

    assert res.citation_count >= 1
    assert any("Smith et al., 2024" in c.text for c in res.citations)


# 10. No citation -> No false citation detection
def test_reg_10_no_citation():
    text = "The experimental observations were conducted over three consecutive months without deviations."
    analyzer = CitationAnalyzer()
    res = analyzer.analyze(text)

    assert res.citation_count == 0
    assert len(res.citations) == 0

    doc = make_doc(text)
    sources = [
        ComparisonSource(
            source_id=110,
            name="Lab Notes",
            text=text,
            sentences=[text],
        )
    ]
    engine = PlagiarismDetectionEngine(settings={"enable_web_search": False})
    result = engine.analyze_document(doc, sources)

    assert len(result.matches) >= 1
    assert result.matches[0].get("is_cited", False) is False
