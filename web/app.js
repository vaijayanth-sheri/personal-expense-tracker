/**
 * Client application logic for Personal Expense Tracker
 */

let state = {
  transactions: [],
  summary: null,
  filters: {
    search: '',
    type: ''
  },
  scenario: {
    scenario_monthly_income: null,
    fixed_delta_eur: 0,
    variable_delta_pct: 0
  }
};

const formatEUR = (num) => {
  return new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR' }).format(num || 0);
};

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('tx-date').value = today;

  setupEventListeners();
  loadData();
});

function setupEventListeners() {
  // Tab switching
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.tab).classList.add('active');

      if (btn.dataset.tab === 'tab-scenarios') {
        syncScenarioBaseline();
        runScenarioSimulation();
      }
    });
  });

  // Add Transaction Form
  document.getElementById('form-add-transaction').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      type: document.getElementById('tx-type').value,
      amount: parseFloat(document.getElementById('tx-amount').value),
      category: document.getElementById('tx-category').value,
      date: document.getElementById('tx-date').value,
      note: document.getElementById('tx-note').value,
      is_recurring: document.getElementById('tx-recurring').checked ? 1 : 0
    };

    try {
      const res = await fetch('/api/transactions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        document.getElementById('tx-amount').value = '';
        document.getElementById('tx-note').value = '';
        document.getElementById('tx-recurring').checked = false;
        loadData();
      }
    } catch (err) {
      console.error("Failed to add transaction", err);
    }
  });

  // Table Filters
  document.getElementById('filter-search').addEventListener('input', (e) => {
    state.filters.search = e.target.value;
    renderTransactionsTable();
  });

  document.getElementById('filter-type').addEventListener('change', (e) => {
    state.filters.type = e.target.value;
    renderTransactionsTable();
  });

  // Export CSV
  document.getElementById('btn-export-csv').addEventListener('click', () => {
    window.location.href = '/api/export';
  });

  // Settings Modal
  const modalSettings = document.getElementById('modal-settings');
  document.getElementById('btn-settings-modal').addEventListener('click', () => {
    if (state.summary && state.summary.settings) {
      document.getElementById('setting-start-balance').value = state.summary.settings.starting_balance || 0;
      document.getElementById('setting-target-reserve').value = state.summary.settings.target_reserve || 5000;
    }
    modalSettings.classList.remove('hidden');
  });
  document.getElementById('btn-close-settings').addEventListener('click', () => modalSettings.classList.add('hidden'));
  document.getElementById('btn-cancel-settings').addEventListener('click', () => modalSettings.classList.add('hidden'));

  document.getElementById('form-settings').addEventListener('submit', async (e) => {
    e.preventDefault();
    const payload = {
      starting_balance: document.getElementById('setting-start-balance').value,
      target_reserve: document.getElementById('setting-target-reserve').value
    };
    await fetch('/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    modalSettings.classList.add('hidden');
    loadData();
  });

  // Edit Transaction Modal
  const modalEdit = document.getElementById('modal-edit');
  document.getElementById('btn-close-edit').addEventListener('click', () => modalEdit.classList.add('hidden'));
  document.getElementById('btn-cancel-edit').addEventListener('click', () => modalEdit.classList.add('hidden'));

  document.getElementById('form-edit-transaction').addEventListener('submit', async (e) => {
    e.preventDefault();
    const id = document.getElementById('edit-id').value;
    const payload = {
      type: document.getElementById('edit-type').value,
      amount: parseFloat(document.getElementById('edit-amount').value),
      category: document.getElementById('edit-category').value,
      date: document.getElementById('edit-date').value,
      note: document.getElementById('edit-note').value,
      is_recurring: document.getElementById('edit-recurring').checked ? 1 : 0
    };

    const res = await fetch(`/api/transactions/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      modalEdit.classList.add('hidden');
      loadData();
    }
  });

  // Exact Salary Simulation Controls
  const inputSalary = document.getElementById('input-exact-salary');
  const sliderSalary = document.getElementById('slider-salary');
  const sliderFixed = document.getElementById('slider-fixed');
  const sliderVariable = document.getElementById('slider-variable');

  inputSalary.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value) || 0;
    sliderSalary.value = val;
    state.scenario.scenario_monthly_income = val;
    updateSalaryDeltaBadge(val);
    runScenarioSimulation();
  });

  sliderSalary.addEventListener('input', (e) => {
    const val = parseFloat(e.target.value) || 0;
    inputSalary.value = val;
    state.scenario.scenario_monthly_income = val;
    updateSalaryDeltaBadge(val);
    runScenarioSimulation();
  });

  sliderFixed.addEventListener('input', (e) => {
    const val = parseInt(e.target.value);
    document.getElementById('val-fixed').textContent = `${val >= 0 ? '+' : ''}€${val}`;
    state.scenario.fixed_delta_eur = val;
    runScenarioSimulation();
  });

  sliderVariable.addEventListener('input', (e) => {
    const val = parseInt(e.target.value);
    document.getElementById('val-variable').textContent = `${val >= 0 ? '+' : ''}${val}%`;
    state.scenario.variable_delta_pct = val;
    runScenarioSimulation();
  });

  document.getElementById('btn-reset-scenarios').addEventListener('click', () => {
    syncScenarioBaseline(true);
    sliderFixed.value = 0;
    sliderVariable.value = 0;
    document.getElementById('val-fixed').textContent = '€0';
    document.getElementById('val-variable').textContent = '0%';
    state.scenario.fixed_delta_eur = 0;
    state.scenario.variable_delta_pct = 0;
    runScenarioSimulation();
  });
}

function updateSalaryDeltaBadge(salary) {
  const baseSalary = state.summary ? state.summary.total_income : 0;
  const delta = salary - baseSalary;
  const badge = document.getElementById('badge-salary-delta');
  if (Math.abs(delta) < 0.01) {
    badge.textContent = 'Current Baseline';
    badge.style.background = 'var(--accent-primary)';
    badge.style.color = '#0f172a';
  } else if (delta > 0) {
    badge.textContent = `+${formatEUR(delta)} vs base`;
    badge.style.background = 'var(--color-success)';
    badge.style.color = '#fff';
  } else {
    badge.textContent = `${formatEUR(delta)} vs base`;
    badge.style.background = 'var(--color-danger)';
    badge.style.color = '#fff';
  }
}

function syncScenarioBaseline(forceReset = false) {
  if (!state.summary) return;
  const baseIncome = state.summary.total_income || 0;
  document.getElementById('lbl-base-salary').textContent = formatEUR(baseIncome);

  const inputSalary = document.getElementById('input-exact-salary');
  const sliderSalary = document.getElementById('slider-salary');

  // Set slider max to at least 2x current income or 10,000
  const maxScale = Math.max(10000, Math.ceil((baseIncome * 2.5) / 1000) * 1000);
  sliderSalary.max = maxScale;

  if (state.scenario.scenario_monthly_income === null || forceReset) {
    state.scenario.scenario_monthly_income = baseIncome;
    inputSalary.value = baseIncome;
    sliderSalary.value = baseIncome;
    updateSalaryDeltaBadge(baseIncome);
  }
}

// --- Data Fetching ---
async function loadData() {
  try {
    const [txRes, sumRes] = await Promise.all([
      fetch('/api/transactions'),
      fetch('/api/summary')
    ]);

    const txData = await txRes.json();
    const sumData = await sumRes.json();

    state.transactions = txData.transactions || [];
    state.summary = sumData;

    renderKPIs();
    renderTransactionsTable();
    renderCategoryBars();

    // If on scenario tab, update simulation
    const activeTab = document.querySelector('.tab-btn.active');
    if (activeTab && activeTab.dataset.tab === 'tab-scenarios') {
      syncScenarioBaseline();
      runScenarioSimulation();
    }
  } catch (err) {
    console.error("Failed to load dashboard data", err);
  }
}

// --- Render Functions ---
function renderKPIs() {
  const s = state.summary;
  if (!s) return;

  document.getElementById('kpi-current-balance').textContent = formatEUR(s.current_balance);
  document.getElementById('kpi-monthly-income').textContent = formatEUR(s.total_income);
  document.getElementById('kpi-recurring-income').textContent = formatEUR(s.recurring_income);
  document.getElementById('kpi-monthly-expense').textContent = formatEUR(s.total_expense);
  document.getElementById('kpi-recurring-expense').textContent = formatEUR(s.recurring_fixed_expense);

  const runwayEl = document.getElementById('kpi-runway');
  if (s.runway.is_infinite) {
    runwayEl.textContent = 'Infinite ♾️';
    runwayEl.className = 'kpi-value text-success';
  } else {
    runwayEl.textContent = `${s.runway.months} mos`;
    runwayEl.className = s.runway.months < 3 ? 'kpi-value text-danger' : 'kpi-value text-info';
  }

  const netFlow = s.net_savings;
  const netFlowEl = document.getElementById('kpi-net-flow');
  netFlowEl.textContent = `Net: ${netFlow >= 0 ? '+' : ''}${formatEUR(netFlow)} / mo`;
  netFlowEl.style.color = netFlow >= 0 ? 'var(--color-success)' : 'var(--color-danger)';
}

function renderCategoryBars() {
  const container = document.getElementById('category-bars');
  if (!state.summary || !state.summary.category_breakdown || state.summary.category_breakdown.length === 0) {
    container.innerHTML = '<p class="text-muted">No expenses recorded yet.</p>';
    return;
  }

  const totalExpense = state.summary.total_expense || 1;
  const html = state.summary.category_breakdown.map(item => {
    const pct = Math.round((item.total / totalExpense) * 100);
    return `
      <div class="cat-bar-item">
        <div class="cat-bar-header">
          <span>${item.category}</span>
          <span><strong>${formatEUR(item.total)}</strong> (${pct}%)</span>
        </div>
        <div class="cat-progress-bg">
          <div class="cat-progress-fill" style="width: ${pct}%;"></div>
        </div>
      </div>
    `;
  }).join('');

  container.innerHTML = html;
}

function renderTransactionsTable() {
  const tbody = document.getElementById('transactions-table-body');
  let list = state.transactions;

  if (state.filters.type) {
    list = list.filter(t => t.type === state.filters.type);
  }
  if (state.filters.search) {
    const q = state.filters.search.toLowerCase();
    list = list.filter(t => 
      (t.category && t.category.toLowerCase().includes(q)) || 
      (t.note && t.note.toLowerCase().includes(q))
    );
  }

  if (list.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No matching transactions.</td></tr>';
    return;
  }

  tbody.innerHTML = list.map(t => {
    const isIncome = t.type === 'income';
    const sign = isIncome ? '+' : '-';
    const colorClass = isIncome ? 'text-success' : 'text-danger';
    return `
      <tr>
        <td>${t.date}</td>
        <td><span class="category-badge">${t.category}</span></td>
        <td>${t.note || '-'}</td>
        <td class="${colorClass}"><strong>${sign}${formatEUR(t.amount)}</strong></td>
        <td>${t.is_recurring ? '🔁 Yes' : 'No'}</td>
        <td>
          <button class="btn btn-edit-sm" onclick="openEditModal(${t.id})">Edit</button>
          <button class="btn btn-danger-sm" onclick="deleteTransaction(${t.id})">Delete</button>
        </td>
      </tr>
    `;
  }).join('');
}

window.openEditModal = function(id) {
  const tx = state.transactions.find(t => t.id === id);
  if (!tx) return;

  document.getElementById('edit-id').value = tx.id;
  document.getElementById('edit-type').value = tx.type;
  document.getElementById('edit-amount').value = tx.amount;
  document.getElementById('edit-category').value = tx.category;
  document.getElementById('edit-date').value = tx.date;
  document.getElementById('edit-note').value = tx.note || '';
  document.getElementById('edit-recurring').checked = tx.is_recurring === 1;

  document.getElementById('modal-edit').classList.remove('hidden');
};

window.deleteTransaction = async function(id) {
  if (!confirm("Are you sure you want to delete this transaction?")) return;
  const res = await fetch(`/api/transactions/${id}`, { method: 'DELETE' });
  if (res.ok) {
    loadData();
  }
};

// --- Scenario & Runway Simulation ---
async function runScenarioSimulation() {
  if (!state.summary) return;

  const targetSalary = state.scenario.scenario_monthly_income !== null 
    ? state.scenario.scenario_monthly_income 
    : state.summary.total_income;

  const payload = {
    starting_balance: state.summary.current_balance,
    base_monthly_income: state.summary.total_income,
    base_fixed_expense: state.summary.recurring_fixed_expense,
    base_variable_expense: state.summary.variable_expense,
    scenario_monthly_income: targetSalary,
    fixed_delta_eur: state.scenario.fixed_delta_eur,
    variable_delta_pct: state.scenario.variable_delta_pct,
    months: 12
  };

  try {
    const res = await fetch('/api/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const sim = await res.json();
    renderScenarioResults(sim);
  } catch (err) {
    console.error("Simulation error", err);
  }
}

function renderScenarioResults(sim) {
  const p3 = sim["3_month_scenario_balance"];
  const p6 = sim["6_month_scenario_balance"];
  const p12 = sim["12_month_scenario_balance"];

  const b3 = sim.baseline_timeline[2].projected_balance;
  const b6 = sim.baseline_timeline[5].projected_balance;
  const b12 = sim.baseline_timeline[11].projected_balance;

  document.getElementById('proj-3m').textContent = formatEUR(p3);
  document.getElementById('proj-6m').textContent = formatEUR(p6);
  document.getElementById('proj-12m').textContent = formatEUR(p12);

  formatDelta('proj-3m-delta', p3 - b3);
  formatDelta('proj-6m-delta', p6 - b6);
  formatDelta('proj-12m-delta', p12 - b12);

  // Generate dynamic insight
  const insightEl = document.getElementById('scenario-insight-text');
  const netMonthly = sim.scenario_monthly_net;
  let text = '';
  if (netMonthly > 0) {
    text = `With a monthly salary of <strong>${formatEUR(sim.scenario_monthly_income)}</strong>, your net monthly surplus will be <strong>+${formatEUR(netMonthly)}</strong>. By month 12, your projected balance reaches <strong>${formatEUR(p12)}</strong>.`;
  } else if (netMonthly === 0) {
    text = `At <strong>${formatEUR(sim.scenario_monthly_income)}</strong>/month, you are breaking even (€0 net monthly). Your balance remains static at <strong>${formatEUR(sim.starting_balance)}</strong>.`;
  } else {
    const burn = Math.abs(netMonthly);
    const monthsLeft = (sim.starting_balance / burn).toFixed(1);
    text = `<span class="text-danger">⚠️ At <strong>${formatEUR(sim.scenario_monthly_income)}</strong>/month, you have a monthly deficit of <strong>-${formatEUR(burn)}</strong>.</span> Your balance will deplete in <strong>${monthsLeft} months</strong>.`;
  }
  insightEl.innerHTML = text;

  // Draw pure canvas line chart
  drawScenarioCanvas(sim);
}

function formatDelta(elemId, delta) {
  const el = document.getElementById(elemId);
  if (Math.abs(delta) < 0.01) {
    el.textContent = 'Identical to baseline';
    el.className = 'proj-delta font-sm text-muted';
  } else if (delta > 0) {
    el.textContent = `+${formatEUR(delta)} vs baseline`;
    el.className = 'proj-delta font-sm text-success';
  } else {
    el.textContent = `${formatEUR(delta)} vs baseline`;
    el.className = 'proj-delta font-sm text-danger';
  }
}

// Lightweight Canvas Charting (Zero dependencies)
function drawScenarioCanvas(sim) {
  const canvas = document.getElementById('scenario-chart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const w = canvas.width;
  const h = canvas.height;

  ctx.clearRect(0, 0, w, h);

  const baselinePts = [sim.starting_balance, ...sim.baseline_timeline.map(t => t.projected_balance)];
  const scenarioPts = [sim.starting_balance, ...sim.scenario_timeline.map(t => t.projected_balance)];

  const allVals = [...baselinePts, ...scenarioPts];
  let minVal = Math.min(...allVals);
  let maxVal = Math.max(...allVals);

  // Add 10% breathing room
  if (minVal === maxVal) {
    minVal -= 100;
    maxVal += 100;
  } else {
    const pad = (maxVal - minVal) * 0.1;
    minVal -= pad;
    maxVal += pad;
  }

  const padLeft = 70;
  const padRight = 30;
  const padTop = 20;
  const padBottom = 35;
  const plotW = w - padLeft - padRight;
  const plotH = h - padTop - padBottom;

  const getX = (i) => padLeft + (i / 12) * plotW;
  const getY = (val) => padTop + plotH - ((val - minVal) / (maxVal - minVal)) * plotH;

  // Grid lines
  ctx.strokeStyle = '#334155';
  ctx.lineWidth = 1;
  ctx.font = '11px sans-serif';
  ctx.fillStyle = '#94a3b8';

  const steps = 4;
  for (let s = 0; s <= steps; s++) {
    const val = minVal + (s / steps) * (maxVal - minVal);
    const y = getY(val);
    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(w - padRight, y);
    ctx.stroke();
    ctx.fillText(`€${Math.round(val)}`, 10, y + 4);
  }

  // Draw X axis labels (Months 0 to 12)
  for (let m = 0; m <= 12; m += 2) {
    const x = getX(m);
    ctx.fillText(m === 0 ? 'Now' : `M${m}`, x - 10, h - 10);
  }

  // Draw Baseline (Grey dashed line)
  ctx.save();
  ctx.setLineDash([4, 4]);
  ctx.strokeStyle = '#94a3b8';
  ctx.lineWidth = 2;
  ctx.beginPath();
  baselinePts.forEach((v, idx) => {
    const x = getX(idx);
    const y = getY(v);
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();
  ctx.restore();

  // Draw Scenario (Bright Blue line)
  ctx.strokeStyle = '#38bdf8';
  ctx.lineWidth = 3;
  ctx.beginPath();
  scenarioPts.forEach((v, idx) => {
    const x = getX(idx);
    const y = getY(v);
    if (idx === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.stroke();

  // Points on scenario
  ctx.fillStyle = '#38bdf8';
  scenarioPts.forEach((v, idx) => {
    const x = getX(idx);
    const y = getY(v);
    ctx.beginPath();
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();
  });
}
