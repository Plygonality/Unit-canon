"""Every GN input and export path must resolve from the canon file."""

from __future__ import annotations

import json
from pathlib import Path

from unit_canon.collection_linter import expected_sizes
from unit_canon.gn_as_code import defaults, defaults_by_socket_name, socket_specs
from unit_canon.load import CANON_FILE, load
from unit_canon.paths import ALL_PATHS, EXPORT_PATHS, GN_INPUTS, resolve_all
from unit_canon.unreal_export import conversion, export_path_values


def test_registry_covers_the_four_measures() -> None:
    gn_keys = {binding.canon_key for binding in GN_INPUTS}
    assert "meters_per_grid" in gn_keys
    assert "deck_height" in gn_keys
    assert "airlock_diameter" in gn_keys
    assert "human_figure.standing_height" in gn_keys


def test_resolve_all_matches_file() -> None:
    canon = load()
    resolved = resolve_all()
    assert resolved["gn.input.meters_per_grid"] == canon.meters_per_grid
    assert resolved["gn.input.deck_height"] == canon.deck_height
    assert resolved["gn.input.airlock_diameter"] == canon.airlock_diameter
    assert (
        resolved["gn.input.human_standing_height"]
        == canon.human_figure.standing_height
    )
    assert resolved["export.unreal.grid_size_uu"] == canon.meters_per_grid * 100
    assert resolved["export.unreal.deck_height_uu"] == canon.deck_height * 100
    assert (
        resolved["export.unreal.airlock_diameter_uu"]
        == canon.airlock_diameter * 100
    )


def test_every_registered_path_is_resolved() -> None:
    resolved = resolve_all()
    assert set(resolved) == {binding.path_id for binding in ALL_PATHS}
    assert all(binding.path_id.startswith("gn.input.") for binding in GN_INPUTS)
    assert all(binding.path_id.startswith("export.") for binding in EXPORT_PATHS)


def test_override_propagates_to_gn_linter_and_unreal(tmp_path: Path) -> None:
    data = json.loads(CANON_FILE.read_text(encoding="utf-8"))
    data["meters_per_grid"] = 2.0
    data["deck_height"] = 4.0
    data["airlock_diameter"] = 1.5
    data["human_figure"]["standing_height"] = 1.9
    data["human_figure"]["eye_height"] = 1.7
    data["human_figure"]["shoulder_width"] = 0.5
    path = tmp_path / "canon.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    canon = load(path)

    gn = defaults(canon)
    assert gn["meters_per_grid"] == 2.0
    assert gn["deck_height"] == 4.0
    assert gn["airlock_diameter"] == 1.5
    assert gn["human_figure.standing_height"] == 1.9

    sizes = expected_sizes(canon)
    assert sizes["grid"] == 2.0
    assert sizes["deck"] == 4.0
    assert sizes["airlock"] == 1.5
    assert sizes["human_figure"] == 1.9

    ue = conversion(canon)
    assert ue.grid_size_uu == 200.0
    assert ue.deck_height_uu == 400.0
    assert ue.airlock_diameter_uu == 150.0
    assert ue.human_standing_height_uu == 190.0

    export = export_path_values(canon)
    assert export["export.unreal.grid_size_uu"] == 200.0


def test_gn_socket_names_are_stable() -> None:
    names = [spec.name for spec in socket_specs()]
    assert names == [
        "Meters Per Grid",
        "Deck Height",
        "Airlock Diameter",
        "Human Standing Height",
        "Human Eye Height",
        "Human Shoulder Width",
    ]
    by_name = defaults_by_socket_name()
    canon = load()
    assert by_name["Meters Per Grid"] == canon.meters_per_grid
    assert by_name["Deck Height"] == canon.deck_height
