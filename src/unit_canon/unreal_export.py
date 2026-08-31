"""Unreal export hook.

Scale conversion reads the one canon file. Mesh export itself is deferred.
"""

from __future__ import annotations

from dataclasses import dataclass

from unit_canon.load import load
from unit_canon.model import Canon
from unit_canon.paths import UNREAL_UU_PER_METER, resolve_all


@dataclass(frozen=True, slots=True)
class UnrealConversion:
    """Unreal-side lengths derived from the unit canon."""

    uu_per_meter: float
    grid_size_uu: float
    deck_height_uu: float
    airlock_diameter_uu: float
    human_standing_height_uu: float
    human_eye_height_uu: float
    human_shoulder_width_uu: float
    human_asset_name: str


def to_unreal_uu(meters: float) -> float:
    """Convert an authored meter length to Unreal units (centimeters)."""
    return meters * UNREAL_UU_PER_METER


def conversion(canon: Canon | None = None) -> UnrealConversion:
    """Unreal sizes. Every field is derived from the canon file."""
    canon = canon or load()
    return UnrealConversion(
        uu_per_meter=UNREAL_UU_PER_METER,
        grid_size_uu=to_unreal_uu(canon.meters_per_grid),
        deck_height_uu=to_unreal_uu(canon.deck_height),
        airlock_diameter_uu=to_unreal_uu(canon.airlock_diameter),
        human_standing_height_uu=to_unreal_uu(
            canon.human_figure.standing_height
        ),
        human_eye_height_uu=to_unreal_uu(canon.human_figure.eye_height),
        human_shoulder_width_uu=to_unreal_uu(
            canon.human_figure.shoulder_width
        ),
        human_asset_name=canon.human_figure.asset_name,
    )


def export_path_values(canon: Canon | None = None) -> dict[str, float | str]:
    """The ``export.*`` registry, resolved from the canon file."""
    resolved = resolve_all(canon)
    return {key: value for key, value in resolved.items() if key.startswith("export.")}


def export(*_args: object, **_kwargs: object) -> None:
    """Placeholder. Unreal mesh export is a later pass.

    Use ``conversion()`` and ``export_path_values()`` until then so any
    exporter still reads scale from the one canon file.
    """
    raise NotImplementedError(
        "Unreal export is not implemented yet. "
        "Read scale from unit_canon.unreal_export.conversion()."
    )
