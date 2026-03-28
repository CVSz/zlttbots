from pathlib import Path

from scripts.extract_gemini_source import extract_artifacts, write_artifacts


def test_extracts_patch_and_heredoc(tmp_path: Path) -> None:
    markdown = """
## Response
```\ndiff --git a/a.py b/a.py
--- a/a.py
+++ b/a.py
@@ -1 +1 @@
-print('a')
+print('b')

cat << 'EOF' > src/main.py
print('ok')
EOF
```
"""
    artifacts = extract_artifacts(markdown)
    kinds = [a.kind for a in artifacts]
    assert "patch" in kinds
    assert "heredoc_file" in kinds

    counts = write_artifacts(artifacts, tmp_path)
    assert counts["patch"] == 1
    assert counts["heredoc_file"] == 1


def test_extracts_hinted_file() -> None:
    markdown = """
File: services/api/src/main.py
```python
print('hello')
```
"""
    artifacts = extract_artifacts(markdown)
    assert any(a.kind == "hinted_file" for a in artifacts)
