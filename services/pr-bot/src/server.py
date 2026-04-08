from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException, Request

from .config import GitHubAppConfig
from .github_app import GitHubAppAuth
from .opa import evaluate_gate
from .rl import Feedback, ReviewerBandit
from .security import verify_webhook_signature

app = FastAPI(title="pr-bot", version="2.0.0")

_config = GitHubAppConfig.from_env()
_auth = GitHubAppAuth(_config)
_bandit = ReviewerBandit()

@app.get("/healthz")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "pr-bot"}


@app.post("/webhook")
async def webhook(request: Request) -> dict[str, Any]:
    raw = await request.body()
    signature = request.headers.get("x-hub-signature-256")
    event = request.headers.get("x-github-event", "")

    if not verify_webhook_signature(_config.webhook_secret, raw, signature):
        raise HTTPException(status_code=401, detail="invalid signature")

    payload = await request.json()

    if event != "pull_request":
        return {"status": "ignored", "reason": "unsupported_event"}

    action = str(payload.get("action", ""))
    installation_id = int(payload.get("installation", {}).get("id", 0))
    repository = str(payload.get("repository", {}).get("full_name", ""))

    if not installation_id or not repository:
        raise HTTPException(status_code=400, detail="missing installation/repository context")

    installation_token = _auth.get_installation_token(installation_id)
    findings = payload.get("findings", []) if isinstance(payload.get("findings"), list) else []
    gate = evaluate_gate(findings)

    if payload.get("feedback"):
        feedback = payload["feedback"]
        _bandit.update(
            Feedback(
                repo=repository,
                accepted=bool(feedback.get("accepted", False)),
                severity=str(feedback.get("severity", "unknown")),
                category=str(feedback.get("category", "quality")),
            )
        )

    return {
        "status": "processed",
        "action": action,
        "repo": repository,
        "installation_token_expires_at": installation_token.expires_at,
        "gate": gate,
        "agent_priority": _bandit.select_agents(),
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "3000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
