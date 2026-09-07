"""Database session management, table initialization, and CRUD operations."""

import json
from contextlib import contextmanager
from typing import Any, Dict, List, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from app.config import DATABASE_URL, DEFAULT_SETTINGS
from app.database.models import Base, Document, Match, Report, Setting, Source
from app.utils.logger import logger

# Create SQLAlchemy engine for SQLite with multi-thread support
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Session = scoped_session(SessionFactory)


def init_db():
    """Initializes database tables and seeds default configuration settings."""
    logger.info("Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)

    with get_db() as session:
        for key, val in DEFAULT_SETTINGS.items():
            existing = session.query(Setting).filter_by(key=key).first()
            if not existing:
                serialized = json.dumps(val) if not isinstance(val, str) else val
                session.add(Setting(key=key, value=serialized))
        session.commit()
    logger.info("Database initialized successfully.")


@contextmanager
def get_db():
    """Provides a transactional scope around a series of operations."""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_setting(key: str, default: Any = None) -> Any:
    """Retrieves a setting by key, attempting JSON deserialization."""
    with get_db() as session:
        setting = session.query(Setting).filter_by(key=key).first()
        if not setting or setting.value is None:
            return default if default is not None else DEFAULT_SETTINGS.get(key)
        try:
            return json.loads(setting.value)
        except Exception:
            return setting.value


def set_setting(key: str, value: Any):
    """Saves a setting value to the database."""
    serialized = json.dumps(value) if not isinstance(value, str) else value
    with get_db() as session:
        setting = session.query(Setting).filter_by(key=key).first()
        if setting:
            setting.value = serialized
        else:
            session.add(Setting(key=key, value=serialized))


def get_all_settings() -> Dict[str, Any]:
    """Returns a dictionary of all persistent settings."""
    result = dict(DEFAULT_SETTINGS)
    with get_db() as session:
        rows = session.query(Setting).all()
        for r in rows:
            try:
                result[r.key] = json.loads(r.value)
            except Exception:
                result[r.key] = r.value
    return result


def get_all_documents(limit: int = 100) -> List[Document]:
    """Fetches list of analyzed documents sorted by latest upload date."""
    with get_db() as session:
        return session.query(Document).order_by(Document.upload_date.desc()).limit(limit).all()


def get_all_sources() -> List[Source]:
    """Fetches all source library documents."""
    with get_db() as session:
        return session.query(Source).order_by(Source.created_at.desc()).all()


def get_dashboard_metrics() -> Dict[str, Any]:
    """Calculates summary statistics for the dashboard cards and charts."""
    with get_db() as session:
        docs = session.query(Document).all()
        total_docs = len(docs)
        if total_docs == 0:
            return {
                "total_docs": 0,
                "total_checks": 0,
                "avg_similarity": 0.0,
                "highest_similarity": 0.0,
                "high_risk_count": 0,
                "recent_docs": [],
                "risk_distribution": {"Very Low": 0, "Low": 0, "Moderate": 0, "High": 0, "Very High": 0},
                "timeline": [],
            }

        sims = [d.overall_similarity for d in docs]
        avg_sim = sum(sims) / total_docs
        high_sim = max(sims)
        high_risk = sum(1 for d in docs if d.risk_level in ["High", "Very High"])

        risk_dist = {"Very Low": 0, "Low": 0, "Moderate": 0, "High": 0, "Very High": 0}
        for d in docs:
            level = d.risk_level or "Very Low"
            risk_dist[level] = risk_dist.get(level, 0) + 1

        recent = [
            d.to_dict()
            for d in session.query(Document).order_by(Document.upload_date.desc()).limit(5).all()
        ]

        return {
            "total_docs": total_docs,
            "total_checks": total_docs,
            "avg_similarity": round(avg_sim, 1),
            "highest_similarity": round(high_sim, 1),
            "high_risk_count": high_risk,
            "recent_docs": recent,
            "risk_distribution": risk_dist,
        }
