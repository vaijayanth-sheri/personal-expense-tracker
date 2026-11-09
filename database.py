"""
Database management module for Personal Expense Tracker.
Uses embedded SQLite to store transactions and user preferences locally.
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional
import shutil
import datetime

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "expenses.db")


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    conn = get_connection(db_path)
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('expense', 'income')),
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                note TEXT,
                is_recurring INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budget_limits (
                category TEXT PRIMARY KEY,
                limit_amount REAL NOT NULL
            )
        """)
        try:
            conn.execute("""
                ALTER TABLE transactions ADD COLUMN currency_code TEXT DEFAULT 'EUR'
            """)
        except Exception:
            pass
        conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                frequency TEXT NOT NULL CHECK(frequency IN ('monthly','annual')),
                next_due TEXT NOT NULL,
                note TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS client_tx_refs (
                client_tx_id TEXT PRIMARY KEY,
                server_tx_id INTEGER NOT NULL,
                FOREIGN KEY(server_tx_id) REFERENCES transactions(id)
            )
        """)
    conn.close()


def add_transaction(
    db_path: str,
    tx_date: str,
    tx_type: str,
    category: str,
    amount: float,
    note: str = "",
    is_recurring: int = 0,
    client_tx_id: Optional[str] = None
) -> int:
    """Add a transaction. If `client_tx_id` is provided and already recorded,
    the function returns the existing server transaction ID to avoid duplication."""
    conn = get_connection(db_path)
    # If a client transaction ID is supplied, check for existing mapping
    if client_tx_id:
        cursor = conn.execute(
            "SELECT server_tx_id FROM client_tx_refs WHERE client_tx_id = ?",
            (client_tx_id,)
        )
        row = cursor.fetchone()
        if row:
            # Already synced – return existing server ID
            conn.close()
            return int(row["server_tx_id"])
    with conn:
        cursor = conn.execute(
            """
            INSERT INTO transactions (date, type, category, amount, note, is_recurring)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (tx_date, tx_type, category, float(amount), note, int(is_recurring))
        )
        tx_id = cursor.lastrowid
        # Record client_tx_id mapping if supplied
        if client_tx_id:
            conn.execute(
                "INSERT INTO client_tx_refs (client_tx_id, server_tx_id) VALUES (?, ?)",
                (client_tx_id, tx_id)
            )



def get_transactions(
    db_path: str = DEFAULT_DB_PATH,
    tx_type: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None
) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    query = "SELECT * FROM transactions WHERE 1=1"
    params: List[Any] = []

    if tx_type:
        query += " AND type = ?"
        params.append(tx_type)
    if category:
        query += " AND category = ?"
        params.append(category)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if search:
        query += " AND (note LIKE ? OR category LIKE ?)"
        wildcard = f"%{search}%"
        params.extend([wildcard, wildcard])

    query += " ORDER BY date DESC, id DESC"
    cursor = conn.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(row) for row in rows]
    conn.close()
    return results


def get_transaction_by_id(db_path: str, tx_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_transaction(
    db_path: str,
    tx_id: int,
    tx_date: str,
    tx_type: str,
    category: str,
    amount: float,
    note: str = "",
    is_recurring: int = 0
) -> bool:
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute(
            """
            UPDATE transactions
            SET date = ?, type = ?, category = ?, amount = ?, note = ?, is_recurring = ?
            WHERE id = ?
            """,
            (tx_date, tx_type, category, float(amount), note, int(is_recurring), tx_id)
        )
        updated = cursor.rowcount > 0
    conn.close()
    return updated


def delete_transaction(db_path: str, tx_id: int) -> bool:
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def get_summary(db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    conn = get_connection(db_path)
    
    # Aggregated totals
    cursor = conn.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) as total_income,
            COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) as total_expense,
            COALESCE(SUM(CASE WHEN type = 'income' AND is_recurring = 1 THEN amount ELSE 0 END), 0) as recurring_income,
            COALESCE(SUM(CASE WHEN type = 'expense' AND is_recurring = 1 THEN amount ELSE 0 END), 0) as recurring_fixed_expense
        FROM transactions
    """)
    row = cursor.fetchone()
    
    total_income = float(row["total_income"])
    total_expense = float(row["total_expense"])
    net_savings = total_income - total_expense
    recurring_income = float(row["recurring_income"])
    recurring_fixed_expense = float(row["recurring_fixed_expense"])
    
    # Spending grouped by category
    cat_cursor = conn.execute("""
        SELECT category, COALESCE(SUM(amount), 0) as total
        FROM transactions
        WHERE type = 'expense'
        GROUP BY category
        ORDER BY total DESC
    """)
    category_breakdown = [dict(c_row) for c_row in cat_cursor.fetchall()]

    conn.close()
    return {
        "total_income": round(total_income, 2),
        "total_expense": round(total_expense, 2),
        "net_savings": round(net_savings, 2),
        "recurring_income": round(recurring_income, 2),
        "recurring_fixed_expense": round(recurring_fixed_expense, 2),
        "category_breakdown": category_breakdown
    }


def set_setting(db_path: str, key: str, value: str) -> None:
    conn = get_connection(db_path)
    with conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value)
        )
    conn.close()


def get_setting(db_path: str, key: str, default: Optional[str] = None) -> Optional[str]:
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default


def get_all_settings(db_path: str = DEFAULT_DB_PATH) -> Dict[str, str]:
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT key, value FROM settings")
    settings = {row["key"]: row["value"] for row in cursor.fetchall()}
    conn.close()
    return settings

# Budget limits management
def set_budget_limit(db_path: str, category: str, limit_amount: float) -> None:
    conn = get_connection(db_path)
    with conn:
        conn.execute(
            "INSERT INTO budget_limits (category, limit_amount) VALUES (?, ?) ON CONFLICT(category) DO UPDATE SET limit_amount=excluded.limit_amount",
            (category, limit_amount),
        )
    conn.close()

def get_budget_limits(db_path: str) -> Dict[str, float]:
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT category, limit_amount FROM budget_limits")
    limits = {row["category"]: float(row["limit_amount"]) for row in cursor.fetchall()}
    conn.close()
    return limits

def delete_budget_limit(db_path: str, category: str) -> bool:
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute("DELETE FROM budget_limits WHERE category = ?", (category,))
        deleted = cursor.rowcount > 0
    conn.close()
    return deleted

# Theme preferences management
def set_theme_preference(db_path: str, key: str, value: str) -> None:
    conn = get_connection(db_path)
    with conn:
        conn.execute(
            "INSERT INTO theme_preferences (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
    conn.close()

def get_theme_preferences(db_path: str) -> Dict[str, str]:
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT key, value FROM theme_preferences")
    prefs = {row["key"]: row["value"] for row in cursor.fetchall()}
    conn.close()
    return prefs

# ----- Backup & Restore -----

def backup_database(db_path: str = DEFAULT_DB_PATH, backup_dir: str = os.path.join(os.path.dirname(__file__), 'backups')) -> str:
    """Create a timestamped backup of the SQLite database.
    Returns the backup file path."""
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(backup_dir, f'expenses_backup_{timestamp}.db')
    shutil.copy2(db_path, backup_path)
    return backup_path

def list_backups(backup_dir: str = os.path.join(os.path.dirname(__file__), 'backups')) -> list:
    """Return a list of backup file names sorted newest first."""
    if not os.path.isdir(backup_dir):
        return []
    files = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
    files.sort(reverse=True)
    return files

def restore_database(backup_file: str, db_path: str = DEFAULT_DB_PATH, backup_dir: str = os.path.join(os.path.dirname(__file__), 'backups')) -> bool:
    """Replace the current DB with the specified backup.
    Returns True on success."""
    backup_path = os.path.join(backup_dir, backup_file)
    if not os.path.isfile(backup_path):
        return False
    shutil.copy2(backup_path, db_path)
    return True

# ----- Duplicate detection -----

def find_duplicate_transactions(db_path: str = DEFAULT_DB_PATH) -> list:
    """Return a list of transaction IDs that appear duplicated (same date, amount, category, note)."""
    conn = get_connection(db_path)
    cursor = conn.execute('''
        SELECT id FROM transactions WHERE (date, amount, category, note) IN (
            SELECT date, amount, category, note FROM transactions
            GROUP BY date, amount, category, note HAVING COUNT(*) > 1
        )
        ORDER BY date DESC
    ''')
    dup_ids = [row['id'] for row in cursor.fetchall()]
    conn.close()
    return dup_ids

# Subscription management functions
def add_subscription(db_path: str, name: str, amount: float, frequency: str, next_due: str, note: str = "") -> int:
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute(
            "INSERT INTO subscriptions (name, amount, frequency, next_due, note) VALUES (?, ?, ?, ?, ?)",
            (name, amount, frequency, next_due, note),
        )
        sub_id = cursor.lastrowid
    conn.close()
    return sub_id

def get_subscriptions(db_path: str) -> List[Dict[str, Any]]:
    conn = get_connection(db_path)
    cursor = conn.execute("SELECT * FROM subscriptions")
    subs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return subs

def update_subscription(db_path: str, sub_id: int, name: str, amount: float, frequency: str, next_due: str, note: str = "") -> bool:
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute(
            "UPDATE subscriptions SET name = ?, amount = ?, frequency = ?, next_due = ?, note = ? WHERE id = ?",
            (name, amount, frequency, next_due, note, sub_id),
        )
        updated = cursor.rowcount > 0
    conn.close()
    return updated

def delete_subscription(db_path: str, sub_id: int) -> bool:
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute("DELETE FROM subscriptions WHERE id = ?", (sub_id,))
        deleted = cursor.rowcount > 0
    conn.close()
    return deleted

