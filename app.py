"""app.py
Streamlit app with core flows:
- Add Expense
- View & Filter
- Settings (add category)
- Dashboard placeholder
"""
import datetime as dt
from typing import List, Dict, Any

import streamlit as st
from sqlmodel import select

from db import init_db, get_engine, ensure_default_categories, get_session
from models import Expense, Category
from analytics import dataframe_for_expenses

st.set_page_config(page_title="Expense Tracker", layout="wide")
st.title("Expense Tracker")

# DB bootstrap
engine = get_engine()
init_db(engine)
ensure_default_categories()

# Navigation
page = st.sidebar.radio(
    "Navigation", ["Add Expense", "View & Filter", "Dashboard", "Settings"], index=0)


def load_categories() -> List[str]:
    with get_session() as s:
        rows = s.exec(select(Category).order_by(Category.name)).all()
    return [c.name for c in rows]


def load_expenses() -> list[dict]:
    with get_session() as s:
        rows = s.exec(select(Expense).order_by(
            Expense.date.desc(), Expense.id.desc())).all()
    return [r.model_dump() for r in rows]


# Add Expense
if page == "Add Expense":
    st.subheader("Add Expense")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        date_val = st.date_input("Date", value=dt.date.today())
    with col2:
        amount_val = st.number_input(
            "Amount", min_value=0.0, step=1.0, format="%.2f")
    with col3:
        cats = load_categories()
        category_val = st.selectbox("Category", options=cats)
    with col4:
        note_val = st.text_input("Note (optional)", max_chars=120)

    if st.button("Save Expense", type="primary"):
        if amount_val <= 0:
            st.error("Amount must be > 0.")
        else:
            with get_session() as s:
                s.add(Expense(date=date_val, amount=float(amount_val),
                      category=category_val, note=note_val or None))
                s.commit()
            st.success("Saved")


# View & Filter
elif page == "View & Filter":
    st.subheader("View & Filter")
    items = load_expenses()
    df = dataframe_for_expenses(items)

    col1, col2, col3 = st.columns(3)
    with col1:
        cats = load_categories()
        cat_filter = st.multiselect("Category filter", cats, [])
    with col2:
        min_d = df["Date"].min() if not df.empty else dt.date.today()
        max_d = df["Date"].max() if not df.empty else dt.date.today()
        date_range = st.date_input("Date range", (min_d, max_d))
    with col3:
        text_filter = st.text_input("Search notes", "")

    if not df.empty:
        if cat_filter:
            df = df[df["Category"].isin(cat_filter)]
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start, end = date_range
            try:
                df = df[(df["Date"] >= start) & (df["Date"] <= end)]
            except Exception:
                pass
        if text_filter.strip():
            df = df[df["Note"].fillna("").str.contains(
                text_filter, case=False, na=False)]

    st.dataframe(df, width="stretch")


# Dashboard (placeholder)
elif page == "Dashboard":
    st.subheader("Dashboard (to be completed)")
    st.info(
        "Charts and summaries (by month / category) will be added next phase.")


# Settings
elif page == "Settings":
    st.subheader("Settings")
    st.markdown("**Add category**")
    new_cat = st.text_input("Category name", "")
    if st.button("Add Category"):
        name = new_cat.strip()
        if not name:
            st.error("Please enter a non-empty name.")
        else:
            try:
                with get_session() as s:
                    s.add(Category(name=name))
                    s.commit()
                st.success("Category added")
            except Exception:
                st.error("Could not add category. It might already exist.")
