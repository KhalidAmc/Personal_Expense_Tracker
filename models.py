from typing import Optional
from datetime import date as dt_date
from sqlmodel import SQLModel, Field


class Category(SQLModel, table=True):
    __tablename__ = "category"
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)


class Expense(SQLModel, table=True):
    __tablename__ = "expense"
    __table_args__ = {"extend_existing": True}
    id: Optional[int] = Field(default=None, primary_key=True)
    date: dt_date = Field(index=True)
    amount: float
    category: str = Field(index=True)
    note: Optional[str] = None
