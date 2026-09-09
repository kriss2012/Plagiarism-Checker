"""SQLAlchemy ORM models for IMRD ResearchGuard.
Stores student academic particulars, paper metrics, similarity matches, structured references,
citation audits, human review decisions, and official clearance records.
"""

from datetime import datetime
import json
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Document(Base):
    """Stores student academic particulars, paper text, and plagiarism verification audit results."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(1024), nullable=False)
    hash = Column(String(64), nullable=False, index=True)
    upload_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    word_count = Column(Integer, default=0)
    page_count = Column(Integer, default=1)
    language = Column(String(32), default="English")
    status = Column(String(32), default="Completed")  # Pending, Completed, Error

    # Student & Academic Particulars for IMRD Shirpur
    student_name = Column(String(255), default="Student", index=True)
    prn_number = Column(String(64), default="", index=True)
    course_name = Column(String(64), default="MCA", index=True)  # MCA, MBA, BCA, BBA, Integrated MCA
    academic_year = Column(String(32), default="2025-2026")
    semester = Column(String(32), default="Semester IV")
    guide_name = Column(String(255), default="")
    paper_title = Column(String(512), default="")
    
    # Official Clearance & UGC Compliance Status
    clearance_status = Column(String(64), default="Approved (Level 0)")  # Approved (Level 0), Revisions Required (Level 1), Major Revisions (Level 2), Rejected (Level 3)
    certificate_no = Column(String(64), default="")

    # Overall similarity & multidimensional verification scores
    overall_similarity = Column(Float, default=0.0)
    risk_level = Column(String(32), default="Very Low")  # Very Low, Low, Moderate, High, Very High
    exact_matches_count = Column(Integer, default=0)
    fuzzy_matches_count = Column(Integer, default=0)
    semantic_matches_count = Column(Integer, default=0)
    quoted_matches_count = Column(Integer, default=0)
    ai_likelihood = Column(String(32), default="Low")

    # Advanced verification scores
    direct_match_score = Column(Float, default=0.0)
    semantic_similarity_score = Column(Float, default=0.0)
    citation_coverage_score = Column(Float, default=100.0)
    reference_verification_score = Column(Float, default=100.0)
    high_risk_similarity = Column(Float, default=0.0)
    academic_verdict = Column(String(64), default="LOW CONCERN")  # LOW CONCERN, MODERATE CONCERN, HIGH CONCERN, INCONCLUSIVE

    # Reference & Citation tallies
    references_count = Column(Integer, default=0)
    verified_references_count = Column(Integer, default=0)
    citation_issues_count = Column(Integer, default=0)

    # Document contents and academic structure
    extracted_text = Column(Text, nullable=True)
    structure_json = Column(Text, nullable=True)

    # Relationships
    matches = relationship("Match", back_populates="document", cascade="all, delete-orphan")
    references = relationship("Reference", back_populates="document", cascade="all, delete-orphan")
    citation_issues = relationship("CitationIssue", back_populates="document", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="document", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "filepath": self.filepath,
            "hash": self.hash,
            "upload_date": self.upload_date.strftime("%Y-%m-%d %H:%M:%S") if self.upload_date else "",
            "word_count": self.word_count,
            "page_count": self.page_count,
            "language": self.language,
            "status": self.status,
            "student_name": self.student_name or "Student",
            "prn_number": self.prn_number or "-",
            "course_name": self.course_name or "MCA",
            "academic_year": self.academic_year or "2025-2026",
            "semester": self.semester or "Semester IV",
            "guide_name": self.guide_name or "-",
            "paper_title": self.paper_title or self.filename,
            "clearance_status": self.clearance_status or "Approved (Level 0)",
            "certificate_no": self.certificate_no or f"IMRD/LIB/{self.id:04d}",
            "overall_similarity": round(self.overall_similarity, 1),
            "risk_level": self.risk_level,
            "exact_matches_count": self.exact_matches_count,
            "fuzzy_matches_count": self.fuzzy_matches_count,
            "semantic_matches_count": self.semantic_matches_count,
            "quoted_matches_count": self.quoted_matches_count,
            "ai_likelihood": self.ai_likelihood,
            "direct_match_score": round(self.direct_match_score or 0.0, 1),
            "semantic_similarity_score": round(self.semantic_similarity_score or 0.0, 1),
            "citation_coverage_score": round(self.citation_coverage_score or 100.0, 1),
            "reference_verification_score": round(self.reference_verification_score or 100.0, 1),
            "high_risk_similarity": round(self.high_risk_similarity or 0.0, 1),
            "academic_verdict": self.academic_verdict or "LOW CONCERN",
            "references_count": self.references_count or 0,
            "verified_references_count": self.verified_references_count or 0,
            "citation_issues_count": self.citation_issues_count or 0,
        }


class Source(Base):
    """Represents a reference paper, book, journal, or comparison source in the library."""
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(512), nullable=False)
    author = Column(String(255), default="Unknown")
    publication_year = Column(Integer, nullable=True)
    publisher = Column(String(255), nullable=True)
    url = Column(String(1024), nullable=True)
    doi = Column(String(255), nullable=True)
    source_type = Column(String(64), default="Journal")  # Journal, Conference, Book, Thesis, Website, Internal Document, Other
    filepath = Column(String(1024), nullable=True)
    content_hash = Column(String(64), nullable=True, index=True)
    text_content = Column(Text, nullable=True)
    word_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    matches = relationship("Match", back_populates="source")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "publication_year": self.publication_year,
            "publisher": self.publisher,
            "url": self.url,
            "doi": self.doi,
            "source_type": self.source_type,
            "filepath": self.filepath,
            "word_count": self.word_count,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else "",
        }


class Match(Base):
    """Detailed record of detected matching text segments between a paper and source."""
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="SET NULL"), nullable=True)
    
    sentence = Column(Text, nullable=False)
    matched_text = Column(Text, nullable=False)
    similarity_score = Column(Float, default=0.0)
    algorithm = Column(String(64), default="Exact")
    page_number = Column(Integer, default=1)
    start_char = Column(Integer, default=0)
    end_char = Column(Integer, default=0)
    
    is_quoted = Column(Boolean, default=False)
    is_cited = Column(Boolean, default=False)
    is_ignored = Column(Boolean, default=False)
    source_name = Column(String(512), default="Unknown Source")

    # Advanced verification fields
    confidence = Column(String(32), default="High")  # High, Medium, Low
    match_category = Column(String(64), default="Copied + No Citation")  # Copied + No Citation, Quoted + Cited, Paraphrased + Cited, etc.
    source_url = Column(String(1024), nullable=True)
    source_domain = Column(String(255), nullable=True)
    source_type = Column(String(64), default="Journal")
    source_reliability = Column(String(32), default="High")  # High, Medium, Low
    
    # Human Review system
    review_decision = Column(String(64), default="Pending Review")  # Pending Review, Confirmed Match, Not Plagiarism, Common Knowledge, Properly Cited, False Positive, Ignored
    review_notes = Column(Text, nullable=True)

    document = relationship("Document", back_populates="matches")
    source = relationship("Source", back_populates="matches")

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "source_id": self.source_id,
            "sentence": self.sentence,
            "matched_text": self.matched_text,
            "similarity_score": round(self.similarity_score, 1),
            "algorithm": self.algorithm,
            "page_number": self.page_number,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "is_quoted": self.is_quoted,
            "is_cited": self.is_cited,
            "is_ignored": self.is_ignored,
            "source_name": self.source_name,
            "confidence": self.confidence or "High",
            "match_category": self.match_category or "Copied + No Citation",
            "source_url": self.source_url,
            "source_domain": self.source_domain or "",
            "source_type": self.source_type or "Journal",
            "source_reliability": self.source_reliability or "High",
            "review_decision": self.review_decision or "Pending Review",
            "review_notes": self.review_notes or "",
        }


class Reference(Base):
    """Structured academic reference entry extracted from the bibliography."""
    __tablename__ = "references"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    ref_number = Column(Integer, nullable=True)
    raw_text = Column(Text, nullable=False)
    title = Column(String(512), default="")
    authors = Column(String(512), default="")
    journal = Column(String(255), default="")
    year = Column(Integer, nullable=True)
    volume = Column(String(64), nullable=True)
    issue = Column(String(64), nullable=True)
    pages = Column(String(64), nullable=True)
    doi = Column(String(255), nullable=True)
    url = Column(String(1024), nullable=True)
    publisher = Column(String(255), nullable=True)
    
    # Verification status: VERIFIED, PARTIALLY VERIFIED, NOT VERIFIED, SUSPICIOUS, DUPLICATE, BROKEN LINK
    status = Column(String(64), default="NOT VERIFIED")
    verification_source = Column(String(255), nullable=True)
    matched_metadata_json = Column(Text, nullable=True)
    difference_notes = Column(Text, nullable=True)
    is_duplicate = Column(Boolean, default=False)

    document = relationship("Document", back_populates="references")

    def to_dict(self):
        matched = {}
        if self.matched_metadata_json:
            try:
                matched = json.loads(self.matched_metadata_json)
            except Exception:
                pass
        return {
            "id": self.id,
            "document_id": self.document_id,
            "ref_number": self.ref_number,
            "raw_text": self.raw_text,
            "title": self.title,
            "authors": self.authors,
            "journal": self.journal,
            "year": self.year,
            "volume": self.volume,
            "issue": self.issue,
            "pages": self.pages,
            "doi": self.doi,
            "url": self.url,
            "publisher": self.publisher,
            "status": self.status,
            "verification_source": self.verification_source,
            "matched_metadata": matched,
            "difference_notes": self.difference_notes or "",
            "is_duplicate": self.is_duplicate,
        }


class CitationIssue(Base):
    """In-text citation audit finding (Missing Reference, Unused Reference, Mismatch, Numbering Error, Broken)."""
    __tablename__ = "citation_issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    issue_type = Column(String(64), nullable=False)
    citation_text = Column(String(255), nullable=False)
    page_number = Column(Integer, default=1)
    details = Column(Text, default="")
    ref_number = Column(Integer, nullable=True)

    document = relationship("Document", back_populates="citation_issues")

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "issue_type": self.issue_type,
            "citation_text": self.citation_text,
            "page_number": self.page_number,
            "details": self.details,
            "ref_number": self.ref_number,
        }


class Report(Base):
    """Tracks generated PDF/HTML/JSON reports and certificates for documents."""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    report_path = Column(String(1024), nullable=False)
    report_type = Column(String(32), default="PDF")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="reports")


class Setting(Base):
    """Key-value persistence for institutional configuration and user preferences."""
    __tablename__ = "settings"

    key = Column(String(128), primary_key=True)
    value = Column(Text, nullable=True)
