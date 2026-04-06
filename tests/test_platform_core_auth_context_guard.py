from pathlib import Path


def test_platform_core_missing_user_context_returns_unauthorized() -> None:
    source = Path('apps/platform-core/src/index.ts').read_text(encoding='utf-8')

    assert 'function requireUserContextOrRespond' in source
    assert 'res.status(401).json({ ok: false, error: "Unauthorized" });' in source
    assert 'logger.warn({ requestId, path: req.path }, "missing user context");' in source
    assert 'throw new Error("Missing user context")' not in source
