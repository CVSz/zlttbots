import json
from pathlib import Path

import importlib.util

MODULE_PATH = Path("services/ai-fix/src/engine.py")
SPEC = importlib.util.spec_from_file_location("ai_fix_engine", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_generate_patch(tmp_path: Path) -> None:
    sarif_path = tmp_path / "result.sarif"
    sarif_path.write_text(
        json.dumps(
            {
                "runs": [
                    {
                        "results": [
                            {"ruleId": "py/sql-injection", "message": {"text": "Unsanitized SQL query"}}
                        ]
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    patch = MODULE.generate_patch(str(sarif_path))
    assert "py/sql-injection" in patch
    assert "Unsanitized SQL query" in patch
