from __future__ import annotations
from typing import List, Dict, Any, Tuple
import io
import pandas as pd

# -------- DataFrame shaping --------


def dataframe_for_expenses(items: List[Dict[str, Any]]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=["ID", "Date", "Amount", "Category", "Note"])
    df = pd.DataFrame(items)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date
    rename = {"id": "ID", "date": "Date", "amount": "Amount",
              "category": "Category", "note": "Note"}
    df = df.rename(columns=rename)[
        ["ID", "Date", "Amount", "Category", "Note"]]
    df = df.sort_values(["Date", "ID"], ascending=[False, False])
    return df

# -------- Summaries --------


def summarize_by_month(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame({
            "Month": pd.Series(dtype="datetime64[ns]"),
            "Total": pd.Series(dtype="float64"),
        })

    x = df.copy()
    x["Date"] = pd.to_datetime(x["Date"], errors="coerce")
    x["Amount"] = pd.to_numeric(x["Amount"], errors="coerce")
    x = x.dropna(subset=["Date"])

    # Month as first day of month (datetime64), robust across pandas versions
    x["Month"] = x["Date"].dt.to_period("M").dt.to_timestamp()

    out = (x.groupby("Month", as_index=False)["Amount"]
           .sum()
           .rename(columns={"Amount": "Total"}))

    # Enforce dtypes explicitly
    out["Month"] = pd.to_datetime(out["Month"], errors="coerce")
    out["Total"] = pd.to_numeric(
        out["Total"], errors="coerce").astype("float64")
    return out


def summarize_by_category(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame({"Category": [], "Total": []})
    out = df.groupby("Category", as_index=False)[
        "Amount"].sum().rename(columns={"Amount": "Total"})
    return out.sort_values("Total", ascending=False)

# -------- KPIs --------


def kpis_current_month(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {"total_month": 0.0, "tx_count": 0, "avg_daily": 0.0, "top_category": "—", "largest": "—"}
    d = df.copy()
    d["Date"] = pd.to_datetime(d["Date"]).dt.date
    today = pd.to_datetime("today").date()
    first_of_month = today.replace(day=1)
    this_month = d[(d["Date"] >= first_of_month) & (d["Date"] <= today)]
    total = float(this_month["Amount"].sum()) if not this_month.empty else 0.0
    tx = int(len(this_month))
    if not this_month.empty:
        per_day = this_month.groupby("Date")["Amount"].sum().mean()
        avg_daily = float(per_day)
        largest_row = this_month.loc[this_month["Amount"].idxmax()]
        largest = f"{largest_row['Category']} — {largest_row['Amount']:.2f} on {largest_row['Date']}"
        by_cat = this_month.groupby(
            "Category")["Amount"].sum().sort_values(ascending=False)
        top_cat = f"{by_cat.index[0]} — {by_cat.iloc[0]:.2f}" if not by_cat.empty else "—"
    else:
        avg_daily, largest, top_cat = 0.0, "—", "—"
    return {"total_month": total, "tx_count": tx, "avg_daily": avg_daily, "top_category": top_cat, "largest": largest}


# -------- CSV helpers --------
CSV_COLUMNS = ["date", "amount", "category", "note"]


def export_csv(df: pd.DataFrame) -> bytes:
    tmp = df.rename(columns={"ID": "id", "Date": "date",
                    "Amount": "amount", "Category": "category", "Note": "note"})
    out = tmp[["date", "amount", "category", "note"]].copy()
    out["date"] = pd.to_datetime(out["date"]).dt.date.astype(str)
    return out.to_csv(index=False).encode("utf-8")


def import_csv_bytes(data: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
    errors: List[str] = []
    try:
        df = pd.read_csv(io.BytesIO(data))
    except Exception as ex:
        return [], [f"Failed to read CSV: {ex}"]
    missing = [c for c in CSV_COLUMNS if c not in df.columns]
    if missing:
        return [], [f"Missing columns: {', '.join(missing)}"]
    try:
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df["amount"] = pd.to_numeric(df["amount"]).astype(float)
        df["category"] = df["category"].astype(str).str.strip()
        if "note" in df.columns:
            df["note"] = df["note"].astype(str)
    except Exception as ex:
        errors.append(f"Failed to normalize: {ex}")
        return [], errors
    items: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        items.append({
            "date": row["date"],
            "amount": float(row["amount"]),
            "category": row["category"],
            "note": None if pd.isna(row.get("note")) else str(row.get("note")),
        })
    return items, errors
