"""Tests for paper structure section detection."""

from app.core.structure import StructureAnalyzer


def test_section_boundary_detection():
    paper_text = """
    Title: Analysis of Neural Networks
    
    Abstract
    This is the abstract text describing the experiment.
    
    Introduction
    Neural networks have revolutionized artificial intelligence and data science.
    
    Methodology
    We train a feedforward model on standard benchmark datasets.
    
    Results
    The accuracy achieved was 98.4 percent on validation data.
    
    Conclusion
    In conclusion, our results demonstrate strong performance.
    
    References
    [1] Author, A. (2020). Deep Learning Foundations.
    """

    analyzer = StructureAnalyzer()
    sections = analyzer.analyze(paper_text)

    assert sections["Abstract"].detected is True
    assert sections["Introduction"].detected is True
    assert sections["Methodology"].detected is True
    assert sections["Results"].detected is True
    assert sections["Conclusion"].detected is True
    assert sections["References"].detected is True

    # Test references boundary offset check
    ref_start = sections["References"].start_char
    assert ref_start > 0
    assert analyzer.is_in_references(ref_start + 10, sections) is True
    assert analyzer.is_in_references(ref_start - 50, sections) is False
