from pathlib import Path

from scripts.repo_cleanup_audit import (
    candidate_local_module_targets,
    normalize_path_list,
    traverse_reachable,
)


def test_candidate_local_module_targets_resolves_index_and_suffix(tmp_path: Path) -> None:
    src = tmp_path / "app" / "main.ts"
    src.parent.mkdir(parents=True)
    src.write_text("import './lib'", encoding="utf-8")

    targets = candidate_local_module_targets(src, "./lib")

    assert any(path.name == "lib.ts" for path in targets)
    assert any(path.name == "index.ts" for path in targets)


def test_traverse_reachable_returns_transitive_nodes(tmp_path: Path) -> None:
    file_a = (tmp_path / "a.py").resolve()
    file_b = (tmp_path / "b.py").resolve()
    file_c = (tmp_path / "c.py").resolve()

    graph = {
        file_a: {file_b},
        file_b: {file_c},
        file_c: set(),
    }

    visited = traverse_reachable(graph, {file_a})

    assert visited == {file_a, file_b, file_c}


def test_normalize_path_list_ignores_non_existing_entries(tmp_path: Path) -> None:
    repo_root = Path.cwd()
    existing = {(repo_root / "scripts" / "repo_cleanup_audit.py").resolve()}

    normalized = normalize_path_list(
        [
            "scripts/repo_cleanup_audit.py",
            "scripts/does-not-exist.py",
        ],
        existing,
    )

    assert normalized == existing
