# Design Specification: Custom Branding & Exact Salary Simulation

## Overview
Enhance the Personal Expense Tracker with a dedicated custom visual identity (Modern Geometric Euro Vault/Prism icon for desktop shortcut, taskbar, favicon, and in-app SVG icons) and replace percentage-based income scenarios with exact Euro (€) monthly salary simulation.

## 1. Custom Visual Identity & Iconography
- **Design Motif:** Modern Geometric Euro Vault/Prism.
  - Dark slate/navy rounded shield backdrop (`#0f172a` & `#1e293b`), vibrant cyan/emerald accents (`#38bdf8`), with a crisp geometric Euro crest (`€`).
- **Assets:**
  - `assets/icon.ico`: High-res Windows multi-size icon (16x16, 32x32, 48x48, 64x64, 128x128, 256x256).
  - `assets/icon.png`: Crisp PNG for web favicon, web app manifest, and taskbar window branding.
- **Desktop & Taskbar Integration:**
  - Desktop shortcut (`Personal Expense Tracker.lnk`) explicitly configured with `assets/icon.ico`.
  - Windows Edge/Chrome app launcher configured with `--app-id="PersonalExpenseTracker"` and web manifest + favicon so the taskbar displays the custom vault icon.
- **In-App Iconography:**
  - Replace plain unicode emojis with cohesive, crisp, lightweight SVG icons across:
    - App Header & Logo
    - Inflow, Outflow, Balance, Runway KPI cards
    - Action buttons (Export CSV, Settings, Edit, Delete, Add)
    - Category indicators

## 2. Exact Monthly Salary Scenario Engine
- **Engine Changes (`analytics.py`):**
  - Update `simulate_scenarios` to accept `scenario_monthly_income: Optional[float]`.
  - If provided, `scenario_monthly_income` directly overrides the baseline income with the exact Euro figure (e.g. €3,500/month).
  - Maintain backward compatibility for any percentage fallback.
- **API Endpoint (`server.py`):**
  - Accept `scenario_monthly_income` in `POST /api/simulate`.
- **Frontend Controls (`web/index.html`, `web/app.js`):**
  - Replace the percentage slider with:
    - **Exact Monthly Salary input (€)** + synchronized slider.
    - Dynamic baseline indicator: *"Current baseline: €X.XX / month"*.
    - Difference badge showing `+€Y / month` or `-€Y / month` relative to current salary.
  - Updates projections in real time across 3, 6, and 12 months with the 12-month trajectory Canvas chart.

## 3. Verification & Testing
- Unit tests updated for exact salary scenario modeling in `tests/test_analytics.py` and `tests/test_server.py`.
- Desktop shortcut and app icon regenerated and verified.
