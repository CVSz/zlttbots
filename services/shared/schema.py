from __future__ import annotations

from typing import Any


def validate(schema: dict[str, type] | list[str], data: dict[str, Any]) -> bool:
    if isinstance(schema, list):
        return all(key in data for key in schema)

    for key, expected_type in schema.items():
        if key not in data or not isinstance(data[key], expected_type):
            return False
    return True
