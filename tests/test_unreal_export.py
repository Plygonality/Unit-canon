"""Unreal export hook reads scale from the canon file and defers mesh export."""

from __future__ import annotations

import pytest

from unit_canon.load import load
from unit_canon.unreal_export import conversion, export, export_path_values, to_unreal_uu


def test_conversion_reads_canon() -> None:
    canon = load()
    table = conversion()
    assert table.uu_per_meter == 100.0
    assert table.grid_size_uu == canon.meters_per_grid * 100
    assert table.deck_height_uu == canon.deck_height * 100
    assert table.airlock_diameter_uu == canon.airlock_diameter * 100
    assert table.human_standing_height_uu == canon.human_figure.standing_height * 100
    assert table.human_eye_height_uu == canon.human_figure.eye_height * 100
    assert table.human_shoulder_width_uu == canon.human_figure.shoulder_width * 100
    assert table.human_asset_name == canon.human_figure.asset_name


def test_to_unreal_uu() -> None:
    assert to_unreal_uu(1.8) == 180.0
    assert to_unreal_uu(3.0) == 300.0


def test_export_path_values_are_export_keys() -> None:
    values = export_path_values()
    assert values
    assert all(key.startswith("export.") for key in values)
    assert "gn.input.deck_height" not in values


def test_export_is_deferred() -> None:
    with pytest.raises(NotImplementedError, match="later|not implemented"):
        export()
