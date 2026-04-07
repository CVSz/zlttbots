import json
from pathlib import Path


def generate_patch(sarif_path: str) -> str:
    path = Path(sarif_path)
    if not path.exists() or path.suffix != ".sarif":
        raise ValueError("sarif_path must be an existing .sarif file")

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    runs = data.get("runs", [])
    if not runs:
        return "# No findings.\n"

    results = runs[0].get("results", [])
    if not results:
        return "# No findings.\n"

    lines: list[str] = []
    for index, result in enumerate(results, start=1):
        rule = result.get("ruleId", "unknown-rule")
        message = result.get("message", {}).get("text", "No message provided")
        lines.append(f"## Finding {index}")
        lines.append(f"- Rule: {rule}")
        lines.append(f"- Issue: {message}")
        lines.append("- Proposed fix: Manual review required before merge.")
        lines.append("")

    return "\n".join(lines).strip() + "\n"
