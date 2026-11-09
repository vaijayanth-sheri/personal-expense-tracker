# Personal Expense Tracker - Design Specification

## Overview
A lightweight, privacy-focused, zero-cloud personal expense tracker designed to run 100% locally on Windows. It delivers fast transaction recording, category grouping, mathematical summaries in Euros (€), runway forecasting, and interactive financial scenario simulation ("what-if" models) with minimal RAM (~25-30 MB) and disk usage (< 10 MB).

## 1. Architecture & Execution Model
- **Language / Runtime:** Python 3.x (standard library + single-file zero-dependency micro-server).
- **Frontend:** Single-page application using modern HTML5, CSS3, and Vanilla JavaScript.
- **Charts:** Lightweight Canvas / SVG data visualizations without external npm/CDN bundles to ensure full offline capability.
- **Desktop Application Launcher:**
  - One-click Desktop shortcut (`Personal Expense Tracker.lnk`) pointing to a quiet launcher script (`run_app.vbs` / `run_app.bat`).
  - Launches the server and opens Microsoft Edge in standalone desktop app mode (`--app=http://127.0.0.1:5055 --window-size=1150,780`).
  - Native desktop window appearance without URL address bar, tabs, or browser clutter.
  - Automatically terminates server when the desktop window is closed or on launcher shutdown.

## 2. Privacy & Data Storage
- **Database Engine:** Embedded SQLite (`data/expenses.db`).
- **Isolation Policy:** 
  - The `data/` folder and any `*.db` files are strictly excluded via `.gitignore`.
  - The repository can be shared or made public on GitHub without risking personal financial data exposure.
  - The application auto-creates `data/` and initializes database tables on first launch.

### Database Schema
- **`transactions` table:**
  - `id`: INTEGER PRIMARY KEY AUTOINCREMENT
  - `date`: TEXT (YYYY-MM-DD)
  - `type`: TEXT CHECK(type IN ('expense', 'income'))
  - `category`: TEXT (e.g. Housing, Food, Utilities, Transport, Health, Leisure, Salary, Side Income, Other)
  - `amount`: REAL (Values in €)
  - `note`: TEXT (optional)
  - `is_recurring`: INTEGER DEFAULT 0 (0 = one-off, 1 = monthly recurring)
  - `created_at`: TIMESTAMP DEFAULT CURRENT_TIMESTAMP

- **`settings` table:**
  - `key`: TEXT PRIMARY KEY
  - `value`: TEXT (stores current starting balance in €, savings goal in €, target reserve months)

## 3. Core Features
1. **Financial Dashboard & Ledger:**
   - Real-time KPI summary in Euros (€): Total Cash Balance, Monthly Inflow, Monthly Outflow, Net Savings Rate.
   - Quick Add bar (Date, Type, Category, Amount in €, Recurring flag, Note).
   - Filterable, searchable transaction table with instant inline Edit and Delete.
   - Monthly category breakdown & spending breakdown graphs.

2. **Runway & Scenario Simulator (Option C):**
   - **Runway Forecast:** Calculates exact runway in months until zero or target savings based on current cash balance and recurring burn rate.
   - **Interactive "What-If" Simulation Sliders:**
     - Income adjustment: -50% to +50%
     - Fixed/Essential expense adjustment: -€1,000 to +€1,000
     - Discretionary/Variable spending adjustment: -100% to +100%
   - Visual trajectory showing projected balances at 3, 6, and 12 months under selected scenarios compared against the baseline.

3. **Data Portability:**
   - 1-click Export to CSV for external auditing / backups.
   - Backup SQLite database button directly in the UI.

## 4. Error Handling & Performance Constraints
- SQLite transactions wrapped in ACID transactions to prevent file corruption.
- Server uses minimal threading/epoll event loop, idle memory footprint ~25 MB.
- Offline-first: zero external CDN dependencies; all CSS, JS, and icons embedded locally.
