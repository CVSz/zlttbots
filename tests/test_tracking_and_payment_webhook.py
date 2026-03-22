from __future__ import annotations

from fastapi.testclient import TestClient

from services.payment import webhook as payment_webhook
from services.tracking import server as tracking_server


class StubCursor:
    def __init__(self):
        self.executed: list[tuple[str, tuple[object, ...]]] = []

    def execute(self, query: str, params: tuple[object, ...]):
        self.executed.append((query, params))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class StubConn:
    def __init__(self):
        self.cursor_instance = StubCursor()

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_tracking_redirects_with_click_id(monkeypatch):
    conn = StubConn()
    monkeypatch.setattr(tracking_server, "AFFILIATE_BASE_URL", "https://aff.example/offer")
    monkeypatch.setattr(tracking_server, "_connect", lambda: conn)

    client = TestClient(tracking_server.app)
    response = client.get("/t/cmp-100", follow_redirects=False)

    assert response.status_code == 307
    location = response.headers["location"]
    assert location.startswith("https://aff.example/offer?cid=cmp-100&click_id=")
    assert len(conn.cursor_instance.executed) == 1


def test_payment_webhook_records_payment(monkeypatch):
    events: list[tuple[str, tuple[object, ...]]] = []

    class StubDB(payment_webhook.DBExecutor):
        def execute(self, query: str, params: tuple[object, ...]) -> None:
            events.append((query, params))

    monkeypatch.setattr(
        payment_webhook,
        "_verify_event",
        lambda payload, signature: {
            "id": "evt_1",
            "type": "payment_intent.succeeded",
            "data": {
                "object": {
                    "amount": 2599,
                    "metadata": {"campaign_id": "cmp-22", "click_id": "clk-9"},
                }
            },
        },
    )
    monkeypatch.setattr(payment_webhook, "_default_db", lambda: StubDB())

    client = TestClient(payment_webhook.app)
    response = client.post("/webhook", content=b"{}", headers={"stripe-signature": "sig"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert len(events) == 2
