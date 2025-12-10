# Personal Expense Tracker: Final
A lightweight, local-first budgeting app built with Streamlit, SQLModel/SQLite, and pandas.
Add expenses, filter/search them, analyze month trends & category totals, and import/export CSV.
Runs fully offline on Python 3.13 (no external services).
**Live demo:** https://personal-expense-tracker-amc.streamlit.app/

## Run
*Windows PowerShell
- cd (project-folder)
- python -m venv .venv
- .\\.venv\Scripts\Activate.ps1
- python -m pip install --upgrade pip
- pip install -r requirements.txt
- streamlit run app.py

*macOS / Linux (bash)
- cd (project-folder)
- python3 -m venv .venv
- source .venv/bin/activate
- python -m pip install --upgrade pip
- pip install -r requirements.txt
- streamlit run app.py

## Requirements
- Python 3.13.x
- Packages pinned in requirements.txt (Streamlit, SQLModel, SQLAlchemy 2.x, pandas, Altair, etc.)

## Files
- "app.py": Streamlit UI (Add Expense, View & Filter, Settings, dashboard)
- "db.py":  SQLite/SQLModel setup
- "models.py": Category/Expense
- "analytics.py": DF helper

### Deployment
The application is deployed on Streamlit Community Cloud at **https://personal-expense-tracker-amc.streamlit.app/**.
