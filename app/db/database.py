# app/db/database.py
from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

# Load environment variables from mounted .env and prefer file values
load_dotenv(encoding='utf-8', override=True)

DB_SCHEMA = "articlesumm_schema"
SQLITE_FALLBACK_URL = os.getenv("SQLITE_FALLBACK_URL", "sqlite:///./articlesumm.db")


def _build_engine(url: str):
    if url.startswith("postgresql"):
        return create_engine(
            url,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3},
        )
    return create_engine(url, pool_pre_ping=True)


def _resolve_database_url() -> tuple[str, bool]:
    configured_url = os.getenv("DATABASE_URL")
    if not configured_url:
        print(f"[DB] DATABASE_URL not set. Using SQLite fallback: {SQLITE_FALLBACK_URL}")
        return SQLITE_FALLBACK_URL, True

    try:
        test_engine = _build_engine(configured_url)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        test_engine.dispose()
        print("[DB] Connected to configured DATABASE_URL")
        return configured_url, configured_url.startswith("sqlite")
    except Exception as exc:
        print(f"[DB] WARNING: Configured DATABASE_URL is unreachable: {exc}")
        print(f"[DB] Falling back to SQLite: {SQLITE_FALLBACK_URL}")
        return SQLITE_FALLBACK_URL, True


ACTIVE_DATABASE_URL, DB_IS_SQLITE = _resolve_database_url()

engine = _build_engine(ACTIVE_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base(
    metadata=MetaData() if DB_IS_SQLITE else MetaData(schema=DB_SCHEMA)
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
