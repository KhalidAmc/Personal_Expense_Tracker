from __future__ import annotations
from contextlib import contextmanager
from typing import Iterator, List
import os
from sqlmodel import SQLModel, Session, create_engine, select
from models import Category, Expense

# Keep DB inside ./data for persistence and clarity
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

_DB_FILE = os.path.join(DATA_DIR, "expenses.db")
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
        have_any = s.exec(select(Category)).first()
        if not have_any:
            for name in defaults:
                s.add(Category(name=name))
            s.commit()

def category_in_use(name: str) -> bool:
    with get_session() as s:
        row = s.exec(select(Expense).where(Expense.category == name)).first()
        return row is not None

def safe_delete_category(name: str) -> tuple[bool, str]:
    """Delete a category only if it's not referenced by any Expense."""
    if category_in_use(name):
        return False, f"Cannot delete '{name}' because it is used by one or more expenses."
    with get_session() as s:
        obj = s.exec(select(Category).where(Category.name == name)).first()
        if obj:
            s.delete(obj)
            s.commit()
            return True, f"Category '{name}' deleted."
        return False, f"Category '{name}' not found."
