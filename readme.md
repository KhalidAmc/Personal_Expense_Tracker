# Personal Expense Tracker: Phase 2
This is a partial implementation for Assignment 2 (phase 2 checkpoint).  
It includes core data entry and basic viewing/filtering. The dashboard and some settings will be implemented in the next phase.

## Run (Windows PowerShell)
*powershell
cd (The Project directory)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py

## Current Scope (Phase 2)
- Add Expense (date, amount, category, note)
- View & Filter (category/date/text)
- Basic Category add
## TODO
- Dashboard (+ charts)
- Category delete 
- Import/Export CSV 

## Files
- "app.py": Streamlit UI (Add Expense, View & Filter, Settings, dashboard)
- "db.py":  SQLite/SQLModel setup
- "models.py": Category/Expense
- "analytics.py": DF helper
