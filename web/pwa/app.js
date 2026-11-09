// app.js – Mobile PWA logic (ES6 module)

// Adjust API_ROOT to your PC's Tailscale IP + port. Example placeholder:
const API_ROOT = 'http://100.101.102.103:5055'; // replace with actual IP

// Open (or create) IndexedDB
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('expense-pwa', 1);
    request.onupgradeneeded = (e) => {
      const db = e.target.result;
      const store = db.createObjectStore('pending', { keyPath: 'client_tx_id' });
      store.createIndex('status', 'status', { unique: false });
    };
    request.onsuccess = (e) => resolve(e.target.result);
    request.onerror = (e) => reject(e.target.error);
  });
}

async function addPending(tx) {
  const db = await openDB();
  const txStore = db.transaction('pending', 'readwrite').objectStore('pending');
  txStore.add({ ...tx, status: 'pending', retryCount: 0, createdAt: Date.now() });
  db.close();
  renderStatus();
}

async function getAllPending() {
  const db = await openDB();
  const store = db.transaction('pending', 'readonly').objectStore('pending');
  const all = await store.getAll();
  db.close();
  return all;
}

async function updateTx(id, changes) {
  const db = await openDB();
  const store = db.transaction('pending', 'readwrite').objectStore('pending');
  const rec = await store.get(id);
  if (rec) {
    Object.assign(rec, changes);
    store.put(rec);
  }
  db.close();
}

async function syncPending() {
  const pending = await getAllPending();
  for (const tx of pending) {
    if (tx.status !== 'pending') continue;
    try {
      const resp = await fetch(`${API_ROOT}/api/transactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          date: tx.date,
          type: tx.type,
          category: tx.category,
          amount: tx.amount,
          note: tx.note,
          is_recurring: Number(tx.is_recurring),
          client_tx_id: tx.client_tx_id,
        }),
      });
      if (resp.ok) {
        await updateTx(tx.client_tx_id, { status: 'synced' });
      } else if (resp.status === 409) {
        // Already exists – treat as synced
        await updateTx(tx.client_tx_id, { status: 'synced' });
      } else {
        const err = await resp.text();
        await updateTx(tx.client_tx_id, { status: 'failed', error: err });
      }
    } catch (e) {
      // Network error – keep pending, maybe increase retryCount
      const rc = (tx.retryCount || 0) + 1;
      await updateTx(tx.client_tx_id, { retryCount: rc });
    }
  }
  renderStatus();
}

function renderStatus() {
  getAllPending().then((list) => {
    const container = document.getElementById('statusList');
    container.innerHTML = '';
    list.forEach((tx) => {
      const div = document.createElement('div');
      div.className = 'status-item';
      div.innerHTML = `
        <strong>${tx.date}</strong> – ${tx.type} – ${tx.category} – €${tx.amount}<br>
        Status: <span>${tx.status}</span>
        ${tx.error ? `<br><em>${tx.error}</em>` : ''}
        ${tx.status === 'failed' ? `<button data-id="${tx.client_tx_id}">Retry</button>` : ''}
      `;
      container.appendChild(div);
    });
    // attach retry handlers
    container.querySelectorAll('button').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const id = btn.getAttribute('data-id');
        await updateTx(id, { status: 'pending' });
        await syncPending();
      });
    });
  });
}

// Form handling
document.getElementById('txForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const tx = {
    client_tx_id: crypto.randomUUID(),
    date: document.getElementById('date').value,
    type: document.getElementById('type').value,
    category: document.getElementById('category').value,
    amount: parseFloat(document.getElementById('amount').value),
    note: document.getElementById('note').value,
    is_recurring: document.getElementById('is_recurring').value,
  };
  await addPending(tx);
  // optimistic UI – clear form
  e.target.reset();
});

// Register service worker & background sync
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('service-worker.js').then(() => {
    // try immediate sync if online
    if (navigator.onLine) syncPending();
  });
}

// Listen to online/offline events
window.addEventListener('online', () => syncPending());

// Initial render
renderStatus();
