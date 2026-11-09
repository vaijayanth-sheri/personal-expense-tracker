# Implementation Plan: Custom Branding & Exact Salary Simulation

### Task 1: Generate Custom Icon Assets (`assets/icon.ico`, `assets/icon.png`)
- **Step 1.1:** Write a Python script using standard library / BMP / pure python ICO generation to generate the Modern Geometric Euro Vault icon in multi-resolution formats (256, 128, 64, 48, 32, 16) and PNG.
- **Step 1.2:** Verify icon files are created in `assets/`.
- **Step 1.3:** Commit custom icon assets.

### Task 2: Exact Salary Simulation Engine (`analytics.py` & tests)
- **Step 2.1:** Add failing unit tests in `tests/test_analytics.py` for exact salary input modeling.
- **Step 2.2:** Update `analytics.py` to support `scenario_monthly_income` override.
- **Step 2.3:** Run tests and ensure all pass.
- **Step 2.4:** Commit analytics updates.

### Task 3: Backend API Support (`server.py` & tests)
- **Step 3.1:** Add test in `tests/test_server.py` verifying `scenario_monthly_income` in `/api/simulate`.
- **Step 3.2:** Update `server.py` to parse and forward `scenario_monthly_income`, and serve `/favicon.ico` and `/manifest.json`.
- **Step 3.3:** Run server tests and verify pass.
- **Step 3.4:** Commit server updates.

### Task 4: Frontend UI Updates (Exact Salary Controls & Custom SVG Icons)
- **Step 4.1:** Update `web/index.html` and `web/style.css` to add:
  - Exact salary number input & slider controls with dynamic delta badge.
  - Crisp embedded SVG icons for Header, Navigation, KPI cards, and buttons.
- **Step 4.2:** Update `web/app.js` to synchronize the exact salary input with slider and trigger dynamic simulation.
- **Step 4.3:** Commit frontend changes.

### Task 5: Desktop Shortcut & Taskbar Icon Integration
- **Step 5.1:** Update `create_desktop_shortcut.bat` to set `assets\icon.ico` as the shortcut icon.
- **Step 5.2:** Re-run shortcut creation to update user's Windows Desktop icon.
- **Step 5.3:** Verify launch behavior.
- **Step 5.4:** Commit launcher scripts.
