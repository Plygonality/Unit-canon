"""Registry of every Geometry Nodes input and export path.

Each binding reads a value from the one canon file. Do not hardcode lengths
in GN builders or exporters — look them up here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from unit_canon.load import load
from unit_canon.model import Canon

Kind = Literal["gn_input", "export"]
Getter = Callable[[Canon], float | str]


@dataclass(frozen=True, slots=True)
class PathBinding:
    """One named input or export setting, bound to a canon measure."""

    path_id: str
    kind: Kind
    name: str
    canon_key: str
    getter: Getter
    description: str


def _gn(
    path_id: str,
    name: str,
    canon_key: str,
    description: str,
) -> PathBinding:
    return PathBinding(
        path_id=path_id,
        kind="gn_input",
        name=name,
        canon_key=canon_key,
        getter=lambda canon, key=canon_key: canon.measure(key),
        description=description,
    )


def _export(
    path_id: str,
    name: str,
    canon_key: str,
    getter: Getter,
    description: str,
) -> PathBinding:
    return PathBinding(
        path_id=path_id,
        kind="export",
        name=name,
        canon_key=canon_key,
        getter=getter,
        description=description,
    )


# Unreal's unit system, not ours. Conversion lives here so exporters do not
# invent a scale factor. 1 Blender meter = 100 Unreal units.
UNREAL_UU_PER_METER = 100.0


def _uu(canon: Canon, key: str) -> float:
    return float(canon.measure(key)) * UNREAL_UU_PER_METER


GN_INPUTS: tuple[PathBinding, ...] = (
    _gn(
        "gn.input.meters_per_grid",
        "Meters Per Grid",
        "meters_per_grid",
        "World-grid spacing. GN snap, array pitch, collection-linter grid.",
    ),
    _gn(
        "gn.input.deck_height",
        "Deck Height",
        "deck_height",
        "Floor-to-floor spacing. Integer multiple of meters per grid.",
    ),
    _gn(
        "gn.input.airlock_diameter",
        "Airlock Diameter",
        "airlock_diameter",
        "Clear circular hatch / tube diameter.",
    ),
    _gn(
        "gn.input.human_standing_height",
        "Human Standing Height",
        "human_figure.standing_height",
        "Scale-reference figure height (UE5 mannequin class).",
    ),
    _gn(
        "gn.input.human_eye_height",
        "Human Eye Height",
        "human_figure.eye_height",
        "Camera / occupancy eye line on the scale figure.",
    ),
    _gn(
        "gn.input.human_shoulder_width",
        "Human Shoulder Width",
        "human_figure.shoulder_width",
        "Figure breadth; must pass through the airlock.",
    ),
)

EXPORT_PATHS: tuple[PathBinding, ...] = (
    _export(
        "export.blender.scene.scale_length",
        "Blender scene scale_length",
        "meters_per_grid",
        lambda _canon: 1.0,
        "Scene unit scale: 1 Blender unit = 1 meter.",
    ),
    _export(
        "export.fbx.global_scale",
        "FBX global_scale",
        "meters_per_grid",
        lambda _canon: 1.0,
        "FBX export scale while scene units are meters.",
    ),
    _export(
        "export.usd.meters_per_unit",
        "USD metersPerUnit",
        "meters_per_grid",
        lambda _canon: 1.0,
        "USD stage metersPerUnit. Scene is authored in meters.",
    ),
    _export(
        "export.unreal.uu_per_meter",
        "Unreal uu per meter",
        "meters_per_grid",
        lambda _canon: UNREAL_UU_PER_METER,
        "Unreal Engine centimeters per authored meter.",
    ),
    _export(
        "export.unreal.grid_size_uu",
        "Unreal grid size (uu)",
        "meters_per_grid",
        lambda canon: _uu(canon, "meters_per_grid"),
        "World-grid snap in Unreal units.",
    ),
    _export(
        "export.unreal.deck_height_uu",
        "Unreal deck height (uu)",
        "deck_height",
        lambda canon: _uu(canon, "deck_height"),
        "Floor-to-floor height in Unreal units.",
    ),
    _export(
        "export.unreal.airlock_diameter_uu",
        "Unreal airlock diameter (uu)",
        "airlock_diameter",
        lambda canon: _uu(canon, "airlock_diameter"),
        "Airlock diameter in Unreal units.",
    ),
    _export(
        "export.unreal.human_standing_height_uu",
        "Unreal human standing height (uu)",
        "human_figure.standing_height",
        lambda canon: _uu(canon, "human_figure.standing_height"),
        "Scale figure height in Unreal units.",
    ),
    _export(
        "export.unreal.human_eye_height_uu",
        "Unreal human eye height (uu)",
        "human_figure.eye_height",
        lambda canon: _uu(canon, "human_figure.eye_height"),
        "Eye-height camera in Unreal units.",
    ),
)

ALL_PATHS: tuple[PathBinding, ...] = GN_INPUTS + EXPORT_PATHS


def gn_inputs() -> tuple[PathBinding, ...]:
    return GN_INPUTS


def export_paths() -> tuple[PathBinding, ...]:
    return EXPORT_PATHS


def all_paths() -> tuple[PathBinding, ...]:
    return ALL_PATHS


def resolve(binding: PathBinding, canon: Canon | None = None) -> float | str:
    return binding.getter(canon or load())


def resolve_all(canon: Canon | None = None) -> dict[str, float | str]:
    """Every GN input and export path, resolved from the one file."""
    canon = canon or load()
    return {binding.path_id: binding.getter(canon) for binding in ALL_PATHS}
