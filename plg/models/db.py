from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from sqlmodel import Session, SQLModel, create_engine

# Import models to make them available to the engine
from plg.models import models  # noqa


DB_DIR = Path.home() / ".plg"
DB_PATH = DB_DIR / "plg.db"
CONN_STR = f"sqlite:///{DB_PATH}"

engine = create_engine(CONN_STR)


def _create_db_and_tables():
    """Creates the database and all tables defined by SQLModel."""
    # Ensure the database directory exists
    DB_DIR.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)


def init_database_if_needed():
    """
    Initializes the database and tables if the database file does not
    already exist.
    """
    if not DB_PATH.exists():
        _create_db_and_tables()


@contextmanager
def get_session(db_engine: Optional[create_engine] = None):
    """Provides a transactional scope around a series of operations."""
    # This ensures that no matter where get_session is called from,
    # the database is ready.
    init_database_if_needed()

    current_engine = db_engine or engine
    session = Session(current_engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
