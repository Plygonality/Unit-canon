"""Collection-linter compares scene roles to the canon file."""

from __future__ import annotations

from unit_canon.collection_linter import (
    Role,
    Scene,
    SceneObject,
    expected_sizes,
    lint,
)
from unit_canon.load import load


def _obj(
    name: str,
    role: Role,
    dimensions: tuple[float, float, float],
    location: tuple[float, float, float] = (0.0, 0.0, 0.0),
) -> SceneObject:
    return SceneObject(
        name=name,
        collection="canon",
        dimensions=dimensions,
        location=location,
        role=role,
    )


def _valid_scene() -> Scene:
    canon = load()
    hf = canon.human_figure
    return Scene(
        objects=(
            _obj(
                hf.asset_name,
                "human_figure",
                (hf.shoulder_width, 0.3, hf.standing_height),
            ),
            _obj(
                "airlock_main",
                "airlock",
                (canon.airlock_diameter, canon.airlock_diameter, 2.0),
            ),
            _obj("deck_0", "deck", (4.0, 4.0, 0.2), (0.0, 0.0, 0.0)),
            _obj("deck_1", "deck", (4.0, 4.0, 0.2), (0.0, 0.0, canon.deck_height)),
            _obj("grid_origin", "grid", (1.0, 1.0, 1.0), (0.0, 0.0, 0.0)),
        )
    )


def test_expected_sizes_read_canon() -> None:
    canon = load()
    sizes = expected_sizes()
    assert sizes["grid"] == canon.meters_per_grid
    assert sizes["deck"] == canon.deck_height
    assert sizes["airlock"] == canon.airlock_diameter
    assert sizes["human_figure"] == canon.human_figure.standing_height


def test_valid_scene_passes() -> None:
    result = lint(_valid_scene())
    assert result.ok
    assert result.checked >= 4


def test_wrong_human_height_fails() -> None:
    objects = [
        obj for obj in _valid_scene().objects if obj.role != "human_figure"
    ]
    objects.append(_obj("HumanFigure", "human_figure", (0.45, 0.3, 2.5)))
    result = lint(Scene(objects=tuple(objects)))
    assert not result.ok
    assert result.by_code("HUMAN_HEIGHT")
    assert result.by_code("HUMAN_HEIGHT")[0].expected == (
        load().human_figure.standing_height
    )


def test_wrong_airlock_diameter_fails() -> None:
    objects = [
        obj for obj in _valid_scene().objects if obj.role != "airlock"
    ]
    objects.append(_obj("airlock_main", "airlock", (2.0, 2.0, 2.0)))
    result = lint(Scene(objects=tuple(objects)))
    assert result.by_code("AIRLOCK_DIAMETER")
    assert result.by_code("AIRLOCK_DIAMETER")[0].expected == load().airlock_diameter


def test_deck_off_spacing_fails() -> None:
    objects = [
        obj for obj in _valid_scene().objects if obj.role != "deck"
    ]
    objects.append(_obj("deck_bad", "deck", (4.0, 4.0, 0.2), (0.0, 0.0, 1.1)))
    result = lint(Scene(objects=tuple(objects)))
    assert result.by_code("DECK_SPACING")
    assert result.by_code("DECK_SPACING")[0].expected == load().deck_height


def test_grid_off_snap_fails() -> None:
    objects = [
        obj for obj in _valid_scene().objects if obj.role != "grid"
    ]
    objects.append(_obj("grid_bad", "grid", (1.0, 1.0, 1.0), (0.3, 0.0, 0.0)))
    result = lint(Scene(objects=tuple(objects)))
    assert result.by_code("GRID_SNAP")
    assert result.by_code("GRID_SNAP")[0].expected == load().meters_per_grid


def test_missing_roles_reported() -> None:
    result = lint(Scene(objects=()), require_roles=True)
    assert len(result.by_code("MISSING_ROLE")) == 4


def test_name_infers_human_figure() -> None:
    canon = load()
    result = lint(
        Scene(
            objects=(
                SceneObject(
                    name=canon.human_figure.asset_name,
                    collection="canon",
                    dimensions=(0.45, 0.3, canon.human_figure.standing_height),
                    location=(0.0, 0.0, 0.0),
                    role=None,
                ),
            )
        ),
        require_roles=False,
    )
    assert result.ok
    assert result.checked == 1


def test_from_dicts() -> None:
    canon = load()
    scene = Scene.from_dicts(
        [
            {
                "name": "HumanFigure",
                "collection": "canon",
                "dimensions": [0.45, 0.3, canon.human_figure.standing_height],
                "location": [0, 0, 0],
                "role": "human_figure",
            }
        ]
    )
    result = lint(scene, require_roles=False)
    assert result.ok
