"""SQLAlchemy ORM models for IMRD ResearchGuard.
Stores student academic particulars, paper metrics, similarity matches, and official clearance records.
"""

from datetime import datetime
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

    # Overall similarity metrics
    overall_similarity = Column(Float, default=0.0)
    risk_level = Column(String(32), default="Very Low")  # Very Low, Low, Moderate, High, Very High
    exact_matches_count = Column(Integer, default=0)
    fuzzy_matches_count = Column(Integer, default=0)
    semantic_matches_count = Column(Integer, default=0)
    quoted_matches_count = Column(Integer, default=0)
    ai_likelihood = Column(String(32), default="Low")

    # Document contents and academic structure
    extracted_text = Column(Text, nullable=True)
    structure_json = Column(Text, nullable=True)

    # Relationships
    matches = relationship("Match", back_populates="document", cascade="all, delete-orphan")
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
