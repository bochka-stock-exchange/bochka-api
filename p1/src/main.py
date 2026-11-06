"""Small, dependency-free exchange API for the P1 engineering exercise."""

from __future__ import annotations

import json
import threading
from collections import defaultdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4


class InputError(Exception):
    """An expected error in a client's request."""


class AuthError(InputError):
    """A missing or invalid demo token."""


class Exchange:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.users = {
            "demo-alice": {"id": "alice", "name": "Алиса"},
            "demo-bob": {"id": "bob", "name": "Боб"},
        }
        self.balances = {
            "alice": {"RUB": 10_000, "BOCH": 0},
            "bob": {"RUB": 10_000, "BOCH": 10},
        }
        self.orders: dict[str, dict] = {}
        self.sequence = 0

    def user(self, authorization: str | None) -> dict:
        if not authorization or not authorization.startswith("TOKEN "):
            raise AuthError("Нужен заголовок Authorization: TOKEN <ключ>")
        user = self.users.get(authorization[6:])
        if user is None:
            raise AuthError("Неизвестный ключ пользователя")
        return user

    def list_orders(self, user_id: str) -> list[dict]:
        return [self.public_order(order) for order in self.orders.values() if order["user_id"] == user_id]

    @staticmethod
    def public_order(order: dict) -> dict:
        return {key: value for key, value in order.items() if key != "locked"}

    def orderbook(self) -> dict:
        sides = {"BUY": defaultdict(int), "SELL": defaultdict(int)}
        for order in self.orders.values():
            if order["status"] in ("NEW", "PARTIALLY_EXECUTED") and order["price"] is not None:
                sides[order["side"]][order["price"]] += order["qty"] - order["filled"]
        return {
            "bids": [{"price": p, "qty": q} for p, q in sorted(sides["BUY"].items(), reverse=True)],
            "asks": [{"price": p, "qty": q} for p, q in sorted(sides["SELL"].items())],
        }

    def create_order(self, user_id: str, data: dict) -> dict:
        if not isinstance(data, dict):
            raise InputError("Тело запроса должно быть JSON-объектом")
        if data.get("ticker") != "BOCH":
            raise InputError("Доступен только тикер BOCH")
        side = data.get("side")
        if side not in ("BUY", "SELL"):
            raise InputError("Направление должно быть BUY или SELL")
        qty = data.get("qty")
        if type(qty) is not int or qty <= 0 or qty > 100_000:
            raise InputError("Количество должно быть целым числом от 1 до 100000")
        price = data.get("price")
        if price is not None and (type(price) is not int or price <= 0 or price > 1_000_000):
            raise InputError("Цена должна быть целым числом от 1 до 1000000")

        opposite = "SELL" if side == "BUY" else "BUY"
        candidates = [
            order for order in self.orders.values()
            if order["side"] == opposite
            and order["user_id"] != user_id
            and order["status"] in ("NEW", "PARTIALLY_EXECUTED")
            and (price is None or (order["price"] <= price if side == "BUY" else order["price"] >= price))
        ]
        candidates.sort(key=lambda order: (order["price"] if side == "BUY" else -order["price"], order["sequence"]))

        if price is None:
            remaining = qty
            cost = 0
            for resting in candidates:
                take = min(remaining, resting["qty"] - resting["filled"])
                cost += take * resting["price"]
                remaining -= take
                if remaining == 0:
                    break
            if remaining:
                raise InputError("В стакане недостаточно встречных заявок для рыночной сделки")
            required = cost if side == "BUY" else qty
        else:
            required = qty * price if side == "BUY" else qty

        currency = "RUB" if side == "BUY" else "BOCH"
        if self.balances[user_id][currency] < required:
            raise InputError(f"Недостаточно {currency} на балансе")

        self.sequence += 1
        order = {
            "id": str(uuid4()), "user_id": user_id, "ticker": "BOCH", "side": side,
            "qty": qty, "price": price, "filled": 0, "status": "NEW", "sequence": self.sequence,
            "locked": required if price is not None else 0,
        }
        if price is not None:
            self.balances[user_id][currency] -= required

        remaining = qty
        for resting in candidates:
            if remaining == 0:
                break
            take = min(remaining, resting["qty"] - resting["filled"])
            trade_price = resting["price"]
            buyer_id = user_id if side == "BUY" else resting["user_id"]
            seller_id = user_id if side == "SELL" else resting["user_id"]
            buy_order = order if side == "BUY" else resting
            sell_order = order if side == "SELL" else resting

            if buy_order["price"] is None:
                self.balances[buyer_id]["RUB"] -= take * trade_price
            else:
                buy_order["locked"] -= take * buy_order["price"]
                self.balances[buyer_id]["RUB"] += take * (buy_order["price"] - trade_price)
            if sell_order["price"] is None:
                self.balances[seller_id]["BOCH"] -= take
            else:
                sell_order["locked"] -= take
            self.balances[buyer_id]["BOCH"] += take
            self.balances[seller_id]["RUB"] += take * trade_price

            order["filled"] += take
            resting["filled"] += take
            resting["status"] = "EXECUTED" if resting["filled"] == resting["qty"] else "PARTIALLY_EXECUTED"
            remaining -= take

        order["status"] = "EXECUTED" if remaining == 0 else ("PARTIALLY_EXECUTED" if order["filled"] else "NEW")
        self.orders[order["id"]] = order
        return self.public_order(order)

    def cancel_order(self, user_id: str, order_id: str) -> dict:
        order = self.orders.get(order_id)
        if order is None or order["user_id"] != user_id:
            raise InputError("Заявка не найдена")
        if order["status"] not in ("NEW", "PARTIALLY_EXECUTED"):
            raise InputError("Можно отменить только активную лимитную заявку")
        currency = "RUB" if order["side"] == "BUY" else "BOCH"
        self.balances[user_id][currency] += order["locked"]
        order["locked"] = 0
        order["status"] = "CANCELLED"
        return self.public_order(order)


class Handler(BaseHTTPRequestHandler):
    exchange: Exchange

    def respond(self, status: HTTPStatus, payload: dict | list) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            body = (Path(__file__).parent / "index.html").read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        try:
            with self.exchange.lock:
                if path == "/api/instruments":
                    payload = [{"ticker": "BOCH", "name": "Акция Бочка"}]
                elif path == "/api/orderbook/BOCH":
                    payload = self.exchange.orderbook()
                elif path in ("/api/me", "/api/balances", "/api/orders") or path.startswith("/api/orders/"):
                    user = self.exchange.user(self.headers.get("Authorization"))
                    if path == "/api/me":
                        payload = user
                    elif path == "/api/balances":
                        payload = self.exchange.balances[user["id"]].copy()
                    elif path == "/api/orders":
                        payload = self.exchange.list_orders(user["id"])
                    else:
                        order = self.exchange.orders.get(path.removeprefix("/api/orders/"))
                        if order is None or order["user_id"] != user["id"]:
                            raise InputError("Заявка не найдена")
                        payload = self.exchange.public_order(order)
                else:
                    self.respond(HTTPStatus.NOT_FOUND, {"error": "Маршрут не найден"})
                    return
            self.respond(HTTPStatus.OK, payload)
        except AuthError as exc:
            self.respond(HTTPStatus.UNAUTHORIZED, {"error": str(exc)})
        except InputError as exc:
            self.respond(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def read_json(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise InputError("Неверная длина запроса") from None
        if length < 0:
            raise InputError("Неверная длина запроса")
        if length > 4096:
            raise InputError("Запрос слишком большой")
        try:
            return json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError):
            raise InputError("Нужен корректный JSON") from None

    def do_POST(self) -> None:
        try:
            if urlparse(self.path).path != "/api/orders":
                self.respond(HTTPStatus.NOT_FOUND, {"error": "Маршрут не найден"})
                return
            with self.exchange.lock:
                user = self.exchange.user(self.headers.get("Authorization"))
                order = self.exchange.create_order(user["id"], self.read_json())
            self.respond(HTTPStatus.CREATED, order)
        except AuthError as exc:
            self.respond(HTTPStatus.UNAUTHORIZED, {"error": str(exc)})
        except InputError as exc:
            self.respond(HTTPStatus.BAD_REQUEST, {"error": str(exc)})

    def do_DELETE(self) -> None:
        try:
            path = urlparse(self.path).path
            if not path.startswith("/api/orders/"):
                self.respond(HTTPStatus.NOT_FOUND, {"error": "Маршрут не найден"})
                return
            with self.exchange.lock:
                user = self.exchange.user(self.headers.get("Authorization"))
                order = self.exchange.cancel_order(user["id"], path.removeprefix("/api/orders/"))
            self.respond(HTTPStatus.OK, order)
        except AuthError as exc:
            self.respond(HTTPStatus.UNAUTHORIZED, {"error": str(exc)})
        except InputError as exc:
            self.respond(HTTPStatus.BAD_REQUEST, {"error": str(exc)})


def create_server(host: str = "127.0.0.1", port: int = 8000) -> ThreadingHTTPServer:
    exchange = Exchange()
    handler = type("ExchangeHandler", (Handler,), {"exchange": exchange})
    return ThreadingHTTPServer((host, port), handler)


if __name__ == "__main__":
    server = create_server()
    print("Биржа Бочка: http://127.0.0.1:8000", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
