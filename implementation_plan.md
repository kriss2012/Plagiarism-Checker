# Implementation Plan: ResearchGuard – Research Paper Plagiarism Checker

ResearchGuard is a complete, professional, production-ready Windows 10/11 64-bit desktop application for academic plagiarism detection, textual similarity analysis, citation/quotation inspection, paper structure recognition, and AI-writing likelihood indicators. The application will be packaged as a standalone Windows executable (`ResearchGuard.exe`) that operates offline-first with zero external dependencies required for the end user.

---

## User Review Required

> [!IMPORTANT]
> **Academic Integrity & Disclaimer Standard**:
> ResearchGuard explicitly reports *"Similarity"* and *"Potential Plagiarism Indicators"*, rather than claiming 100% definitive proof of plagiarism. Final determination requires academic/human review. This disclaimer is displayed in the UI, report cover sheets, and executive summaries.

> [!NOTE]
> **Sentence-Transformers & Offline NLP Model**:
> The application integrates `sentence-transformers` (`all-MiniLM-L6-v2`) for deep semantic paraphrase detection. If the model weights are not pre-downloaded or the user is working completely offline in an air-gapped environment, the engine will gracefully fall back to TF-IDF cosine similarity + RapidFuzz token matching while clearly displaying `NLP Model: Offline/Heuristic Mode` without crashing.

> [!TIP]
> **Standalone Executable Strategy**:
> We will configure PyInstaller to produce a high-performance Windows build with all UI assets, styles, database drivers, and NLP tokenizer data bundled. We will also provide a build script (`build_exe.py`) that handles single-click compilation and generates an Inno Setup installer script for `ResearchGuard_Setup.exe`.

---

## Proposed Architecture & Directory Structure

```
d:\Programs\Poligram\
├── app/
│   ├── __init__.py
│   ├── main.py                     # Application entry point & Qt application lifecycle
│   ├── config.py                   # Constants, directories, user settings schema
│   ├── database/
│   │   ├── __init__.py
│   │   ├── models.py               # SQLAlchemy ORM: Document, Source, Match, Report, Setting
│   │   └── session.py              # SQLite connection manager, migrations, CRUD helpers
│   ├── core/
│   │   ├── __init__.py
│   │   ├── extractor.py            # Text extraction: PDF (PyMuPDF), DOCX (python-docx), TXT; Scanned detection
│   │   ├── preprocessor.py         # Unicode normalization, punctuation/quotes, sentence tokenization
│   │   ├── language.py             # Language identification (English, Hindi, Marathi, etc.)
│   │   ├── structure.py            # Academic structure parser (Abstract, Intro, Lit Review, Methods, Results, Ref)
│   │   ├── citations.py            # Citation detection (APA, IEEE [n], Harvard, DOI, URL, quote isolation)
│   │   ├── ai_detector.py          # Stylometric AI-indicator (perplexity, burstiness, variance heuristics)
│   │   ├── scoring.py              # Transparent weighted composite scoring with exclusions
│   │   ├── common_phrases.py       # Configurable academic cliché filters
│   │   └── engine.py               # Orchestrator: Exact, Fuzzy, N-gram, TF-IDF, Semantic matching
│   ├── ml/
│   │   ├── __init__.py
│   │   └── semantic.py             # SentenceTransformers all-MiniLM-L6-v2 loader & cosine similarity
│   ├── web/
│   │   ├── __init__.py
│   │   └── search.py               # Modular opt-in academic search (Crossref / arXiv / OpenAlex APIs)
│   ├── reports/
│   │   ├── __init__.py
│   │   ├── pdf_generator.py        # ReportLab PDF generator with cover page, charts, tables, disclaimers
│   │   ├── html_generator.py       # Standalone interactive HTML report with match highlights
│   │   └── export.py               # CSV and JSON exporters
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── theme.py                # Modern professional Light & Dark themes, QSS palettes, indigo accents
│   │   ├── main_window.py          # App shell: Top bar, responsive sidebar navigation, stack views
│   │   ├── views/
│   │   │   ├── dashboard_view.py   # Metric cards, similarity distribution, risk levels, recent checks
│   │   │   ├── new_check_view.py   # Drag & drop upload, multi-file queue, text paste modal, depth config
│   │   │   ├── results_view.py     # Similarity gauge, summary breakdown, risk banner, filter tabs
│   │   │   ├── match_viewer_view.py# Side-by-side original vs source viewer, color-coded highlights, inspector
│   │   │   ├── documents_view.py   # Document history table, search, filters, actions (View, Re-run, Export)
│   │   │   ├── source_library_view.py # Source corpus management (Add PDF, DOCX, TXT, DOI, URLs)
│   │   │   ├── settings_view.py    # General, Analysis, Documents, Reports, Web, Privacy tabs
│   │   │   └── help_view.py        # User guide, methodology, academic disclaimer, model status
│   │   ├── widgets/
│   │   │   ├── charts.py           # High-DPI QPainter vector charts: Gauge meter, Bar charts, Donut charts
│   │   │   ├── cards.py            # Dashboard metric cards, status pills, risk badges
│   │   │   ├── highlight_editor.py # Interactive rich-text document viewer with click-to-match inspector
│   │   │   └── file_drop.py        # Modern drag-and-drop file target widget
│   │   └── workers/
│   │       ├── analysis_worker.py  # Background QThread with progress signals (0-100%, stage status, cancel)
│   │       └── report_worker.py    # Background worker for PDF/HTML report export
│   └── utils/
│       ├── __init__.py
│       ├── logger.py               # Rotating file logging to logs/researchguard.log
│       └── security.py             # Path traversal sanitization, SHA-256 hash checks, file limit guards
├── tests/
│   ├── test_extractor.py
│   ├── test_engine.py
│   ├── test_citations.py
│   ├── test_scoring.py
│   └── test_reports.py
├── resources/
│   ├── icons/                      # SVG icons for UI
│   └── sample_papers/              # Sample academic documents for testing
├── ResearchGuard.spec              # PyInstaller executable packaging specification
├── build_exe.py                    # Build script for Windows EXE compilation
├── installer.iss                   # Inno Setup script for installer generation
└── requirements.txt                # Production dependencies
```

---

## Proposed Changes

### Core Engine & Analysis Algorithms

#### [NEW] [extractor.py](file:///d:/Programs/Poligram/app/core/extractor.py)
- **PDF Extraction**: PyMuPDF (`fitz`) page-by-page text extraction with page indices, paragraph boundary detection, and font/layout metadata.
- **DOCX Extraction**: `python-docx` paragraph parsing, headings detection, and table cell extraction.
- **Scanned PDF Detection**: Heuristics to detect zero-text or low-glyph pages with embedded raster images, generating user warnings ("This document appears to contain scanned pages. OCR is required for reliable analysis.").
- **File Integrity & Hashes**: Computes SHA-256 for document file, text, and individual paragraphs for instant duplicate detection.

#### [NEW] [preprocessor.py](file:///d:/Programs/Poligram/app/core/preprocessor.py) & [language.py](file:///d:/Programs/Poligram/app/core/language.py)
- Normalize Unicode (NFKC), standardize smart quotes/dashes, clean control characters while preserving exact character offsets.
- Multi-language segmentation: Multilingual sentence splitting supporting English, Hindi (Devanagari danda `।`), Marathi, and standard Latin punctuation.
- Maintain dual representations: `OriginalDocument` (for highlighting and visual presentation) and `NormalizedDocument` (for mathematical similarity analysis).

#### [NEW] [structure.py](file:///d:/Programs/Poligram/app/core/structure.py) & [citations.py](file:///d:/Programs/Poligram/app/core/citations.py)
- **Section Detection**: Identify Title, Abstract, Keywords, Introduction, Literature Review, Methodology, Results, Discussion, Conclusion, References.
- **Citation Parsing**: Regex engine for IEEE (`[1]`, `[1-3]`), APA/Harvard (`(Smith, 2024)`, `Smith et al. (2023)`), DOIs (`10.xxxx/...`), and web references.
- **Quotation Isolation**: Extract double quotes, single quotes, and block quotes. Content inside quotes with adjacent citations is flagged as *"Quoted / Cited Content"* rather than uncredited plagiarism.
- **Common Phrases Filter**: Filter out common academic boilerplate ("the results of this study indicate", "in conclusion", "this paper presents", etc.) with configurable threshold.

#### [NEW] [engine.py](file:///d:/Programs/Poligram/app/core/engine.py), [scoring.py](file:///d:/Programs/Poligram/app/core/scoring.py), [ai_detector.py](file:///d:/Programs/Poligram/app/core/ai_detector.py)
- **Multi-Method Similarity Engine**:
  1. **Exact Matching**: SHA-256 sentence hashing and rolling n-gram windowing.
  2. **Fuzzy Matching**: RapidFuzz Levenshtein & token ratio with configurable threshold (default 80%).
  3. **N-Gram Similarity**: 3-gram, 5-gram, and 7-gram Jaccard / containment coefficient.
  4. **TF-IDF Cosine Similarity**: Scikit-learn TfidfVectorizer across document chunks and corpus documents.
  5. **Semantic Similarity**: `SentenceTransformer` with cosine similarity (`all-MiniLM-L6-v2`) with graceful offline fallback.
- **Transparent Composite Scoring**:
  $$\text{Score} = \frac{\sum w_i \times \text{MatchedTokens}_i}{\text{TotalAnalyzedTokens}} \times 100$$
  Configurable exclusions: Exclude References section, exclude Quoted/Cited text, exclude Common Academic Phrases.
- **AI-Generated Writing Heuristic**:
  Calculates sentence length variance, burstiness, vocabulary richness (Type-Token Ratio), and repetition entropy. Produces an informative "AI-writing likelihood indicator: Low / Medium / High" accompanied by a prominent warning that stylometrics are probabilistic.

---

### UI & Desktop Experience (PySide6)

#### [NEW] [theme.py](file:///d:/Programs/Poligram/app/ui/theme.py)
- Custom high-contrast modern styling: Dark and Light modes.
- Color palette: Deep navy/slate background, indigo/blue primary accent (`#4F46E5`), emerald green for low similarity (`#10B981`), amber for moderate (`#F59E0B`), rose red for high risk (`#EF4444`).
- Modern typography, rounded cards (`border-radius: 8px`), clean borders, smooth hover animations.

#### [NEW] [widgets/charts.py](file:///d:/Programs/Poligram/app/ui/widgets/charts.py)
- Native PySide6 vector-rendered charts:
  1. **Similarity Gauge / Meter**: Semi-circular speedometer with color gradient (green $\to$ amber $\to$ red) and dynamic needle.
  2. **Risk Distribution Donut Chart**: Proportions of Very Low, Low, Moderate, High, Very High.
  3. **Checks Over Time Bar/Line Chart**: Historical scan trends.
  4. **Source Category Breakdown**: Horizontal progress bars.

#### [NEW] [views/](file:///d:/Programs/Poligram/app/ui/views/)
1. **DashboardView**: High-level KPIs (Total Documents, Average Similarity, High Risk Count, Recent Checks, System Status, NLP Model Status).
2. **NewCheckView**: Drag-and-drop file target, multi-document queue (filename, size, pages, word count, status), direct text paste tab, comparison mode (Local Corpus, History, Opt-in Web), analysis depth slider.
3. **ResultsView**: Executive summary card, overall similarity gauge, risk badge, algorithm breakdown, section structure checklist, citations count, AI likelihood indicator.
4. **MatchViewerView**: Split-screen comparison. Left: Original paper with interactive color-coded highlights (Exact = Red, Fuzzy = Amber, Semantic = Purple, Quoted = Blue). Right: Matched source excerpt, similarity score, algorithm, page, and buttons for Next, Previous, Ignore Match, Open Source.
5. **DocumentsView**: Full searchable history table with filter by risk/date, actions to Re-analyze, Export Report, or Delete.
6. **SourceLibraryView**: Repository for reference books, journal papers, and past submissions against which papers are checked.
7. **SettingsView**: Comprehensive tabs for General, Analysis thresholds, Document filters, Report branding (institution name, guide name, logo), Web search opt-in, and Privacy (Offline mode toggle).
8. **HelpView**: Full documentation, academic plagiarism ethics guide, methodology description, and diagnostic model status.

---

### Database, Reports & Security

#### [NEW] [database/models.py](file:///d:/Programs/Poligram/app/database/models.py) & [session.py](file:///d:/Programs/Poligram/app/database/session.py)
- SQLAlchemy SQLite database storing `Document`, `Source`, `Match`, `Report`, `Setting`.
- Thread-safe sessions with connection pooling.

#### [NEW] [reports/pdf_generator.py](file:///d:/Programs/Poligram/app/reports/pdf_generator.py), [html_generator.py](file:///d:/Programs/Poligram/app/reports/html_generator.py)
- **ReportLab PDF**: Formal academic layout with university header, student/researcher name, roll number, department, supervisor name, paper title, executive summary, pie/gauge charts, side-by-side match breakdown, and prominent disclaimer.
- **Standalone HTML Report**: Self-contained HTML with embedded styles and interactive highlight filtering.
- **JSON & CSV Export**: Structured match data for research and departmental archives.

#### [NEW] [utils/security.py](file:///d:/Programs/Poligram/app/utils/security.py) & [logger.py](file:///d:/Programs/Poligram/app/utils/logger.py)
- Path traversal defense (`os.path.commonpath`), sanitized file names, maximum file size constraints (default 50MB, configurable).
- Isolated local file processing; strictly offline by default; zero document transmission without explicit user trigger.
- Rotating log handler writing clean operational logs to `logs/researchguard.log`.

---

### Packaging & Executable Generation

#### [NEW] [ResearchGuard.spec](file:///d:/Programs/Poligram/ResearchGuard.spec) & [build_exe.py](file:///d:/Programs/Poligram/build_exe.py)
- PyInstaller configuration targeting Windows 64-bit:
  - Bundles PySide6, PyMuPDF, python-docx, scikit-learn, rapidfuzz, reportlab, sqlalchemy, and resources.
  - Generates standalone `dist/ResearchGuard/ResearchGuard.exe`.
  - Validates executable launch and produces Inno Setup script (`installer.iss`) for an optional installer.

---

## Verification Plan

### Automated Tests
- Run `pytest tests/` verifying:
  1. `test_extractor.py`: PDF, DOCX, and TXT extraction, page tracking, scanned document heuristic.
  2. `test_engine.py`: Exact matching, RapidFuzz token matching, N-gram calculation, TF-IDF cosine similarity.
  3. `test_citations.py`: Citation pattern detection (APA, IEEE, Harvard), quotation isolation, references boundary detection.
  4. `test_scoring.py`: Scoring math, exclusions (quotes, references, common phrases), weight distribution.
  5. `test_reports.py`: PDF generation via ReportLab and HTML export generation.

### Manual & Interactive Verification
- Launch the PySide6 desktop application directly with `python -m app.main`.
- Test drag-and-drop document upload with sample academic papers.
- Inspect the Dashboard, New Check queue, Results view with interactive highlight viewer, and Settings.
- Verify light/dark theme switching and responsive resizing.
- Generate a sample PDF report and verify layout, charts, student/institutional metadata, and academic disclaimer.
- Run `python build_exe.py` to compile `ResearchGuard.exe` and verify executable creation.
