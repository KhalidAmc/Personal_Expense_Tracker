from __future__ import annotations
from analytics import (
    dataframe_for_expenses, summarize_by_month, summarize_by_category,
    kpis_current_month, export_csv, import_csv_bytes
)
from models import Expense, Category
from db import init_db, get_engine, ensure_default_categories, get_session, safe_delete_category
from sqlmodel import select
import pandas as pd
import streamlit as st
from typing import List, Dict, Any
import datetime as dt
import warnings
from sqlalchemy.exc import SAWarning
warnings.filterwarnings(
    "ignore",
    r"This declarative base already contains a class with the same class name",
    category=SAWarning,
)


st.set_page_config(page_title="Expense Tracker", page_icon="💰", layout="wide")
st.markdown("""
<style>
/* shrink the big metric numbers/text to prevent truncation */
div[data-testid="stMetricValue"] { font-size: 14px !important; }
div[data-testid="stMetricLabel"] { font-size: 14px !important; }
</style>
""", unsafe_allow_html=True)
st.title("💰 Personal Expense Tracker")

# Init DB & defaults
engine = get_engine()
init_db(engine)
ensure_default_categories()

# Helpers


def load_categories() -> List[str]:
    with get_session() as s:
        rows = s.exec(select(Category).order_by(Category.name)).all()
    return [c.name for c in rows]


def load_expenses() -> List[Dict[str, Any]]:
    with get_session() as s:
        rows = s.exec(select(Expense).order_by(
            Expense.date.desc(), Expense.id.desc())).all()
    return [r.model_dump() for r in rows]


# Navigation
page = st.sidebar.radio(
    "Navigation", ["Add Expense", "View & Filter", "Dashboard", "Settings"], index=0)

# Add Expense
if page == "Add Expense":
    st.subheader("Add a new expense")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        date_val = st.date_input("Date", value=dt.date.today())
    with c2:
        amount_val = st.number_input(
            "Amount", min_value=0.0, step=1.0, format="%.2f")
    with c3:
        cats = load_categories()
        category_val = st.selectbox("Category", options=cats)
    with c4:
        note_val = st.text_input("Note (optional)", max_chars=160)

    if st.button("Save Expense", type="primary"):
        if amount_val <= 0:
            st.error("Amount must be greater than 0.")
        else:
            with get_session() as s:
                s.add(Expense(date=date_val, amount=float(amount_val),
                      category=category_val, note=note_val or None))
                s.commit()
            st.success("Expense saved ✅")

# View & Filter
elif page == "View & Filter":
    st.subheader("All expenses (with filters, CSV import/export)")
    items = load_expenses()
    df = dataframe_for_expenses(items)

    cc1, cc2, cc3, cc4 = st.columns([1, 1, 2, 2])
    with cc1:
        cats = load_categories()
        cat_filter = st.multiselect("Category filter", cats, [])
    with cc2:
        min_d = df["Date"].min() if not df.empty else dt.date.today()
        max_d = df["Date"].max() if not df.empty else dt.date.today()
        date_range = st.date_input("Date range", (min_d, max_d))
    with cc3:
        text_filter = st.text_input("Search notes", "")
    with cc4:
        st.write(" ")

    fdf = df.copy()
    if not fdf.empty:
        if cat_filter:
            fdf = fdf[fdf["Category"].isin(cat_filter)]
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start, end = date_range
            fdf = fdf[(fdf["Date"] >= start) & (fdf["Date"] <= end)]
        if text_filter.strip():
            fdf = fdf[fdf["Note"].fillna("").str.contains(
                text_filter, case=False, na=False)]
    # Display
    display_df = fdf[["Date", "Amount", "Category", "Note"]].copy()
    # make Amount purely numeric
    display_df["Amount"] = pd.to_numeric(
        display_df["Amount"], errors="coerce").astype("float64")

    # clean Note: turn literal "nan"/None/NaN into empty strings
    display_df["Note"] = (
        display_df["Note"]
        .replace({pd.NA: "", None: "", "nan": ""})
        .fillna("")
        .astype(str)
    )

    st.dataframe(
        display_df.style.format({"Amount": "{:,.0f}"}),
        hide_index=True,
        use_container_width=True,
    )

    # Export
    exp_bytes = export_csv(fdf)
    st.download_button("⬇️ Export filtered to CSV", data=exp_bytes,
                       file_name="expenses_filtered.csv", mime="text/csv")

    # Import
    st.markdown("#### Import CSV")
    up = st.file_uploader(
        "Upload CSV (columns: date,amount,category,note)", type=["csv"])
    if up is not None:
        content = up.read()
        rows, errs = import_csv_bytes(content)
        if errs:
            for e in errs:
                st.error(e)
        elif rows:
            created_cats = set()
            with get_session() as s:
                existing = {c.name for c in s.exec(select(Category)).all()}
                for r in rows:
                    cat = r["category"]
                    if cat not in existing and cat not in created_cats:
                        s.add(Category(name=cat))
                        created_cats.add(cat)
                s.commit()
                for r in rows:
                    s.add(Expense(
                        date=r["date"], amount=r["amount"], category=r["category"], note=r["note"]))
                s.commit()
            st.success(f"Imported {len(rows)} rows ✅")

# Dashboard
elif page == "Dashboard":
    st.subheader("Dashboard (KPIs, Monthly & Category summaries)")
    items = load_expenses()
    df = dataframe_for_expenses(items)

    k = kpis_current_month(df)
    kcol1, kcol2, kcol3, kcol4, kcol5 = st.columns(5)
    kcol1.metric("Total this month", f"{k['total_month']:.2f}")
    kcol2.metric("Transactions this month", str(k["tx_count"]))
    kcol3.metric("Avg daily (this month)", f"{k['avg_daily']:.2f}")
    kcol4.metric("Top category this month", k["top_category"])
    kcol5.metric("Largest expense this month", k["largest"])

    st.markdown("---")
    st.markdown("### Totals by Month")
    by_month = summarize_by_month(df).sort_values("Month")
    display_tbl = pd.DataFrame({
        "Month": by_month["Month"].dt.strftime("%B %Y"),
        "Total": pd.to_numeric(by_month["Total"], errors="coerce")
    })

    # Remove any non-numeric rows that failed coercion
    display_tbl = display_tbl.dropna(
        subset=["Total"]).astype({"Total": "float64"})

    # Format with pandas Styler (avoids Streamlit's numeric validator)
    styler = display_tbl.style.format({"Total": "{:,.0f}"})

    st.dataframe(
        styler,
        hide_index=True,
        width=420,
        # formatting is handled by Styler
    )

    if not by_month.empty:
        import altair as alt
        chart_m = alt.Chart(by_month).mark_line(point=True).encode(
            # show month labels (not daily ticks)
            x=alt.X("yearmonth(Month):T",
                    axis=alt.Axis(format="%b %Y", labelAngle=-30, title="Month")),
            y=alt.Y("Total:Q", title="Total"),
            tooltip=[
                alt.Tooltip("yearmonth(Month):T", title="Month"),
                alt.Tooltip("Total:Q", title="Total"),
            ],
        ).properties(height=280)
        st.altair_chart(chart_m, use_container_width=True)
    else:
        st.info("No data yet. Add some expenses.")

    st.markdown("### Totals by Category")
    by_cat = summarize_by_category(df)
    # Clean display table (2 cols, numeric Total)
    cat_tbl = pd.DataFrame({
        "Category": by_cat["Category"].astype(str),
        "Total": pd.to_numeric(by_cat["Total"], errors="coerce")
    }).dropna(subset=["Total"]).astype({"Total": "float64"})

    # Pretty formatting via Styler (avoids ⚠️ icons)
    cat_styler = cat_tbl.style.format({"Total": "{:,.0f}"})

    st.dataframe(
        cat_styler,
        hide_index=True,
        width=420,
    )
    if not by_cat.empty:
        import altair as alt
        chart_c = alt.Chart(by_cat).mark_bar().encode(
            x="Category:N",
            y="Total:Q",
            tooltip=["Category:N", "Total:Q"]
        ).properties(height=280)
        st.altair_chart(chart_c, use_container_width=True)

# Settings
elif page == "Settings":
    st.subheader("Manage categories")
    st.markdown("**Add a new category**")
    new_cat = st.text_input("Category name", "")
    if st.button("Add Category"):
        name = new_cat.strip()
        if not name:
            st.error("Enter a non-empty name.")
        else:
            try:
                with get_session() as s:
                    s.add(Category(name=name))
                    s.commit()
                st.success("Category added ✅")
            except Exception:
                st.error("Could not add category. It might already exist.")

    st.markdown("---")
    st.markdown("**Delete a category (safe)**")
    cats = load_categories()
    if cats:
        to_delete = st.selectbox("Select category to delete", options=[
                                 "(None)"] + cats, index=0)
        if to_delete != "(None)" and st.button(f"Delete '{to_delete}'", type="secondary"):
            ok, msg = safe_delete_category(to_delete)
            (st.success if ok else st.error)(msg)
    else:
        st.info("No categories yet.")
