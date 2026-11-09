"""
Database management module for Personal Expense Tracker.
Uses embedded SQLite to store transactions and user preferences locally.
"""

import os
import sqlite3
from typing import List, Dict, Any, Optional

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
    conn.close()


def add_transaction(
    db_path: str,
    tx_date: str,
    tx_type: str,
    category: str,
    amount: float,
    note: str = "",
    is_recurring: int = 0
) -> int:
    conn = get_connection(db_path)
    with conn:
        cursor = conn.execute(
            """
            INSERT INTO transactions (date, type, category, amount, note, is_recurring)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (tx_date, tx_type, category, float(amount), note, int(is_recurring))
        )
        tx_id = cursor.lastrowid
    conn.close()
    return tx_id


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
