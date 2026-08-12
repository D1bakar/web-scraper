"""Database session and initialization."""

from __future__ import annotations

import logging
import time
from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.models import Base

logger = logging.getLogger(__name__)

_engine = None
_SessionLocal = None
_MAX_COMMIT_RETRIES = 5


def _configure_sqlite(connection, _record) -> None:
    """Enable WAL mode and busy timeout for concurrent access."""
    cursor = connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()
        db_path = settings.database_url.replace("sqlite:///", "")
        if db_path.startswith("./"):
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
        _engine = create_engine(
            settings.database_url,
            connect_args=connect_args,
            pool_pre_ping=True,
        )

        if settings.database_url.startswith("sqlite"):
            event.listen(_engine, "connect", _configure_sqlite)

        _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    return _engine


def reset_db_engine() -> None:
    """Reset engine (for tests)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None


def init_db() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    if _SessionLocal is None:
        get_engine()
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def safe_commit(db: Session) -> None:
    """Commit with retry on SQLite lock contention."""
    for attempt in range(_MAX_COMMIT_RETRIES):
        try:
            db.commit()
            return
        except OperationalError as exc:
            db.rollback()
            if "locked" in str(exc).lower() and attempt < _MAX_COMMIT_RETRIES - 1:
                time.sleep(0.05 * (attempt + 1))
                continue
            raise


def get_session_factory():
    """Return session factory, initializing engine if needed."""
    if _SessionLocal is None:
        get_engine()
    return _SessionLocal


def check_db_connection() -> bool:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("Database health check failed: %s", exc)
        return False
