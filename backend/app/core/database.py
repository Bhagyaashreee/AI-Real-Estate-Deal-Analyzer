import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Ensure data directory exists
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BACKEND_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Build SQLite URL with normalized absolute path if relative
db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///./data/"):
    db_file_name = db_url.replace("sqlite:///./data/", "")
    resolved_db_path = DATA_DIR / db_file_name
    db_url = f"sqlite:///{resolved_db_path.as_posix()}"

connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency for providing database sessions per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create database tables if they do not exist."""
    # Import models here so Base knows about them before create_all
    import app.models.property  # noqa: F401
    Base.metadata.create_all(bind=engine)

