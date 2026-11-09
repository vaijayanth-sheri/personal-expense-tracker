import os
import unittest
import tempfile
import sqlite3
from datetime import date
import database

class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_expenses.db")
        database.init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_init_db_creates_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        self.assertIn("transactions", tables)
        self.assertIn("settings", tables)

    def test_add_and_get_transaction(self):
        t_id = database.add_transaction(
            db_path=self.db_path,
            tx_date="2026-11-09",
            tx_type="expense",
            category="Food",
            amount=45.50,
            note="Grocery shopping",
            is_recurring=0
        )
        self.assertIsInstance(t_id, int)
        
        txs = database.get_transactions(db_path=self.db_path)
        self.assertEqual(len(txs), 1)
        self.assertEqual(txs[0]["category"], "Food")
        self.assertEqual(txs[0]["amount"], 45.50)
        self.assertEqual(txs[0]["type"], "expense")
        self.assertEqual(txs[0]["is_recurring"], 0)

    def test_update_transaction(self):
        t_id = database.add_transaction(
            db_path=self.db_path,
            tx_date="2026-11-09",
            tx_type="expense",
            category="Transport",
            amount=15.00,
            note="Train ticket",
            is_recurring=0
        )
        database.update_transaction(
            db_path=self.db_path,
            tx_id=t_id,
            tx_date="2026-11-09",
            tx_type="expense",
            category="Transport",
            amount=18.50,
            note="Train & tram ticket",
            is_recurring=0
        )
        tx = database.get_transaction_by_id(db_path=self.db_path, tx_id=t_id)
        self.assertIsNotNone(tx)
        self.assertEqual(tx["amount"], 18.50)
        self.assertEqual(tx["note"], "Train & tram ticket")

    def test_delete_transaction(self):
        t_id = database.add_transaction(
            db_path=self.db_path,
            tx_date="2026-11-09",
            tx_type="income",
            category="Salary",
            amount=2500.00,
            note="Monthly pay",
            is_recurring=1
        )
        deleted = database.delete_transaction(db_path=self.db_path, tx_id=t_id)
        self.assertTrue(deleted)
        txs = database.get_transactions(db_path=self.db_path)
        self.assertEqual(len(txs), 0)

    def test_summary_and_recurring(self):
        database.add_transaction(self.db_path, "2026-11-01", "income", "Salary", 3000.0, "Salary", 1)
        database.add_transaction(self.db_path, "2026-11-02", "expense", "Rent", 900.0, "Apartment", 1)
        database.add_transaction(self.db_path, "2026-11-05", "expense", "Groceries", 250.0, "Food", 0)

        summary = database.get_summary(self.db_path)
        self.assertEqual(summary["total_income"], 3000.0)
        self.assertEqual(summary["total_expense"], 1150.0)
        self.assertEqual(summary["net_savings"], 1850.0)
        self.assertEqual(summary["recurring_fixed_expense"], 900.0)
        self.assertEqual(summary["recurring_income"], 3000.0)

    def test_settings_storage(self):
        database.set_setting(self.db_path, "starting_balance", "5000.0")
        val = database.get_setting(self.db_path, "starting_balance")
        self.assertEqual(val, "5000.0")

if __name__ == "__main__":
    unittest.main()
