# Personal Expense Tracker

A minimalist, ultra-lightweight, 100% local personal finance application for Windows.

## Highlights
- **100% Local & Private:** All transactions are stored locally in `data/expenses.db` (SQLite). The `data/` folder is strictly ignored by Git so your data is never accidentally published or committed when sharing the codebase.
- **Ultra-lightweight:** Zero Node/npm runtime, zero heavy frameworks, zero heavy pip dependencies. Runs on Python standard library with ~25 MB RAM and < 10 MB disk footprint.
- **Euro (€) First:** Formatted in Euros (€) across balance displays, inflows, outflows, and forecasts.
- **Runway & Scenario Simulator:** Interactive "what-if" simulation sliders (income variance, fixed cost changes, variable spending adjustments) with pure Canvas 12-month projections.
- **One-Click Desktop App:** Launches as a standalone borderless Windows desktop window (no browser bars or tabs).

## Quick Start
1. Double-click **`Personal Expense Tracker`** on your Desktop.
   *(Or run `run_app.bat` in this folder)*.
2. The standalone desktop window will appear immediately.

## Data Safety
- Your data lives strictly in `data/expenses.db`.
- Use the **"📥 Export CSV"** button in the app anytime to export your records for offline backups or spreadsheet analysis.
