"""The packaged canon.json is the only measure file."""

from __future__ import annotations

from pathlib import Path

from unit_canon.load import CANON_FILE


def test_only_one_canon_json() -> None:
    root = Path(__file__).resolve().parents[1]
    found = list(root.rglob("canon.json"))
    found = [path for path in found if ".venv" not in path.parts]
    assert found == [CANON_FILE.resolve()] or found == [
        path for path in found if path.resolve() == CANON_FILE.resolve()
    ]
    assert len(found) == 1
    assert found[0].name == "canon.json"
