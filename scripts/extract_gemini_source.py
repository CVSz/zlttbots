#!/usr/bin/env python3
"""Extract recoverable source artifacts from Gemini chat-export markdown.

This utility scans a markdown transcript for:
1) unified diffs (`diff --git ...`)
2) shell heredoc file writes (`cat << 'EOF' > path`)
3) fenced code blocks with a `File:` or `Path:` hint directly above them

Output is deterministic and idempotent: running it repeatedly produces the same
set of files for unchanged input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator


CODE_FENCE_PATTERN = re.compile(r"```(?P<lang>[^\n]*)\n(?P<body>.*?)\n```", re.DOTALL)
HEREDOC_PATTERN = re.compile(
    r"cat\s+<<\s*['\"]?(?P<tag>[A-Za-z0-9_\-]+)['\"]?\s*>\s*(?P<path>[^\n]+)\n(?P<body>.*?)\n(?P=tag)",
    re.DOTALL,
)
PATH_HINT_PATTERN = re.compile(r"(?:^|\n)(?:File|Path)\s*:\s*(?P<path>[^\n]+)\s*$", re.IGNORECASE)


@dataclass(frozen=True)
class Artifact:
    kind: str
    suggested_path: str
    content: str
    source_index: int

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.content.encode("utf-8")).hexdigest()[:16]


def _iter_code_fences(markdown: str) -> Iterator[tuple[int, int, str, str]]:
    for idx, match in enumerate(CODE_FENCE_PATTERN.finditer(markdown), start=1):
        yield idx, match.start(), (match.group("lang") or "").strip().lower(), match.group("body")


def extract_artifacts(markdown: str) -> list[Artifact]:
    artifacts: list[Artifact] = []

    for idx, fence_start, lang, body in _iter_code_fences(markdown):
        stripped = body.strip()
        if not stripped:
            continue

        if "diff --git " in stripped or stripped.startswith("--- ") and "+++ " in stripped:
            artifacts.append(
                Artifact(
                    kind="patch",
                    suggested_path=f"patches/patch_{idx:04d}.diff",
                    content=stripped + "\n",
                    source_index=idx,
                )
            )

        for heredoc in HEREDOC_PATTERN.finditer(body):
            target = heredoc.group("path").strip()
            content = heredoc.group("body")
            if target:
                artifacts.append(
                    Artifact(
                        kind="heredoc_file",
                        suggested_path=f"files/{target}",
                        content=content + "\n",
                        source_index=idx,
                    )
                )

        # Heuristic: nearby path hint in raw markdown before the current fence.
        prefix = markdown[max(0, fence_start - 500) : fence_start]
        hint_match = PATH_HINT_PATTERN.search(prefix)
        if hint_match:
            hint_path = hint_match.group("path").strip()
            if hint_path:
                artifacts.append(
                    Artifact(
                        kind="hinted_file",
                        suggested_path=f"files/{hint_path}",
                        content=body.rstrip("\n") + "\n",
                        source_index=idx,
                    )
                )

    # Deduplicate by (kind, path, digest) while keeping stable order
    seen: set[tuple[str, str, str]] = set()
    deduped: list[Artifact] = []
    for artifact in artifacts:
        key = (artifact.kind, artifact.suggested_path, artifact.digest)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(artifact)
    return deduped


def _safe_join(root: Path, relative: str) -> Path:
    cleaned = relative.strip().lstrip("/")
    path = (root / cleaned).resolve()
    if root.resolve() not in path.parents and path != root.resolve():
        raise ValueError(f"Unsafe output path outside output directory: {relative}")
    return path


def write_artifacts(artifacts: Iterable[Artifact], output_dir: Path) -> dict[str, int]:
    counts = {"patch": 0, "heredoc_file": 0, "hinted_file": 0}
    for artifact in artifacts:
        rel = artifact.suggested_path
        if artifact.kind in {"heredoc_file", "hinted_file"}:
            rel = f"{artifact.kind}/{artifact.source_index:04d}_{artifact.digest}_{Path(rel).name}"
        out_path = _safe_join(output_dir, rel)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(artifact.content, encoding="utf-8")
        counts[artifact.kind] = counts.get(artifact.kind, 0) + 1

    manifest = {
        "total": sum(counts.values()),
        "counts": counts,
        "artifacts": [
            {
                "kind": a.kind,
                "source_index": a.source_index,
                "digest": a.digest,
                "suggested_path": a.suggested_path,
            }
            for a in artifacts
        ],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Path to Gemini markdown export")
    parser.add_argument("-o", "--output", type=Path, default=Path("generated/gemini-source"), help="Output directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    markdown = args.input.read_text(encoding="utf-8")
    artifacts = extract_artifacts(markdown)
    counts = write_artifacts(artifacts, args.output)
    print(json.dumps({"output": str(args.output), "counts": counts, "total": len(artifacts)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
