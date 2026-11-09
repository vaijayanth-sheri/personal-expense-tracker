# Personal Expense Tracker Implementation Plan

> **Goal:** Build an ultra-lightweight, local-only personal expense tracker in Python with SQLite, web-view desktop mode, and predictive scenario modeling in Euros (€).

---

### Task 1: Environment & Project Setup (.gitignore & test skeleton)

- **Step 1.1:** Create `.gitignore` to strictly exclude local SQLite databases, `data/` folder, caches, and OS files.
- **Step 1.2:** Write minimal unit test structure using standard library `unittest` (no pip dependencies required).
- **Step 1.3:** Commit environment setup.

---

### Task 2: Database Layer (`database.py`) & Tests

- **Step 2.1:** Write unit tests for SQLite database operations:
  - `init_db(db_path)`: creates tables `transactions` and `settings`.
  - `add_transaction(date, type, category, amount, note, is_recurring)`
  - `get_transactions(filter_options)`
  - `update_transaction(id, ...)`
  - `delete_transaction(id)`
  - `get_summary()` (inflow, outflow, balance, recurring burn rate)
  - `get_settings()` / `update_setting(key, value)`
- **Step 2.2:** Run tests and verify they fail.
- **Step 2.3:** Implement `database.py`.
- **Step 2.4:** Run tests and verify all pass.
- **Step 2.5:** Commit database layer.

---

### Task 3: Financial Math & Scenario Simulator Engine (`analytics.py`) & Tests

- **Step 3.1:** Write unit tests for:
  - Runway calculation (`calculate_runway(current_balance, recurring_burn, variable_burn)`).
  - Scenario simulation (`simulate_scenarios(base_income, base_fixed, base_variable, income_delta_pct, fixed_delta_eur, variable_delta_pct, months=12)`).
  - Target amount needed (`calculate_needed_savings(target_date, target_amount, current_balance, net_monthly_savings)`).
- **Step 3.2:** Run tests and verify failure.
- **Step 3.3:** Implement `analytics.py`.
- **Step 3.4:** Run tests and verify all pass.
- **Step 3.5:** Commit analytics engine.

---

### Task 4: Lightweight Backend Server (`server.py`) & API Endpoints

- **Step 4.1:** Write unit tests for JSON REST API endpoints using Python's built-in `http.server` / `urllib.request`:
  - `GET /api/transactions`
  - `POST /api/transactions`
  - `PUT /api/transactions/<id>`
  - `DELETE /api/transactions/<id>`
  - `GET /api/summary`
  - `POST /api/simulate`
  - `GET /api/settings`, `POST /api/settings`
  - `GET /api/export` (CSV export)
- **Step 4.2:** Run tests and verify failure.
- **Step 4.3:** Implement `server.py` using Python standard library (clean, fast, 0 pip bloat).
- **Step 4.4:** Run tests and verify all pass.
- **Step 4.5:** Commit server module.

---

### Task 5: Minimalist Frontend (`web/index.html`, `web/style.css`, `web/app.js`)

- **Step 5.1:** Build clean HTML5 structure with:
  - KPI Cards (Current Balance in €, Monthly Inflow, Monthly Outflow, Net Burn / Savings).
  - Quick Transaction Entry bar.
  - Interactive Filter & Transactions Table (with inline edit & delete).
  - Visual Breakdown Chart (pure Canvas / SVG - 0 KB CDN bloat).
  - Scenario Simulator Tab:
    - Sliders for Income %, Fixed Costs € change, Discretionary % change.
    - 3, 6, 12-month projected balance outcomes with runway readout.
- **Step 5.2:** Implement modern, responsive CSS (clean slate, dark/light balanced theme, compact spacing).
- **Step 5.3:** Implement client-side `app.js` with instant reactivity and modal/inline editors.
- **Step 5.4:** Commit frontend assets.

---

### Task 6: Desktop Launcher & One-Click Shortcut (`create_desktop_shortcut.bat`, `run_app.bat`, `run_app.vbs`)

- **Step 6.1:** Create `run_app.bat` that runs the local micro-server and opens Microsoft Edge in clean app mode:
  ```cmd
  msedge.exe --app=http://127.0.0.1:5055 --window-size=1180,800
  ```
- **Step 6.2:** Create silent VBScript wrapper `run_app.vbs` so no ugly black command prompt window stays open while using the app.
- **Step 6.3:** Create `create_desktop_shortcut.bat` that automatically places a "Personal Expense Tracker" desktop icon on the user's Windows Desktop.
- **Step 6.4:** Test end-to-end launch workflow.
- **Step 6.5:** Commit launchers and packaging scripts.

---

### Task 7: Final Verification & User Guide

- **Step 7.1:** Run full test suite.
- **Step 7.2:** Launch application, verify data persistence in `data/expenses.db`, verify `.gitignore` safety.
- **Step 7.3:** Write concise `README.md` with instructions on running and sharing the project safely.
