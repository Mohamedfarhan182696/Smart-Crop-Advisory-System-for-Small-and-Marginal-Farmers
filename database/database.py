"""
Database Connection
====================
SQLAlchemy engine and session management.
Supports SQLite (dev) and PostgreSQL (prod) via DATABASE_URL env var.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager

from database.models import Base


def _get_database_url() -> str:
    """Get database URL from environment or use default SQLite."""
    default_db_path = Path(__file__).resolve().parent / "scas.db"
    return os.environ.get("DATABASE_URL", f"sqlite:///{default_db_path}")


def _create_engine(database_url: str = None):
    """Create SQLAlchemy engine with appropriate settings."""
    if database_url is None:
        database_url = _get_database_url()

    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(
        database_url,
        connect_args=connect_args,
        echo=os.environ.get("DATABASE_ECHO", "false").lower() == "true",
        pool_pre_ping=True,
    )

    # Enable WAL mode for SQLite (better concurrent performance)
    if database_url.startswith("sqlite"):
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


# Module-level engine and session factory
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the database engine (singleton)."""
    global _engine
    if _engine is None:
        _engine = _create_engine()
    return _engine


def get_session_factory():
    """Get or create the session factory (singleton)."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
        )
    return _SessionLocal


def init_database():
    """Initialize the database — create all tables if they don't exist."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    return engine


def get_db() -> Session:
    """Get a database session. Use with context manager or manual close."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    return db


@contextmanager
def get_db_session():
    """Context manager for database sessions with automatic cleanup."""
    db = get_db()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def reset_database():
    """Drop and recreate all tables. USE WITH CAUTION — destroys all data."""
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
