"""Tests for loading and validating the one canon file."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from unit_canon.load import CANON_FILE, CanonError, load
from unit_canon.model import Canon


def test_packaged_file_exists() -> None:
    assert CANON_FILE.is_file()
    assert CANON_FILE.name == "canon.json"


def test_load_defaults() -> None:
    canon = load()
    assert isinstance(canon, Canon)
    assert canon.unit == "meter"
    assert canon.schema_version == 1
    assert canon.meters_per_grid == 1.0
    assert canon.deck_height == 3.0
    assert canon.airlock_diameter == 1.0
    assert canon.human_figure.asset_name == "HumanFigure"
    assert canon.human_figure.standing_height == 1.8
    assert canon.human_figure.eye_height == 1.65
    assert canon.human_figure.shoulder_width == 0.45


def test_derived_measures() -> None:
    canon = load()
    assert canon.airlock_radius == 0.5
    assert canon.grids_per_deck == 3.0
    assert canon.overhead_clearance == pytest.approx(1.2)


def test_measure_lookup() -> None:
    canon = load()
    assert canon.measure("deck_height") == 3.0
    assert canon.measure("human_figure.eye_height") == 1.65
    with pytest.raises(KeyError, match="Unknown canon key"):
        canon.measure("nope")


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(CanonError, match="Cannot read"):
        load(tmp_path / "missing.json")


def test_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "canon.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(CanonError, match="not valid JSON"):
        load(path)


def test_missing_keys(tmp_path: Path) -> None:
    path = tmp_path / "canon.json"
    path.write_text(json.dumps({"meters_per_grid": 1.0}), encoding="utf-8")
    with pytest.raises(CanonError, match="missing keys"):
        load(path)


def test_unit_must_be_meter(tmp_path: Path) -> None:
    data = json.loads(CANON_FILE.read_text(encoding="utf-8"))
    data["unit"] = "centimeter"
    path = tmp_path / "canon.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CanonError, match="meter"):
        load(path)


def test_deck_must_be_integer_grids(tmp_path: Path) -> None:
    data = json.loads(CANON_FILE.read_text(encoding="utf-8"))
    data["deck_height"] = 3.2
    path = tmp_path / "canon.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CanonError, match="integer multiple"):
        load(path)


def test_human_must_fit_under_deck(tmp_path: Path) -> None:
    data = json.loads(CANON_FILE.read_text(encoding="utf-8"))
    data["human_figure"]["standing_height"] = 3.0
    path = tmp_path / "canon.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CanonError, match="standing_height"):
        load(path)


def test_shoulders_must_fit_airlock(tmp_path: Path) -> None:
    data = json.loads(CANON_FILE.read_text(encoding="utf-8"))
    data["human_figure"]["shoulder_width"] = 1.0
    path = tmp_path / "canon.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CanonError, match="shoulder_width"):
        load(path)


def test_eye_below_standing(tmp_path: Path) -> None:
    data = json.loads(CANON_FILE.read_text(encoding="utf-8"))
    data["human_figure"]["eye_height"] = 1.9
    path = tmp_path / "canon.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CanonError, match="eye_height"):
        load(path)


def test_non_positive_rejected(tmp_path: Path) -> None:
    data = json.loads(CANON_FILE.read_text(encoding="utf-8"))
    data["meters_per_grid"] = 0
    path = tmp_path / "canon.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CanonError, match="must be > 0"):
        load(path)
