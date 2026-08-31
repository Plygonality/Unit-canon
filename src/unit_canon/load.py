"""Load the one canon file. Nothing else may invent these numbers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from unit_canon.model import Canon, HumanFigure

try:
    from importlib.resources import files as _files
except ImportError:  # pragma: no cover
    from importlib_resources import files as _files  # type: ignore[no-redef]

CANON_FILE: Path = Path(str(_files("unit_canon").joinpath("canon.json")))

_REQUIRED_ROOT = (
    "schema_version",
    "unit",
    "meters_per_grid",
    "deck_height",
    "airlock_diameter",
    "human_figure",
)
_REQUIRED_HUMAN = (
    "asset_name",
    "standing_height",
    "eye_height",
    "shoulder_width",
)


class CanonError(ValueError):
    """The canon file is missing, malformed, or internally inconsistent."""


def load(path: Path | str | None = None) -> Canon:
    """Read and validate the unit canon.

    ``path`` is for tests and explicit overrides only. Production callers
    should omit it so every path reads the packaged ``canon.json``.
    """
    source = Path(path) if path is not None else CANON_FILE
    try:
        raw_text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise CanonError(f"Cannot read canon file: {source}") from exc
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise CanonError(f"Canon file is not valid JSON: {source}") from exc
    if not isinstance(data, dict):
        raise CanonError("Canon file must be a JSON object.")
    return parse(data, source=source)


def parse(data: dict[str, Any], *, source: Path | str | None = None) -> Canon:
    """Validate a canon dict and return a frozen ``Canon``."""
    where = f" ({source})" if source else ""
    missing = [key for key in _REQUIRED_ROOT if key not in data]
    if missing:
        raise CanonError(f"Canon missing keys{where}: {', '.join(missing)}")

    unit = data["unit"]
    if unit != "meter":
        raise CanonError(f"Canon unit must be 'meter', got {unit!r}{where}.")

    schema_version = _int(data["schema_version"], "schema_version", where)
    if schema_version != 1:
        raise CanonError(
            f"Unsupported canon schema_version {schema_version}{where}."
        )

    meters_per_grid = _positive(data["meters_per_grid"], "meters_per_grid", where)
    deck_height = _positive(data["deck_height"], "deck_height", where)
    airlock_diameter = _positive(
        data["airlock_diameter"], "airlock_diameter", where
    )
    human = _human(data["human_figure"], where)

    remainder = deck_height / meters_per_grid
    if abs(remainder - round(remainder)) > 1e-9:
        raise CanonError(
            "deck_height must be an integer multiple of meters_per_grid"
            f"{where}: {deck_height} / {meters_per_grid} = {remainder}."
        )

    if human.standing_height >= deck_height:
        raise CanonError(
            "human_figure.standing_height must be less than deck_height"
            f"{where}: {human.standing_height} >= {deck_height}."
        )
    if human.eye_height >= human.standing_height:
        raise CanonError(
            "human_figure.eye_height must be less than standing_height"
            f"{where}: {human.eye_height} >= {human.standing_height}."
        )
    if human.shoulder_width >= airlock_diameter:
        raise CanonError(
            "human_figure.shoulder_width must be less than airlock_diameter"
            f"{where}: {human.shoulder_width} >= {airlock_diameter}."
        )

    return Canon(
        schema_version=schema_version,
        unit=unit,
        meters_per_grid=meters_per_grid,
        deck_height=deck_height,
        airlock_diameter=airlock_diameter,
        human_figure=human,
    )


def _human(value: Any, where: str) -> HumanFigure:
    if not isinstance(value, dict):
        raise CanonError(f"human_figure must be an object{where}.")
    missing = [key for key in _REQUIRED_HUMAN if key not in value]
    if missing:
        raise CanonError(
            f"human_figure missing keys{where}: {', '.join(missing)}"
        )
    asset_name = value["asset_name"]
    if not isinstance(asset_name, str) or not asset_name.strip():
        raise CanonError(f"human_figure.asset_name must be a non-empty string{where}.")
    return HumanFigure(
        asset_name=asset_name.strip(),
        standing_height=_positive(
            value["standing_height"], "human_figure.standing_height", where
        ),
        eye_height=_positive(
            value["eye_height"], "human_figure.eye_height", where
        ),
        shoulder_width=_positive(
            value["shoulder_width"], "human_figure.shoulder_width", where
        ),
    )


def _positive(value: Any, name: str, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CanonError(f"{name} must be a number{where}, got {value!r}.")
    number = float(value)
    if number <= 0.0:
        raise CanonError(f"{name} must be > 0{where}, got {number}.")
    return number


def _int(value: Any, name: str, where: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CanonError(f"{name} must be an integer{where}, got {value!r}.")
    return value
