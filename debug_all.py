"""
Comprehensive debug test suite for IMRD ResearchGuard.
Uses EJ1105539.pdf as the test document.
Run: python -X utf8 debug_all.py
"""

import sys, os, traceback, tempfile, inspect
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

TEST_PDF = str(ROOT / "EJ1105539.pdf")
PASS = "[PASS]"
FAIL = "[FAIL]"

results = []

def section(title):
    print(f"\n{'='*64}\n  {title}\n{'='*64}")

def check(name, ok, detail=""):
    icon = PASS if ok else FAIL
    results.append((name, ok))
    print(f"  {icon}  {name}")
    if detail:
        for line in str(detail).strip().split("\n")[:8]:
            print(f"         {line}")

def run(name, fn):
    try:
        result = fn()
        check(name, True, result if isinstance(result, str) else "")
        return result
    except Exception as e:
        check(name, False, traceback.format_exc())
        return None


# ═══════════════════════════════════════════════════════════
# 1. CONFIG
# ═══════════════════════════════════════════════════════════
section("1. IMPORTS & CONFIG")
config = run("Import app.config", lambda: __import__("app.config", fromlist=["*"]))
if config:
    check("APP_TITLE defined",    bool(getattr(config, "APP_TITLE", None)), getattr(config, "APP_TITLE", ""))
    check("DATABASE_URL defined", bool(getattr(config, "DATABASE_URL", None)))
    check("CACHE_DIR exists",     Path(str(getattr(config, "CACHE_DIR", ""))).exists(),
          str(getattr(config, "CACHE_DIR", "")))
    check("TEST_PDF exists",      Path(TEST_PDF).exists(), TEST_PDF)


# ═══════════════════════════════════════════════════════════
# 2. DATABASE
# ═══════════════════════════════════════════════════════════
section("2. DATABASE & SESSION")
dbs = run("Import app.database.session", lambda: __import__("app.database.session", fromlist=["*"]))
if dbs:
    run("init_db()", lambda: (dbs.init_db(), "OK")[1])
    run("get_all_settings()", lambda: f"{len(dbs.get_all_settings())} settings loaded")

    def _rtrip():
        dbs.set_setting("_dbg_key", "hello")
        v = dbs.get_setting("_dbg_key")
        assert v == "hello", f"Got {v!r}"
        return f"round-trip OK: {v!r}"
    run("set_setting / get_setting round-trip", _rtrip)

    run("get_all_documents()", lambda: f"{len(dbs.get_all_documents(limit=10))} doc(s) in DB")
    run("get_all_sources()",   lambda: f"{len(dbs.get_all_sources())} source(s) in DB")

    def _cert():
        c = dbs.generate_certificate_number()
        assert c.startswith("IMRD/"), f"Bad cert: {c}"
        return f"cert={c}"
    run("generate_certificate_number()", _cert)

    def _dash():
        m = dbs.get_dashboard_metrics()
        assert isinstance(m, dict) and "total_docs" in m
        return f"total_docs={m['total_docs']}, avg_sim={m.get('avg_similarity',0)}"
    run("get_dashboard_metrics()", _dash)


# ═══════════════════════════════════════════════════════════
# 3. DOCUMENT EXTRACTOR
# ═══════════════════════════════════════════════════════════
section("3. DOCUMENT EXTRACTOR")
from app.core.extractor import DocumentExtractor

extracted = None
try:
    ext = DocumentExtractor()
    extracted = ext.extract(TEST_PDF)
    check("PDF extraction returns ExtractedDocument", True, type(extracted).__name__)
    check("full_text populated",  bool(extracted.full_text), f"{len(extracted.full_text)} chars")
    check("word_count > 100",     extracted.word_count > 100,     f"word_count={extracted.word_count}")
    check("page_count > 0",       extracted.page_count > 0,       f"page_count={extracted.page_count}")
    check("file_hash present",    bool(extracted.file_hash),      f"hash={extracted.file_hash[:16]}...")
    check("not encrypted",        not extracted.is_encrypted)
    check("pages list populated", len(extracted.pages) > 0,       f"{len(extracted.pages)} page(s)")
except Exception as e:
    check("PDF extraction", False, traceback.format_exc())


# ═══════════════════════════════════════════════════════════
# 4. PREPROCESSOR
# ═══════════════════════════════════════════════════════════
section("4. TEXT PREPROCESSOR")
from app.core.preprocessor import TextPreprocessor

def _preproc():
    pp = TextPreprocessor()
    sample = ("The research methodology adopted in this study is quantitative. "
              "We analyzed 200 samples from various academic sources.")
    sentences = pp.split_sentences(sample)
    assert len(sentences) >= 1, "No sentences"
    cleaned = pp.normalize_text(sample)
    assert cleaned, "Cleaned text empty"
    return f"sentences={len(sentences)}, normalized_len={len(cleaned)}"
run("TextPreprocessor.split_sentences() + normalize_text()", _preproc)

def _pdf_sentences():
    if not extracted: return "skipped — no extracted text"
    pp = TextPreprocessor()
    sentences = pp.split_sentences(extracted.full_text[:5000])
    return f"{len(sentences)} sentences from PDF first 5000 chars"
run("split_sentences() on PDF content", _pdf_sentences)

def _preproc_pages():
    if not extracted: return "skipped"
    pp = TextPreprocessor()
    doc = pp.preprocess_pages(extracted.pages)
    return f"PreprocessedDocument: {len(doc.sentences)} sentences, {doc.total_words} words"
preprocessed = None
try:
    pp = TextPreprocessor()
    if extracted:
        preprocessed = pp.preprocess_pages(extracted.pages)
        check("preprocess_pages() on PDF pages", True,
              f"{len(preprocessed.sentences)} sentences, {preprocessed.word_count} words")
except Exception as e:
    check("preprocess_pages()", False, traceback.format_exc())



# ═══════════════════════════════════════════════════════════
# 5. STRUCTURE ANALYSER
# ═══════════════════════════════════════════════════════════
section("5. STRUCTURE ANALYSER")
from app.core.structure import StructureAnalyzer

def _structure():
    if not extracted: return "skipped"
    ana = StructureAnalyzer()
    struct = ana.analyze(extracted.full_text[:8000])
    assert isinstance(struct, dict)
    return f"sections found: {list(struct.keys())[:6]}"
run("StructureAnalyzer.analyze() on PDF", _structure)


# ═══════════════════════════════════════════════════════════
# 6. CITATION DETECTOR
# ═══════════════════════════════════════════════════════════
section("6. CITATION DETECTOR")
from app.core.citations import CitationAnalyzer

def _citations():
    cd = CitationAnalyzer()
    sample = ('This approach was proposed by Smith et al. (2020). '
              'As noted in [1], results were significant. '
              '"Education is key" (Jones, 2019, p. 45). See also [2,3].')
    result = cd.analyze(sample)
    return (f"citations={result.citation_count}, refs={result.reference_count}, "
            f"quotes={len(result.quotes or [])}")
run("CitationAnalyzer.analyze()", _citations)

def _cite_pdf():
    if not extracted: return "skipped"
    cd = CitationAnalyzer()
    result = cd.analyze(extracted.full_text)
    return (f"PDF citations={result.citation_count}, "
            f"refs={result.reference_count}, quotes={len(result.quotes or [])}")
run("CitationAnalyzer on full PDF", _cite_pdf)


# ═══════════════════════════════════════════════════════════
# 7. AI WRITING DETECTOR
# ═══════════════════════════════════════════════════════════
section("7. AI WRITING DETECTOR")
from app.core.ai_detector import AIWritingDetector

def _ai():
    det = AIWritingDetector()
    sample = "This study investigates the impact of artificial intelligence on educational outcomes in higher education institutions."
    result = det.analyze(sample)
    return f"likelihood={result.likelihood}, score={result.score:.2f}"
run("AIWritingDetector.analyze() — human sample", _ai)

def _ai_pdf():
    if not extracted: return "skipped"
    det = AIWritingDetector()
    result = det.analyze(extracted.full_text[:3000])
    return f"PDF AI likelihood={result.likelihood}, score={result.score:.2f}"
run("AIWritingDetector on PDF text", _ai_pdf)


# ═══════════════════════════════════════════════════════════
# 8. SCORING ENGINE
# ═══════════════════════════════════════════════════════════
section("8. SCORING ENGINE")
from app.core.scoring import ScoringEngine

def _scoring():
    scorer = ScoringEngine()
    mock_matches = [
        {"similarity_score": 85.0, "algorithm": "Exact",    "is_quoted": False, "is_ignored": False},
        {"similarity_score": 72.0, "algorithm": "Fuzzy",    "is_quoted": False, "is_ignored": False},
        {"similarity_score": 91.0, "algorithm": "Semantic", "is_quoted": True,  "is_ignored": False},
        {"similarity_score": 68.0, "algorithm": "Exact",    "is_quoted": False, "is_ignored": True},
    ]
    result = scorer.calculate_score(
        total_document_words=500,
        matches=mock_matches,
        exclude_quotes=True,
        exclude_references=True,
    )
    return (f"overall={result.overall_similarity:.1f}%, risk={result.risk_level}, "
            f"exact_count={result.exact_count}")
run("ScoringEngine.calculate_score()", _scoring)



# ═══════════════════════════════════════════════════════════
# 9. PLAGIARISM ENGINE — END-TO-END
# ═══════════════════════════════════════════════════════════
section("9. PLAGIARISM ENGINE (end-to-end on PDF)")
from app.core.engine import PlagiarismDetectionEngine, ComparisonSource

def _engine():
    if not extracted:
        return "skipped — no extracted PDF"
    engine = PlagiarismDetectionEngine()
    # Use first 1500 chars of PDF as a comparison source (guarantees real matches)
    excerpt = extracted.full_text[:1500]
    sources = [
        ComparisonSource(
            source_id=1,
            name="Self-Reference Test Source",
            text=excerpt,
            sentences=[s.strip() for s in excerpt.split(".") if len(s.strip().split()) >= 4],
            author="Test Author",
            source_type="Journal",
        )
    ]
    sig = inspect.signature(engine.analyze)
    params = list(sig.parameters.keys())
    print(f"         engine.analyze() params: {params}")
    result = engine.analyze(TEST_PDF, sources, settings={})
    return (f"similarity={result.score_breakdown.overall_similarity:.1f}%, "
            f"matches={len(result.matches)}, "
            f"risk={result.score_breakdown.risk_level}, "
            f"words={result.score_breakdown.total_analyzed_words}")
engine_result = None
try:
    if extracted:
        engine = PlagiarismDetectionEngine()
        excerpt = extracted.full_text[:1500]
        sources = [ComparisonSource(
            source_id=1, name="Self-Reference Test",
            text=excerpt,
            sentences=[s.strip() for s in excerpt.split(".") if len(s.strip().split()) >= 4],
            author="Test", source_type="Journal",
        )]
        engine_result = engine.analyze_document(
            extracted=extracted,
            comparison_sources=sources,
        )
        check("PlagiarismDetectionEngine.analyze_document()", True,
              f"similarity={engine_result.score_breakdown.overall_similarity:.1f}%, "
              f"matches={len(engine_result.matches)}, risk={engine_result.score_breakdown.risk_level}")
        check("Result has score_breakdown", hasattr(engine_result, "score_breakdown"))
        check("Result has matches list",    isinstance(engine_result.matches, list))
        check("Matches > 0 (self-match)",   len(engine_result.matches) > 0,
              f"{len(engine_result.matches)} matches found")
except Exception as e:
    check("PlagiarismDetectionEngine.analyze_document()", False, traceback.format_exc())



# ═══════════════════════════════════════════════════════════
# 10. REPORT GENERATORS
# ═══════════════════════════════════════════════════════════
section("10. REPORT GENERATORS")
from app.reports.pdf_generator import PDFReportGenerator
from app.reports.html_generator import HTMLReportGenerator
from app.core.scoring import ScoreBreakdown

def _make_mock():
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
        word_count = extracted.word_count if extracted else 3500
        page_count = extracted.page_count if extracted else 10
        extracted_text = (extracted.full_text[:1000] if extracted else "Sample text.")
        score_breakdown = ScoreBreakdown(
            overall_similarity=18.5, risk_level="Low",
            exact_percentage=8.0, fuzzy_percentage=6.5,
            semantic_percentage=4.0, quoted_percentage=2.0,
            total_analyzed_words=word_count, matched_words=647,
            exact_count=12, fuzzy_count=9, semantic_count=6, quoted_count=3,
            ignored_count=0, explanation="Debug test run."
        )
        matches = [
            {"sentence": "This study analyzes AI impact on education.",
             "matched_text": "This study analyzes AI impact on education.",
             "similarity_score": 95.0, "algorithm": "Exact",
             "source_name": "Test Journal", "page_number": 1,
             "is_quoted": False, "is_cited": False, "is_ignored": False}
        ]
        student_name = "Krunal Patil"
        prn_number   = "2023MCA001"
        course_name  = "MCA"
        academic_year = "2025-2026"
        semester      = "Semester IV"
        guide_name    = "Dr. R. K. Sharma"
        paper_title   = "Impact of AI on Educational Assessment"
        clearance_status = "Approved (Level 0)"
        certificate_no   = "IMRD/LIB/PLAG/2026/0001"
        structure = {}
        citations = MockCit()
        ai_writing = MockAI()
    return MockResult()

mock_result = _make_mock()

def _pdf_report():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        out = f.name
    gen = PDFReportGenerator(out)
    doc_data = {
        "filename": mock_result.document_filename,
        "student_name": mock_result.student_name,
        "prn_number": mock_result.prn_number,
        "course_name": mock_result.course_name,
        "academic_year": mock_result.academic_year,
        "semester": mock_result.semester,
        "guide_name": mock_result.guide_name,
        "paper_title": mock_result.paper_title,
        "clearance_status": mock_result.clearance_status,
        "certificate_no": mock_result.certificate_no,
        "word_count": mock_result.word_count,
        "page_count": mock_result.page_count,
        "file_hash": mock_result.file_hash,
    }
    sb = mock_result.score_breakdown
    score_data = {
        "overall_similarity": sb.overall_similarity,
        "risk_level": sb.risk_level,
        "exact_percentage": sb.exact_percentage,
        "fuzzy_percentage": sb.fuzzy_percentage,
        "semantic_percentage": sb.semantic_percentage,
        "quoted_percentage": sb.quoted_percentage,
        "total_analyzed_words": sb.total_analyzed_words,
        "matched_words": sb.matched_words,
        "exact_count": sb.exact_count,
        "fuzzy_count": sb.fuzzy_count,
        "semantic_count": sb.semantic_count,
        "quoted_count": sb.quoted_count,
        "ignored_count": sb.ignored_count,
        "explanation": sb.explanation,
    }
    result_path = gen.generate_report(doc_data, score_data, mock_result.matches)
    size = Path(str(result_path)).stat().st_size
    assert size > 1000, f"PDF too small: {size}"
    return f"PDF OK: {size//1024} KB at {result_path}"
run("PDFReportGenerator.generate_report()", _pdf_report)

def _html_report():
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
        out = f.name
    gen = HTMLReportGenerator(out)
    doc_data = {
        "filename": mock_result.document_filename,
        "student_name": mock_result.student_name,
        "prn_number": mock_result.prn_number,
        "course_name": mock_result.course_name,
        "academic_year": mock_result.academic_year,
        "semester": mock_result.semester,
        "guide_name": mock_result.guide_name,
        "paper_title": mock_result.paper_title,
        "clearance_status": mock_result.clearance_status,
        "certificate_no": mock_result.certificate_no,
        "word_count": mock_result.word_count,
        "page_count": mock_result.page_count,
        "file_hash": mock_result.file_hash,
    }
    sb = mock_result.score_breakdown
    score_data = {
        "overall_similarity": sb.overall_similarity, "risk_level": sb.risk_level,
        "exact_percentage": sb.exact_percentage, "fuzzy_percentage": sb.fuzzy_percentage,
        "semantic_percentage": sb.semantic_percentage, "quoted_percentage": sb.quoted_percentage,
        "total_analyzed_words": sb.total_analyzed_words, "matched_words": sb.matched_words,
        "exact_count": sb.exact_count, "fuzzy_count": sb.fuzzy_count,
        "semantic_count": sb.semantic_count, "quoted_count": sb.quoted_count,
        "ignored_count": sb.ignored_count, "explanation": sb.explanation,
    }
    cit_data = {
        "citation_count": 3, "reference_count": 5,
        "quotes": [], "uncited_claims": 1,
    }
    struct_data = {}
    result_path = gen.generate_report(doc_data, score_data, mock_result.matches, cit_data, struct_data)
    size = Path(str(result_path)).stat().st_size
    assert size > 500, f"HTML too small: {size}"
    return f"HTML OK: {size//1024} KB at {result_path}"
run("HTMLReportGenerator.generate_report()", _html_report)



# ═══════════════════════════════════════════════════════════
# 11. THEME
# ═══════════════════════════════════════════════════════════
section("11. THEME (non-GUI check)")

def _theme():
    from app.ui.theme import get_theme_stylesheet
    css = get_theme_stylesheet()
    assert "#21a7d0" in css, "RCPIMRD teal missing"
    assert "#273c66" in css, "RCPIMRD navy missing"
    src = open("app/ui/theme.py").read()
    assert "DARK_THEME" not in src, "DARK_THEME still present!"
    return f"CSS={len(css)} chars, RCPIMRD palette confirmed, no DARK_THEME"
run("RCPIMRD theme / no dark mode", _theme)


# ═══════════════════════════════════════════════════════════
# 12. SPLASH ASSETS
# ═══════════════════════════════════════════════════════════
section("12. SPLASH SCREEN & ASSETS")

def _splash():
    from app.ui.splash import AnimatedSplash
    assets = ["resources/splash_bg.jpg", "resources/kirigen_watermark.jpg",
              "resources/app_icon.png"]
    found, missing = [], []
    for a in assets:
        (found if Path(a).exists() else missing).append(a)
    if missing:
        raise FileNotFoundError(f"Missing: {missing}")
    return f"AnimatedSplash importable | assets: {found}"
run("Splash module + all assets", _splash)


# ═══════════════════════════════════════════════════════════
# 13. MAIN WINDOW STATIC CHECKS
# ═══════════════════════════════════════════════════════════
section("13. MAIN WINDOW (static checks)")

def _mw_stale():
    src = open("app/ui/main_window.py").read()
    issues = []
    if "theme_changed" in src:   issues.append("stale theme_changed")
    if "theme_btn"     in src:   issues.append("stale theme_btn")
    if "def _toggle_theme" in src: issues.append("stale _toggle_theme method")
    if issues: raise AssertionError("; ".join(issues))
    return "No stale dark-mode references"
run("main_window.py — no stale dark-mode code", _mw_stale)

def _sv_stale():
    src = open("app/ui/views/settings_view.py").read()
    issues = []
    if "theme_combo"   in src: issues.append("stale theme_combo")
    if "theme_changed" in src: issues.append("stale theme_changed")
    if issues: raise AssertionError("; ".join(issues))
    return "No dark-mode artifacts"
run("settings_view.py — no dark-mode artifacts", _sv_stale)

def _session_detached():
    src = open("app/database/session.py").read()
    assert "expunge_all()" in src, "Missing expunge_all() fix"
    assert "expire_on_commit=False" in src, "Missing expire_on_commit=False"
    return "DetachedInstanceError fix present"
run("session.py — DetachedInstanceError fix", _session_detached)


# ═══════════════════════════════════════════════════════════
# 14. ANALYSIS WORKER
# ═══════════════════════════════════════════════════════════
section("14. ANALYSIS WORKER (import check)")

def _worker():
    from app.ui.workers.analysis_worker import AnalysisWorker
    sig = inspect.signature(AnalysisWorker.__init__)
    params = list(sig.parameters.keys())
    return f"AnalysisWorker.__init__ params: {params}"
run("AnalysisWorker importable + signature", _worker)


# ═══════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════
section("FINAL SUMMARY")
total  = len(results)
passed = sum(1 for _, ok in results if ok)
failed = total - passed

print(f"\n  Total:  {total}")
print(f"  Passed: {passed}  [PASS]")
print(f"  Failed: {failed}  [FAIL]")

if failed:
    print("\n  FAILED TESTS:")
    for name, ok in results:
        if not ok:
            print(f"    * {name}")

print()
sys.exit(0 if failed == 0 else 1)
