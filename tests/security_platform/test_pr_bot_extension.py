from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

import pytest

PR_BOT_ROOT = Path(__file__).resolve().parents[2] / "services" / "pr-bot"
sys.path.insert(0, str(PR_BOT_ROOT))

os.environ.setdefault("GH_APP_ID", "123456")
os.environ.setdefault("GH_WEBHOOK_SECRET", "unit-test-secret")
os.environ.setdefault(
    "GH_PRIVATE_KEY",
    "-----BEGIN PRIVATE KEY-----\\nMIIBVwIBADANBgkqhkiG9w0BAQEFAASCAT8wggE7AgEAAkEAuQ6q7v6jM9U2lUo5\\n50lvYmlJ6S2jY6Q5c4Q1k9QxJ9S4uGdQ4Q7f8o7Ww2wQ3m2k9bFf8n0V0x5x9f8Q\\nJwIDAQABAkEAk7Xw7YV8m3j6v9l3k4s1c8a5p0v2q4r6t8u0w2y4z6A8C0E2G4I6\\nK8M0O2Q4S6U8W0Y2a4c6e8g0i2k4m6o8qQIgf5m7o9q1s3u5w7y9A1C3E5G7I9K1\\nM3O5Q7S9U1W3Y5a7c9eCIFf9h1j3l5n7p9r1t3v5x7z9B1D3F5H7J9L1N3P5R7T9\\nAiBv1x3z5B7D9F1H3J5L7N9P1R3T5V7X9Z1b3d5f7h9j1l3nQIgV7X9Z1b3d5f7h9\\nj1l3n5p7r9t1v3x5z7B9D1F3H5J7L9N1CIE3G5I7K9M1O3Q5S7U9W1Y3a5c7e9g1\\ni3k5m7o9q1s3u5w7y9A\\n-----END PRIVATE KEY-----",
)

from src.memory import ReviewMemoryStore
from src.opa import evaluate_gate
from src.rl import Feedback, ReviewerBandit
from src.security import verify_webhook_signature


def test_gate_blocks_critical_and_warns_medium() -> None:
    result = evaluate_gate(
        [
            {"severity": "critical", "comment": "SQL injection risk"},
            {"severity": "medium", "comment": "Use stricter typing"},
        ]
    )
    assert result["deny"] == ["BLOCKER: SQL injection risk"]
    assert result["warn"] == ["Use stricter typing"]


def test_rl_bandit_updates_weights_deterministically() -> None:
    bandit = ReviewerBandit()
    bandit.update(
        Feedback(repo="acme/repo", accepted=True, severity="high", category="security")
    )
    bandit.update(
        Feedback(repo="acme/repo", accepted=False, severity="low", category="perf")
    )
    snapshot = bandit.snapshot()
    assert snapshot["security"] == pytest.approx(1.1)
    assert snapshot["perf"] == pytest.approx(0.9)
    assert bandit.select_agents()[0] == "security"


def test_verify_signature_uses_hmac_sha256() -> None:
    payload = json.dumps({"event": "pull_request"}).encode("utf-8")
    secret = "abc123"
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    signature = f"sha256={digest}"
    assert verify_webhook_signature(secret, payload, signature)
    assert not verify_webhook_signature(secret, payload, "sha256=deadbeef")


def test_memory_store_validates_embedding_dimensions() -> None:
    store = ReviewMemoryStore(db_url="postgresql://unused", embedding_dimensions=4)
    with pytest.raises(ValueError):
        store.search_similar([0.1, 0.2], limit=1)
