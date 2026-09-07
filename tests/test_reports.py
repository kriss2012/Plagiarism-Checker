"""Tests for PDF (ReportLab) and HTML report generation."""

from pathlib import Path
from app.reports.html_generator import HTMLReportGenerator
from app.reports.pdf_generator import PDFReportGenerator


def test_pdf_report_generation(tmp_path):
    pdf_out = tmp_path / "test_report.pdf"
    gen = PDFReportGenerator(pdf_out)

    doc_data = {
        "filename": "quantum_computing.pdf",
        "hash": "a1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f90",
        "word_count": 3400,
        "page_count": 8,
    }

    score_dict = {
        "overall_similarity": 28.5,
        "risk_level": "Moderate",
        "exact_percentage": 12.0,
        "exact_count": 4,
        "fuzzy_percentage": 10.5,
        "fuzzy_count": 6,
        "semantic_percentage": 6.0,
        "semantic_count": 3,
        "quoted_percentage": 4.0,
        "quoted_count": 2,
        "ignored_count": 0,
    }

    matches = [
        {
            "sentence": "Quantum supremacy represents a milestone in algorithmic acceleration.",
            "matched_text": "Quantum supremacy represents a milestone in computational acceleration.",
            "similarity_score": 92.0,
            "algorithm": "Fuzzy Match",
            "page_number": 2,
            "source_name": "Nature Physics (2023)",
        }
    ]

    cit_dict = {
        "citation_count": 14,
        "reference_count": 22,
        "quotes": [],
        "uncited_claims": 2,
    }

    structure_dict = {
        "Abstract": {"detected": True},
        "Introduction": {"detected": True},
        "Methodology": {"detected": True},
        "Results": {"detected": True},
        "Conclusion": {"detected": True},
        "References": {"detected": True},
    }

    meta = {
        "institution": "Stanford University",
        "department": "Applied Physics",
        "researcher": "Alex Doe",
        "supervisor": "Dr. Sarah Connor",
        "title": "Quantum Algorithmic Speedups",
    }

    res_path = gen.generate_report(doc_data, score_dict, matches, cit_dict, structure_dict, metadata=meta)
    assert res_path.exists()
    assert res_path.stat().st_size > 1000


def test_html_report_generation(tmp_path):
    html_out = tmp_path / "test_report.html"
    gen = HTMLReportGenerator(html_out)

    doc_data = {"filename": "paper.pdf", "word_count": 1500}
    score_dict = {
        "overall_similarity": 15.0,
        "risk_level": "Low",
        "exact_count": 1,
        "fuzzy_count": 2,
        "semantic_count": 1,
        "quoted_count": 0,
    }

    res_path = gen.generate_report(doc_data, score_dict, [], {}, {})
    assert res_path.exists()
    content = res_path.read_text(encoding="utf-8")
    assert "ResearchGuard" in content
    assert "15.0%" in content
