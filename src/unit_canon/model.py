"""Canonical scale values. Loaded only from canon.json."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HumanFigure:
    """Scale-reference human. Standing height is the primary dimension."""

    asset_name: str
    standing_height: float
    eye_height: float
    shoulder_width: float


@dataclass(frozen=True, slots=True)
class Canon:
    """The four measures every GN input and export path must read."""

    schema_version: int
    unit: str
    meters_per_grid: float
    deck_height: float
    airlock_diameter: float
    human_figure: HumanFigure

    @property
    def airlock_radius(self) -> float:
        return self.airlock_diameter / 2.0

    @property
    def grids_per_deck(self) -> float:
        return self.deck_height / self.meters_per_grid

    @property
    def overhead_clearance(self) -> float:
        return self.deck_height - self.human_figure.standing_height

    def measure(self, key: str) -> float:
        """Look up a length by dotted key (e.g. ``human_figure.standing_height``)."""
        mapping = {
            "meters_per_grid": self.meters_per_grid,
            "deck_height": self.deck_height,
            "airlock_diameter": self.airlock_diameter,
            "airlock_radius": self.airlock_radius,
            "grids_per_deck": self.grids_per_deck,
            "overhead_clearance": self.overhead_clearance,
            "human_figure.standing_height": self.human_figure.standing_height,
            "human_figure.eye_height": self.human_figure.eye_height,
            "human_figure.shoulder_width": self.human_figure.shoulder_width,
        }
        try:
            return mapping[key]
        except KeyError as exc:
            known = ", ".join(mapping)
            raise KeyError(f"Unknown canon key {key!r}. Known: {known}") from exc
