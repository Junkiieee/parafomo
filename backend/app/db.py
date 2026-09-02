"""SQLAlchemy motoru, oturum ve Base."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings

_settings = get_settings()

engine = create_engine(
    _settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite + FastAPI thread'leri
    echo=False,
)


@event.listens_for(engine, "connect")
def _enable_sqlite_fk(dbapi_conn, _record) -> None:
    """SQLite'ta yabancı anahtar zorlaması varsayılan kapalı — ondelete CASCADE
    çalışsın diye her bağlantıda aç."""
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON")
    cur.close()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Tabloları oluştur (yoksa). Modeller import edilmiş olmalı."""
    from . import models  # noqa: F401  (tabloları Base'e kaydeder)

    Base.metadata.create_all(bind=engine)
