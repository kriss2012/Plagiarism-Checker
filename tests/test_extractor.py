"""Tests for document text extraction from TXT and structure formatting."""

from pathlib import Path
import pytest
from app.core.extractor import DocumentExtractor


def test_txt_extraction():
    sample_file = Path("resources/sample_papers/sample_source.txt")
    extractor = DocumentExtractor()
    extracted = extractor.extract(sample_file)

    assert extracted.filename == "sample_source.txt"
    assert extracted.word_count > 100
    assert len(extracted.pages) >= 1
    assert "Attention Mechanisms" in extracted.full_text
    assert extracted.file_hash != ""


def test_pdf_extraction():
    pdf_file = Path("resources/sample_papers/test_sample.pdf")
    extractor = DocumentExtractor()
    extracted = extractor.extract(pdf_file)

    assert extracted.filename == "test_sample.pdf"
    assert extracted.word_count > 10
    assert len(extracted.pages) == 1
    assert "Sample Generated PDF" in extracted.full_text


def test_docx_extraction():
    docx_file = Path("resources/sample_papers/test_sample.docx")
    extractor = DocumentExtractor()
    extracted = extractor.extract(docx_file)

    assert extracted.filename == "test_sample.docx"
    assert extracted.word_count > 10
    assert "Sample Generated Word" in extracted.full_text
    assert "Accuracy | 99%" in extracted.full_text


def test_file_not_found():
    extractor = DocumentExtractor()
    with pytest.raises(FileNotFoundError):
        extractor.extract("non_existent_file.pdf")


def test_unsupported_extension():
    fake_file = Path("test_unsupported.xyz")
    fake_file.write_text("dummy")
    extractor = DocumentExtractor()
    try:
        with pytest.raises(ValueError):
            extractor.extract(fake_file)
    finally:
        fake_file.unlink(missing_ok=True)
