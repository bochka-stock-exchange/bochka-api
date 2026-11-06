"""Behavior checks for the P1 exchange, including invalid input."""

import json
import sys
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from main import Exchange, InputError, create_server  # noqa: E402


class ExchangeTests(unittest.TestCase):
    def setUp(self):
        self.exchange = Exchange()

    def test_limit_and_market_trade(self):
        sell = self.exchange.create_order("bob", {"ticker": "BOCH", "side": "SELL", "qty": 2, "price": 100})
        self.assertEqual(self.exchange.balances["bob"]["BOCH"], 8)
        self.assertEqual(self.exchange.orderbook()["asks"], [{"price": 100, "qty": 2}])
        buy = self.exchange.create_order("alice", {"ticker": "BOCH", "side": "BUY", "qty": 1, "price": None})
        self.assertEqual(buy["status"], "EXECUTED")
        self.assertEqual(self.exchange.orders[sell["id"]]["status"], "PARTIALLY_EXECUTED")
        self.assertEqual(self.exchange.balances["alice"], {"RUB": 9900, "BOCH": 1})
        self.assertEqual(self.exchange.balances["bob"], {"RUB": 10100, "BOCH": 8})
        self.assertEqual(self.exchange.orderbook()["asks"], [{"price": 100, "qty": 1}])

    def test_bad_input_does_not_change_state(self):
        before = self.exchange.balances["alice"].copy()
        with self.assertRaisesRegex(InputError, "Количество"):
            self.exchange.create_order("alice", {"ticker": "BOCH", "side": "BUY", "qty": -1, "price": 100})
        with self.assertRaisesRegex(InputError, "встречных"):
            self.exchange.create_order("alice", {"ticker": "BOCH", "side": "BUY", "qty": 1, "price": None})
        self.assertEqual(self.exchange.balances["alice"], before)
        self.assertEqual(self.exchange.orders, {})

    def test_cancel_refunds_only_owner(self):
        order = self.exchange.create_order("alice", {"ticker": "BOCH", "side": "BUY", "qty": 2, "price": 100})
        self.assertEqual(self.exchange.balances["alice"]["RUB"], 9800)
        with self.assertRaisesRegex(InputError, "не найдена"):
            self.exchange.cancel_order("bob", order["id"])
        cancelled = self.exchange.cancel_order("alice", order["id"])
        self.assertEqual(cancelled["status"], "CANCELLED")
        self.assertEqual(self.exchange.balances["alice"]["RUB"], 10000)
        self.assertEqual(self.exchange.orderbook()["bids"], [])

    def test_aggressive_limit_price_improvement(self):
        self.exchange.create_order("bob", {"ticker": "BOCH", "side": "SELL", "qty": 1, "price": 90})
        buy = self.exchange.create_order("alice", {"ticker": "BOCH", "side": "BUY", "qty": 1, "price": 100})
        self.assertEqual(buy["status"], "EXECUTED")
        self.assertEqual(self.exchange.balances["alice"]["RUB"], 9910)
        self.assertEqual(self.exchange.balances["bob"]["RUB"], 10090)

    def test_cancel_partially_filled_order_returns_remaining_asset(self):
        sell = self.exchange.create_order("bob", {"ticker": "BOCH", "side": "SELL", "qty": 2, "price": 100})
        self.exchange.create_order("alice", {"ticker": "BOCH", "side": "BUY", "qty": 1, "price": None})
        cancelled = self.exchange.cancel_order("bob", sell["id"])
        self.assertEqual(cancelled["status"], "CANCELLED")
        self.assertEqual(cancelled["filled"], 1)
        self.assertEqual(self.exchange.balances["bob"], {"RUB": 10100, "BOCH": 9})
        self.assertEqual(self.exchange.orderbook()["asks"], [])


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, path, method="GET", data=None, token="demo-alice"):
        body = None if data is None else json.dumps(data).encode()
        headers = {} if token is None else {"Authorization": f"TOKEN {token}"}
        req = Request(self.base + path, body, headers, method=method)
        try:
            with urlopen(req, timeout=2) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    def test_html_and_api_flow(self):
        with urlopen(self.base + "/", timeout=2) as response:
            self.assertIn("Торги без лишнего".encode(), response.read())
        status, payload = self.request("/api/orders", "POST", {"ticker": "BOCH", "side": "BUY", "qty": 1, "price": 120})
        self.assertEqual(status, 201)
        self.assertEqual(payload["status"], "NEW")
        status, book = self.request("/api/orderbook/BOCH")
        self.assertEqual(book["bids"], [{"price": 120, "qty": 1}])
        status, payload = self.request(f"/api/orders/{payload['id']}", "DELETE")
        self.assertEqual(payload["status"], "CANCELLED")

    def test_api_rejects_bad_input_and_token(self):
        status, payload = self.request("/api/orders", "POST", {"ticker": "BOCH", "side": "BUY", "qty": 0, "price": 100})
        self.assertEqual(status, 400)
        self.assertIn("Количество", payload["error"])
        status, payload = self.request("/api/balances", token="wrong")
        self.assertEqual(status, 401)
        self.assertIn("ключ", payload["error"])


if __name__ == "__main__":
    unittest.main()
