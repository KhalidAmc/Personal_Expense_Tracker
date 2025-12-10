"""db.py
SQLite database setup + session helper
"""
from contextlib import contextmanager
from typing import Iterator, List
import os
from sqlmodel import SQLModel, Session, create_engine, select
from models import Category

_DB_FILE = os.path.join(os.path.dirname(__file__), "expenses.db")
_DB_URL = f"sqlite:///{_DB_FILE}"

_engine = create_engine(_DB_URL, echo=False)


def get_engine():
    return _engine


def init_db(engine) -> None:
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Iterator[Session]:
    with Session(_engine) as session:
        yield session


def ensure_default_categories(defaults: List[str] | None = None) -> None:
    if defaults is None:
        defaults = ["Food", "Transport", "Rent", "Utilities", "Other"]
    with get_session() as s:
        existing = s.exec(select(Category)).all()
        if not existing:
            for name in defaults:
                s.add(Category(name=name))
            s.commit()
