"""
Lightweight embedded HTTP server for Personal Expense Tracker.
Uses standard library http.server to provide zero-overhead REST API
and serve the frontend single-page application.
"""

import os
import json
import csv
import io
import mimetypes
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, Optional

import database
import analytics

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(BASE_DIR, "web")


class ExpenseTrackerHandler(BaseHTTPRequestHandler):
    db_path: str = database.DEFAULT_DB_PATH

    def log_message(self, format: str, *args: Any) -> None:
        # Suppress noisy HTTP request logging to keep console clean
        return

    def _send_json(self, data: Any, status_code: int = 200) -> None:
        response_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_bytes)

    def _read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length)
        return json.loads(body.decode("utf-8"))

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if path.startswith("/api/"):
            self._handle_api_get(path, query)
        else:
            self._serve_static(path)

    def _handle_api_get(self, path: str, query: Dict[str, Any]) -> None:
        # Existing endpoints
        if path == "/api/transactions":
            tx_type = query.get("type", [None])[0]
            category = query.get("category", [None])[0]
            start_date = query.get("start_date", [None])[0]
            end_date = query.get("end_date", [None])[0]
            search = query.get("search", [None])[0]

            transactions = database.get_transactions(
                db_path=self.db_path,
                tx_type=tx_type,
                category=category,
                start_date=start_date,
                end_date=end_date,
                search=search
            )
            self._send_json({"transactions": transactions})
            return
        elif path == "/api/summary":
            summary = database.get_summary(self.db_path)
            settings = database.get_all_settings(self.db_path)
            starting_bal = float(settings.get("starting_balance", "0.0") or 0.0)
            target_reserve = float(settings.get("target_reserve", "5000.0") or 5000.0)

            current_balance = starting_bal + summary["net_savings"]

            variable_expense = max(0.0, summary["total_expense"] - summary["recurring_fixed_expense"])
            net_monthly_burn = summary["total_expense"] - summary["total_income"]
            runway = analytics.calculate_runway(current_balance, net_monthly_burn)

            response = {
                **summary,
                "starting_balance": starting_bal,
                "current_balance": round(current_balance, 2),
                "variable_expense": round(variable_expense, 2),
                "target_reserve": target_reserve,
                "runway": runway,
                "settings": settings
            }
            self._send_json(response)
            return
        elif path == "/api/settings":
            settings = database.get_all_settings(self.db_path)
            self._send_json({"settings": settings})
            return
        elif path == "/api/export":
            # Export transactions as CSV
            transactions = database.get_transactions(self.db_path)
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Date", "Type", "Category", "Amount (EUR)", "Note", "Recurring", "Created At"])
            for t in transactions:
                writer.writerow([
                    t["id"], t["date"], t["type"], t["category"],
                    t["amount"], t["note"], t["is_recurring"], t["created_at"]
                ])
            csv_data = output.getvalue().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=\"personal_expenses.csv\"")
            self.send_header("Content-Length", str(len(csv_data)))
            self.end_headers()
            self.wfile.write(csv_data)
            return
        elif path == "/api/backup":
            # List available backups
            backups = database.list_backups()
            self._send_json({"backups": backups})
            return
        elif path == "/api/duplicate_transactions":
            dup_ids = database.find_duplicate_transactions(self.db_path)
            self._send_json({"duplicate_ids": dup_ids})
            return
        elif path == "/api/budget_limits":
            limits = database.get_budget_limits(self.db_path)
            self._send_json({"budget_limits": limits})
            return
        elif path == "/api/theme":
            prefs = database.get_theme_preferences(self.db_path)
            self._send_json({"theme": prefs})
            return
        else:
            self._send_json({"error": "Endpoint not found"}, 404)
            return
        if path == "/api/transactions":
            tx_type = query.get("type", [None])[0]
            category = query.get("category", [None])[0]
            start_date = query.get("start_date", [None])[0]
            end_date = query.get("end_date", [None])[0]
            search = query.get("search", [None])[0]

            transactions = database.get_transactions(
                db_path=self.db_path,
                tx_type=tx_type,
                category=category,
                start_date=start_date,
                end_date=end_date,
                search=search
            )
            self._send_json({"transactions": transactions})

        elif path == "/api/summary":
            summary = database.get_summary(self.db_path)
            settings = database.get_all_settings(self.db_path)
            starting_bal = float(settings.get("starting_balance", "0.0") or 0.0)
            target_reserve = float(settings.get("target_reserve", "5000.0") or 5000.0)

            current_balance = starting_bal + summary["net_savings"]
            
            # Monthly burn is (recurring_fixed_expense + variable_expense) - total_income
            # If negative, surplus
            variable_expense = max(0.0, summary["total_expense"] - summary["recurring_fixed_expense"])
            net_monthly_burn = summary["total_expense"] - summary["total_income"]
            runway = analytics.calculate_runway(current_balance, net_monthly_burn)

            response = {
                **summary,
                "starting_balance": starting_bal,
                "current_balance": round(current_balance, 2),
                "variable_expense": round(variable_expense, 2),
                "target_reserve": target_reserve,
                "runway": runway,
                "settings": settings
            }
            self._send_json(response)

        elif path == "/api/settings":
            settings = database.get_all_settings(self.db_path)
            self._send_json({"settings": settings})

        elif path == "/api/export":
            # Export transactions as CSV
            transactions = database.get_transactions(self.db_path)
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Date", "Type", "Category", "Amount (EUR)", "Note", "Recurring", "Created At"])
            for t in transactions:
                writer.writerow([
                    t["id"], t["date"], t["type"], t["category"],
                    t["amount"], t["note"], t["is_recurring"], t["created_at"]
                ])
            csv_data = output.getvalue().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", "attachment; filename=\"personal_expenses.csv\"")
            self.send_header("Content-Length", str(len(csv_data)))
            self.end_headers()
            self.wfile.write(csv_data)

        else:
            self._send_json({"error": "Endpoint not found"}, 404)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/transactions":
            body = self._read_json_body()
            try:
                tx_id = database.add_transaction(
                    db_path=self.db_path,
                    tx_date=body.get("date"),
                    tx_type=body.get("type"),
                    category=body.get("category", "Other"),
                    amount=float(body.get("amount", 0.0)),
                    note=body.get("note", ""),
                    is_recurring=int(body.get("is_recurring", 0))
                )
                self._send_json({"success": True, "id": tx_id}, 201)
            except Exception as e:
                self._send_json({"error": str(e)}, 400)

        elif path == "/api/settings":
            body = self._read_json_body()
            for k, v in body.items():
                database.set_setting(self.db_path, str(k), str(v))
            self._send_json({"success": True})

        elif path == "/api/simulate":
            body = self._read_json_body()
            scen_income = body.get("scenario_monthly_income")
            if scen_income is not None:
                scen_income = float(scen_income)

            res = analytics.simulate_scenarios(
                starting_balance=float(body.get("starting_balance", 0.0)),
                base_monthly_income=float(body.get("base_monthly_income", 0.0)),
                base_fixed_expense=float(body.get("base_fixed_expense", 0.0)),
                base_variable_expense=float(body.get("base_variable_expense", 0.0)),
                income_delta_pct=float(body.get("income_delta_pct", 0.0)),
                scenario_monthly_income=scen_income,
                fixed_delta_eur=float(body.get("fixed_delta_eur", 0.0)),
                variable_delta_pct=float(body.get("variable_delta_pct", 0.0)),
                months=int(body.get("months", 12))
            )
            self._send_json(res)

        else:
            self._send_json({"error": "Endpoint not found"}, 404)

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/transactions/"):
            try:
                tx_id = int(path.split("/")[-1])
                body = self._read_json_body()
                success = database.update_transaction(
                    db_path=self.db_path,
                    tx_id=tx_id,
                    tx_date=body.get("date"),
                    tx_type=body.get("type"),
                    category=body.get("category", "Other"),
                    amount=float(body.get("amount", 0.0)),
                    note=body.get("note", ""),
                    is_recurring=int(body.get("is_recurring", 0))
                )
                self._send_json({"success": success})
            except Exception as e:
                self._send_json({"error": str(e)}, 400)
        else:
            self._send_json({"error": "Endpoint not found"}, 404)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/transactions/"):
            try:
                tx_id = int(path.split("/")[-1])
                success = database.delete_transaction(self.db_path, tx_id)
                self._send_json({"success": success})
            except Exception as e:
                self._send_json({"error": str(e)}, 400)
        else:
            self._send_json({"error": "Endpoint not found"}, 404)

    def _serve_static(self, path: str) -> None:
        if path == "/" or not path:
            path = "/index.html"

        safe_path = os.path.normpath(path.lstrip("/"))
        file_path = os.path.join(WEB_DIR, safe_path)

        if not os.path.commonpath([WEB_DIR, file_path]).startswith(WEB_DIR) or not os.path.isfile(file_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"File Not Found")
            return

        content_type, _ = mimetypes.guess_type(file_path)
        content_type = content_type or "application/octet-stream"

        with open(file_path, "rb") as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def create_server(host: str = "127.0.0.1", port: int = 5055, db_path: str = database.DEFAULT_DB_PATH) -> HTTPServer:
    database.init_db(db_path)
    handler_class = type("CustomExpenseTrackerHandler", (ExpenseTrackerHandler,), {"db_path": db_path})
    return HTTPServer((host, port), handler_class)


if __name__ == "__main__":
    server_address = ("127.0.0.1", 5055)
    httpd = create_server(server_address[0], server_address[1])
    print(f"Personal Expense Tracker running on http://{server_address[0]}:{server_address[1]}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()
