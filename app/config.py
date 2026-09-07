"""Configuration constants, application directories, and defaults for ResearchGuard.
Tailored for SES's R. C. Patel Institute of Management Research and Development (IMRD), Shirpur.
Central Library Plagiarism & Research Paper Clearance Cell.
"""

import os
import sys
from pathlib import Path

# Application & Institutional Metadata
APP_NAME = "ResearchGuard"
APP_TITLE = "IMRD ResearchGuard – Student Paper & Dissertation Plagiarism Checker"
APP_VERSION = "1.0.0"
ORGANIZATION = "SES's R. C. Patel IMRD Shirpur"

# Institutional Credentials
INSTITUTION_NAME = "SES's R. C. Patel Institute of Management Research and Development, Shirpur"
INSTITUTION_SHORT = "IMRD Shirpur"
AFFILIATION_TEXT = "Affiliated to KBC North Maharashtra University, Jalgaon • Accredited 'A' Grade by NAAC"
LIBRARY_DEPARTMENT = "Central Library & Research Verification Cell"
INSTITUTION_ADDRESS = "Karwand Naka, Shirpur, Dist. Dhule, Maharashtra - 425405"

# Determine application base paths
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
    APP_DATA_DIR = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME
else:
    BASE_DIR = Path(__file__).resolve().parent.parent
    APP_DATA_DIR = BASE_DIR / "data"

# Create application subdirectories
APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR = APP_DATA_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_DIR = APP_DATA_DIR / "db"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
SOURCES_DIR = APP_DATA_DIR / "sources"
SOURCES_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR = APP_DATA_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = APP_DATA_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Database file path
DATABASE_PATH = DATABASE_DIR / "researchguard.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

# Log file path
LOG_FILE_PATH = LOGS_DIR / "researchguard.log"

# Default Librarian Settings Schema
DEFAULT_SETTINGS = {
    # General & Institutional
    "app_name": "IMRD ResearchGuard",
    "institution_name": INSTITUTION_NAME,
    "institution_short": INSTITUTION_SHORT,
    "affiliation_text": AFFILIATION_TEXT,
    "department_name": "Department of Computer Applications & Management",
    "theme": "light",  # Professional Light Windows Theme by default
    "auto_save_reports": True,
    "confirm_deletion": True,
    
    # Librarian Verification Credentials
    "librarian_name": "Central Library Officer",
    "librarian_designation": "Librarian / Verification Officer",
    "default_course": "MCA",
    "default_academic_year": "2025-2026",
    
    # UGC / Institutional Thresholds
    # UGC Regulation: Similarities up to 10% are excluded (Level 0: Acceptable)
    "ugc_level_0_max": 10.0,
    "ugc_level_1_max": 40.0,
    "ugc_level_2_max": 60.0,
    
    # Analysis Sensitivity & Thresholds
    "exact_match_min_words": 5,
    "fuzzy_similarity_threshold": 80.0,
    "semantic_similarity_threshold": 75.0,
    "ngram_size": 5,
    "min_match_character_length": 30,
    "filter_common_phrases": True,
    
    # Exclusions
    "exclude_references": True,
    "exclude_quotes": True,
    "exclude_citations": True,
    "exclude_small_matches": True,
    "min_word_count_to_flag": 6,
    
    # Documents
    "max_file_size_mb": 50,
    "ocr_enabled": False,
    "extract_tables": True,
    
    # Scoring Weights
    "weight_exact": 0.45,
    "weight_fuzzy": 0.30,
    "weight_semantic": 0.25,
    
    # Privacy & Network
    "offline_mode": True,  # Strictly local documents by default
    "enable_web_search": False,
    "web_search_provider": "crossref",
    "web_search_api_key": "",
    "delete_source_documents_after_analysis": False,
    
    # Risk Level Thresholds
    "risk_very_low_max": 10.0,
    "risk_low_max": 25.0,
    "risk_moderate_max": 40.0,
    "risk_high_max": 60.0,
}

# Official Clearance Certificate Disclaimer
ACADEMIC_DISCLAIMER = (
    "This similarity clearance certificate is issued by the Central Library of SES's R. C. Patel IMRD, Shirpur "
    "for academic project / dissertation submission in accordance with University and Institutional academic integrity guidelines. "
    "The similarity index reflects textual overlap identified against available institutional repositories and published academic sources."
)
