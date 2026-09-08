"""
Comprehensive debug test suite for IMRD ResearchGuard.
Tests every major subsystem using EJ1105539.pdf as the test document.
Run: python debug_all.py
"""

import sys
import os
import traceback
from pathlib import Path

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Add project root to path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

TEST_PDF = str(ROOT / "EJ1105539.pdf")

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

results = []

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def check(name, ok, detail=""):
    icon = PASS if ok else FAIL
    results.append((name, ok))
    print(f"  {icon}  {name}")
    if detail:
        for line in str(detail).split("\n")[:6]:
            print(f"         {line}")

def run(name, fn):
    try:
        result = fn()
        check(name, True, result if isinstance(result, str) else "")
        return result
    except Exception as e:
        check(name, False, traceback.format_exc())
        return None


# ══════════════════════════════════════════════════════════════
# 1. IMPORTS & CONFIG
# ══════════════════════════════════════════════════════════════
section("1. IMPORTS & CONFIG")

config = run("Import app.config", lambda: __import__("app.config", fromlist=["*"]))
if config:
    check("APP_TITLE defined",    bool(getattr(config, "APP_TITLE", None)))
    check("DATABASE_URL defined", bool(getattr(config, "DATABASE_URL", None)))
    check("CACHE_DIR exists",     Path(getattr(config, "CACHE_DIR", "")).exists())


# ══════════════════════════════════════════════════════════════
# 2. DATABASE
# ══════════════════════════════════════════════════════════════
section("2. DATABASE & SESSION")

db_session = run("Import app.database.session", lambda: __import__("app.database.session", fromlist=["*"]))

if db_session:
    run("init_db()", lambda: db_session.init_db())
    
    run("get_all_settings()", lambda: db_session.get_all_settings())
    
    def test_set_get():
        db_session.set_setting("_debug_test_key", "hello_world")
        val = db_session.get_setting("_debug_test_key")
        assert val == "hello_world", f"Got {val!r}"
        return f"round-trip value: {val!r}"
    run("set_setting / get_setting round-trip", test_set_get)
    
    def test_docs():
        docs = db_session.get_all_documents(limit=10)
        return f"{len(docs)} document(s) in DB"
    run("get_all_documents()", test_docs)
    
    def test_sources():
        srcs = db_session.get_all_sources()
        return f"{len(srcs)} source(s) in DB"
    run("get_all_sources()", test_sources)
    
    def test_cert():
        c = db_session.generate_certificate_number()
        assert c.startswith("IMRD/"), f"Bad cert: {c}"
        return f"cert: {c}"
    run("generate_certificate_number()", test_cert)
    
    def test_dashboard():
        m = db_session.get_dashboard_metrics()
        assert isinstance(m, dict)
        assert "total_docs" in m
        return f"total_docs={m['total_docs']}, avg_sim={m.get('avg_similarity',0)}"
    run("get_dashboard_metrics()", test_dashboard)


# ══════════════════════════════════════════════════════════════
# 3. DOCUMENT EXTRACTOR
# ══════════════════════════════════════════════════════════════
section("3. DOCUMENT EXTRACTOR")

from app.core.extractor import DocumentExtractor

def test_pdf_extract():
    ext = DocumentExtractor()
    result = ext.extract(TEST_PDF)
    assert result.text, "No text extracted"
    wc = len(result.text.split())
    return f"words={wc}, pages={result.page_count}, lang={result.language}"

extracted_result = None
try:
    ext = DocumentExtractor()
    extracted_result = ext.extract(TEST_PDF)
    check("PDF text extraction", bool(extracted_result.text), f"words={len(extracted_result.text.split())}")
    check("Page count detected",  extracted_result.page_count > 0, f"pages={extracted_result.page_count}")
    check("Language detected",    bool(extracted_result.language), f"lang={extracted_result.language}")
    check("Word count > 100",     len(extracted_result.text.split()) > 100)
except Exception as e:
    check("PDF text extraction", False, traceback.format_exc())


# ══════════════════════════════════════════════════════════════
# 4. PREPROCESSOR
# ══════════════════════════════════════════════════════════════
section("4. TEXT PREPROCESSOR")

from app.core.preprocessor import TextPreprocessor

def test_preproc():
    pp = TextPreprocessor()
    sample = "The research methodology adopted in this study is quantitative. We analyzed 200 samples from various sources."
    sentences = pp.extract_sentences(sample)
    assert len(sentences) >= 1, "No sentences extracted"
    cleaned = pp.clean_text(sample)
    assert cleaned, "Cleaned text empty"
    return f"sentences={len(sentences)}, cleaned_len={len(cleaned)}"

run("TextPreprocessor.extract_sentences()", test_preproc)

def test_pdf_sentences():
    if not extracted_result:
        return "skipped (no extracted text)"
    pp = TextPreprocessor()
    sentences = pp.extract_sentences(extracted_result.text[:5000])
    return f"{len(sentences)} sentences from PDF first 5000 chars"
run("Sentence extraction from PDF", test_pdf_sentences)


# ══════════════════════════════════════════════════════════════
# 5. DOCUMENT STRUCTURE ANALYSER
# ══════════════════════════════════════════════════════════════
section("5. STRUCTURE ANALYSER")

from app.core.structure import DocumentStructureAnalyzer

def test_structure():
    if not extracted_result:
        return "skipped"
    ana = DocumentStructureAnalyzer()
    struct = ana.analyze(extracted_result.text[:8000])
    assert isinstance(struct, dict)
    return f"sections={list(struct.keys())[:5]}"
run("DocumentStructureAnalyzer.analyze()", test_structure)


# ══════════════════════════════════════════════════════════════
# 6. CITATION DETECTOR
# ══════════════════════════════════════════════════════════════
section("6. CITATION DETECTOR")

from app.core.citations import CitationDetector

def test_citations():
    cd = CitationDetector()
    sample = ('This approach was proposed by Smith et al. (2020). '
              'As noted in [1], the results were significant. '
              '"Education is the key to success" (Jones, 2019, p. 45).')
    result = cd.detect(sample)
    return (f"citations={result.citation_count}, "
            f"refs={result.reference_count}, "
            f"quotes={len(result.quotes or [])}")
run("CitationDetector.detect()", test_citations)


# ══════════════════════════════════════════════════════════════
# 7. AI WRITING DETECTOR
# ══════════════════════════════════════════════════════════════
section("7. AI WRITING DETECTOR")

from app.core.ai_detector import AIWritingDetector

def test_ai():
    detector = AIWritingDetector()
    sample = "This study investigates the impact of artificial intelligence on educational outcomes."
    result = detector.analyze(sample)
    return f"likelihood={result.likelihood}, score={result.score:.1f}"
run("AIWritingDetector.analyze()", test_ai)


# ══════════════════════════════════════════════════════════════
# 8. SCORING
# ══════════════════════════════════════════════════════════════
section("8. SCORING ENGINE")

from app.core.scoring import SimilarityScorer

def test_scoring():
    scorer = SimilarityScorer()
    mock_matches = [
        {"similarity_score": 85.0, "algorithm": "Exact",  "is_quoted": False, "is_ignored": False},
        {"similarity_score": 72.0, "algorithm": "Fuzzy",  "is_quoted": False, "is_ignored": False},
        {"similarity_score": 91.0, "algorithm": "Semantic","is_quoted": True,  "is_ignored": False},
    ]
    result = scorer.calculate(mock_matches, total_words=500)
    return (f"overall={result.overall_similarity:.1f}%, "
            f"risk={result.risk_level}, "
            f"exact%={result.exact_percentage:.1f}")
run("SimilarityScorer.calculate()", test_scoring)


# ══════════════════════════════════════════════════════════════
# 9. PLAGIARISM ENGINE (end-to-end on PDF)
# ══════════════════════════════════════════════════════════════
section("9. PLAGIARISM ENGINE (end-to-end)")

from app.core.engine import PlagiarismEngine, ComparisonSource

def test_engine_basic():
    """Engine with a small inline comparison source."""
    engine = PlagiarismEngine()
    if not extracted_result:
        return "skipped — no extracted PDF text"
    
    # Use first 2000 chars of the PDF itself as a comparison source (guarantees matches)
    doc_excerpt = extracted_result.text[:2000]
    sources = [
        ComparisonSource(
            source_id=1,
            name="Self-Reference Test Source",
            text=doc_excerpt,
            sentences=[s.strip() for s in doc_excerpt.split(".") if len(s.strip().split()) >= 4],
            author="Test",
            source_type="Journal",
        )
    ]
    result = engine.analyze(TEST_PDF, sources, settings={})
    return (f"similarity={result.score_breakdown.overall_similarity:.1f}%, "
            f"matches={len(result.matches)}, "
            f"risk={result.score_breakdown.risk_level}")

run("PlagiarismEngine.analyze() — self-match test", test_engine_basic)


# ══════════════════════════════════════════════════════════════
# 10. REPORT GENERATORS
# ══════════════════════════════════════════════════════════════
section("10. REPORT GENERATORS")

import tempfile

from app.reports.pdf_generator import generate_pdf_report
from app.reports.html_generator import generate_html_report

def make_mock_result():
    """Build a minimal mock result object for report generators."""
    from app.core.scoring import ScoreBreakdown
    from dataclasses import dataclass

    @dataclass
    class MockCit:
        citation_count: int = 3
        reference_count: int = 5
        quotes: list = None
        uncited_claims: int = 1
        def __post_init__(self):
            if self.quotes is None: self.quotes = []

    @dataclass
    class MockAI:
        likelihood: str = "Low"
        score: float = 12.5

    class MockResult:
        document_filename = "EJ1105539.pdf"
        file_hash = "abc123def456"
        word_count = 3500
        page_count = 10
        extracted_text = extracted_result.text[:1000] if extracted_result else "Sample text."
        score_breakdown = ScoreBreakdown(
            overall_similarity=18.5, risk_level="Low",
            exact_percentage=8.0, fuzzy_percentage=6.5,
            semantic_percentage=4.0, quoted_percentage=2.0,
            total_analyzed_words=3500, matched_words=647,
            exact_count=12, fuzzy_count=9, semantic_count=6, quoted_count=3,
            ignored_count=0, explanation="Test run."
        )
        matches = [
            {"sentence": "This study analyzes AI impact on education.",
             "matched_text": "This study analyzes AI impact on education.",
             "similarity_score": 95.0, "algorithm": "Exact",
             "source_name": "Test Journal Article",
             "page_number": 1, "is_quoted": False, "is_cited": False, "is_ignored": False}
        ]
        student_name = "Krunal Patil"
        prn_number = "2023MCA001"
        course_name = "MCA"
        academic_year = "2025-2026"
        semester = "Semester IV"
        guide_name = "Dr. R. K. Sharma"
        paper_title = "Impact of AI on Educational Assessment"
        clearance_status = "Approved (Level 0)"
        certificate_no = "IMRD/LIB/PLAG/2026/0001"
        structure = {}
        citations = MockCit()
        ai_writing = MockAI()

    return MockResult()

mock_result = make_mock_result()

def test_pdf_report():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        out_path = f.name
    generate_pdf_report(mock_result, out_path)
    size = Path(out_path).stat().st_size
    assert size > 1000, f"PDF too small: {size} bytes"
    return f"PDF generated: {size//1024} KB at {out_path}"
run("generate_pdf_report()", test_pdf_report)

def test_html_report():
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        out_path = f.name
    generate_html_report(mock_result, out_path)
    size = Path(out_path).stat().st_size
    assert size > 500, f"HTML too small: {size} bytes"
    return f"HTML generated: {size//1024} KB at {out_path}"
run("generate_html_report()", test_html_report)


# ══════════════════════════════════════════════════════════════
# 11. THEME / UI (non-GUI checks)
# ══════════════════════════════════════════════════════════════
section("11. THEME (non-GUI)")

def test_theme():
    from app.ui.theme import get_theme_stylesheet, RCPIMRD_THEME
    css = get_theme_stylesheet()
    assert "#21a7d0" in css, "RCPIMRD teal missing"
    assert "#273c66" in css, "RCPIMRD navy missing"
    assert "DARK_THEME" not in open("app/ui/theme.py").read(), "DARK_THEME still present"
    return f"CSS length={len(css)} chars, RCPIMRD palette verified"
run("Theme: RCPIMRD palette / no dark mode", test_theme)


# ══════════════════════════════════════════════════════════════
# 12. SPLASH SCREEN (import only)
# ══════════════════════════════════════════════════════════════
section("12. SPLASH SCREEN MODULE")

def test_splash_import():
    from app.ui.splash import AnimatedSplash
    assets = [
        ROOT / "resources" / "splash_bg.jpg",
        ROOT / "resources" / "kirigen_watermark.jpg",
    ]
    missing = [str(a) for a in assets if not a.exists()]
    if missing:
        raise FileNotFoundError(f"Missing assets: {missing}")
    return "AnimatedSplash class importable, all assets present"
run("Splash screen module + assets", test_splash_import)


# ══════════════════════════════════════════════════════════════
# 13. MAIN WINDOW (import-level + signal check)
# ══════════════════════════════════════════════════════════════
section("13. MAIN WINDOW (static checks)")

def test_main_window_src():
    src = open("app/ui/main_window.py").read()
    issues = []
    if "theme_changed" in src:
        issues.append("Stale theme_changed reference found")
    if "_toggle_theme" in src and "def _toggle_theme" in src:
        issues.append("_toggle_theme method still present")
    if "theme_btn" in src:
        issues.append("theme_btn still referenced")
    if issues:
        raise AssertionError("; ".join(issues))
    return "No stale dark-mode references in main_window.py"
run("main_window.py — no stale dark-mode refs", test_main_window_src)

def test_settings_view_src():
    src = open("app/ui/views/settings_view.py").read()
    issues = []
    if "theme_combo" in src:
        issues.append("theme_combo still present in settings_view")
    if "theme_changed" in src:
        issues.append("theme_changed still present in settings_view")
    if issues:
        raise AssertionError("; ".join(issues))
    return "No dark-mode artifacts in settings_view.py"
run("settings_view.py — no dark-mode artifacts", test_settings_view_src)


# ══════════════════════════════════════════════════════════════
# 14. WORKERS
# ══════════════════════════════════════════════════════════════
section("14. ANALYSIS WORKER (import check)")

def test_worker_import():
    from app.ui.workers.analysis_worker import AnalysisWorker
    import inspect
    sig = inspect.signature(AnalysisWorker.__init__)
    params = list(sig.parameters.keys())
    return f"AnalysisWorker.__init__ params: {params}"
run("AnalysisWorker importable", test_worker_import)


# ══════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════
section("SUMMARY")
total  = len(results)
passed = sum(1 for _, ok in results if ok)
failed = total - passed

print(f"\n  Total:  {total}")
print(f"  Passed: {passed}  ✅")
print(f"  Failed: {failed}  ❌")
print()

if failed:
    print("  FAILED TESTS:")
    for name, ok in results:
        if not ok:
            print(f"    • {name}")

print()
sys.exit(0 if failed == 0 else 1)
