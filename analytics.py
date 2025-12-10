"""analytics.py
Dataframe helper for table display.
More advanced summaries (by month/category) will be added in next Phase.
"""
from typing import List, Dict, Any
import pandas as pd


def dataframe_for_expenses(items: List[Dict[str, Any]]) -> pd.DataFrame:
    if not items:
        return pd.DataFrame(columns=["ID", "Date", "Amount", "Category", "Note"])
    df = pd.DataFrame(items)
    df = df.rename(columns={"id": "ID", "date": "Date",
                   "amount": "Amount", "category": "Category", "note": "Note"})
    df = df[["ID", "Date", "Amount", "Category", "Note"]]
    return df
