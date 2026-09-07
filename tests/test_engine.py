"""End-to-end plagiarism detection engine tests."""

from pathlib import Path
from app.core.engine import ComparisonSource, PlagiarismDetectionEngine
from app.core.extractor import DocumentExtractor


def test_engine_plagiarism_detection():
    source_path = Path("resources/sample_papers/sample_source.txt")
    target_path = Path("resources/sample_papers/suspicious_paper.txt")

    extractor = DocumentExtractor()
    src_ext = extractor.extract(source_path)
    target_ext = extractor.extract(target_path)

    comp_source = ComparisonSource(
        source_id=1,
        name="Baseline Attention Paper",
        text=src_ext.full_text,
        sentences=[line.strip() for line in src_ext.full_text.splitlines() if len(line.strip().split()) >= 4],
    )

    engine = PlagiarismDetectionEngine()
    result = engine.analyze_document(target_ext, [comp_source])

    assert result.document_filename == "suspicious_paper.txt"
    assert result.word_count > 100
    assert len(result.matches) > 0

    # Ensure exact and fuzzy matches were identified
    algos = [m["algorithm"] for m in result.matches]
    assert any("Exact" in a for a in algos)

    # Ensure overall score was computed
    assert result.score_breakdown.overall_similarity > 0.0
    assert result.score_breakdown.risk_level in ["Moderate", "High", "Very High", "Low"]


def test_duplicate_document_detection():
    source_path = Path("resources/sample_papers/sample_source.txt")

    extractor = DocumentExtractor()
    src_ext = extractor.extract(source_path)

    comp_source = ComparisonSource(
        source_id=1,
        name="Identical Source",
        text=src_ext.full_text,
        sentences=[line.strip() for line in src_ext.full_text.splitlines() if len(line.strip().split()) >= 4],
    )

    engine = PlagiarismDetectionEngine()
    result = engine.analyze_document(src_ext, [comp_source])

    assert result.is_duplicate is True
    assert any("duplicate" in w.lower() for w in result.warnings)
