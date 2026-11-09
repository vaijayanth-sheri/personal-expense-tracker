import os
import json
import unittest
import tempfile
import urllib.request
import urllib.error
import threading
import server
import database

class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = os.path.join(cls.temp_dir.name, "server_test.db")
        database.init_db(cls.db_path)
        cls.port = 5098
        cls.httpd = server.create_server(host="127.0.0.1", port=cls.port, db_path=cls.db_path)
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.temp_dir.cleanup()

    def test_post_and_get_transaction(self):
        url = f"{self.base_url}/api/transactions"
        payload = {
            "date": "2026-11-09",
            "type": "expense",
            "category": "Dining",
            "amount": 25.50,
            "note": "Lunch with friends",
            "is_recurring": 0
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 201)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            tx_id = data.get("id")

        # GET transactions
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(len(data["transactions"]) >= 1)
            found = any(t["id"] == tx_id for t in data["transactions"])
            self.assertTrue(found)

    def test_get_summary_api(self):
        url = f"{self.base_url}/api/summary"
        with urllib.request.urlopen(url) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("total_income", data)
            self.assertIn("total_expense", data)
            self.assertIn("category_breakdown", data)

    def test_simulate_api_exact_salary(self):
        url = f"{self.base_url}/api/simulate"
        payload = {
            "starting_balance": 4000.0,
            "base_monthly_income": 3000.0,
            "base_fixed_expense": 1000.0,
            "base_variable_expense": 1000.0,
            "scenario_monthly_income": 3800.0,
            "fixed_delta_eur": 0.0,
            "variable_delta_pct": 0.0
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["scenario_monthly_income"], 3800.0)
            self.assertEqual(data["scenario_monthly_net"], 1800.0)

    def test_simulate_api(self):
        url = f"{self.base_url}/api/simulate"
        payload = {
            "starting_balance": 4000.0,
            "base_monthly_income": 3000.0,
            "base_fixed_expense": 1000.0,
            "base_variable_expense": 1000.0,
            "income_delta_pct": 10.0,
            "fixed_delta_eur": 0.0,
            "variable_delta_pct": -10.0
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("scenario_timeline", data)
            self.assertIn("scenario_monthly_net", data)

if __name__ == "__main__":
    unittest.main()
