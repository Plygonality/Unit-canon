"""Collection-linter: scene objects must match the one canon file.

Objects declare a role (``human_figure``, ``airlock``, ``deck``, ``grid``).
The linter compares their dimensions and placement to canon measures.
Blender is optional — pass a dumped scene (see ``Scene``) from a bpy adapter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal, Sequence

from unit_canon.load import load
from unit_canon.model import Canon

Role = Literal["human_figure", "airlock", "deck", "grid"]
ROLES: tuple[Role, ...] = ("human_figure", "airlock", "deck", "grid")

DEFAULT_TOLERANCE_M = 0.01


@dataclass(frozen=True, slots=True)
class SceneObject:
    name: str
    collection: str
    dimensions: tuple[float, float, float]
    location: tuple[float, float, float]
    role: Role | None = None


@dataclass(frozen=True, slots=True)
class Scene:
    objects: tuple[SceneObject, ...] = ()

    @classmethod
    def from_dicts(cls, rows: Iterable[dict]) -> Scene:
        objects = []
        for row in rows:
            role = row.get("role")
            objects.append(
                SceneObject(
                    name=str(row["name"]),
                    collection=str(row.get("collection", "")),
                    dimensions=_vec3(row.get("dimensions", (0.0, 0.0, 0.0))),
                    location=_vec3(row.get("location", (0.0, 0.0, 0.0))),
                    role=role,
                )
            )
        return cls(objects=tuple(objects))


@dataclass(frozen=True, slots=True)
class Violation:
    code: str
    message: str
    object_name: str | None = None
    expected: float | None = None
    actual: float | None = None


@dataclass(frozen=True, slots=True)
class LintResult:
    violations: tuple[Violation, ...]
    checked: int

    @property
    def ok(self) -> bool:
        return not self.violations

    def by_code(self, code: str) -> tuple[Violation, ...]:
        return tuple(item for item in self.violations if item.code == code)


def expected_sizes(canon: Canon | None = None) -> dict[str, float]:
    """Role → length the linter compares against. Reads the canon file."""
    canon = canon or load()
    return {
        "grid": canon.meters_per_grid,
        "deck": canon.deck_height,
        "airlock": canon.airlock_diameter,
        "human_figure": canon.human_figure.standing_height,
    }


def lint(
    scene: Scene | Sequence[SceneObject],
    canon: Canon | None = None,
    *,
    tolerance_m: float = DEFAULT_TOLERANCE_M,
    require_roles: bool = True,
) -> LintResult:
    """Lint a scene against the unit canon."""
    canon = canon or load()
    objects = scene.objects if isinstance(scene, Scene) else tuple(scene)
    expected = expected_sizes(canon)
    violations: list[Violation] = []

    seen: set[Role] = set()
    checked = 0
    for obj in objects:
        role = _infer_role(obj, canon)
        if role is None:
            continue
        seen.add(role)
        checked += 1
        violations.extend(_lint_object(obj, role, canon, expected, tolerance_m))

    if require_roles:
        for role in ROLES:
            if role not in seen:
                violations.append(
                    Violation(
                        code="MISSING_ROLE",
                        message=(
                            f"No object with role {role!r}. "
                            "Collection-linter expects a scale reference "
                            "for every canon measure."
                        ),
                    )
                )

    return LintResult(violations=tuple(violations), checked=checked)


def _infer_role(obj: SceneObject, canon: Canon) -> Role | None:
    if obj.role in ROLES:
        return obj.role
    name = obj.name.strip()
    if name == canon.human_figure.asset_name:
        return "human_figure"
    lowered = name.lower()
    for role in ROLES:
        if lowered == role or lowered.startswith(f"{role}_"):
            return role
    return None


def _lint_object(
    obj: SceneObject,
    role: Role,
    _canon: Canon,
    expected: dict[str, float],
    tolerance_m: float,
) -> list[Violation]:
    if role == "human_figure":
        actual = obj.dimensions[2]
        return _close(
            obj,
            "HUMAN_HEIGHT",
            expected["human_figure"],
            actual,
            tolerance_m,
            "standing height",
        )
    if role == "airlock":
        actual = _diameter_xy(obj.dimensions)
        return _close(
            obj,
            "AIRLOCK_DIAMETER",
            expected["airlock"],
            actual,
            tolerance_m,
            "diameter",
        )
    if role == "deck":
        return _multiple(
            obj,
            "DECK_SPACING",
            obj.location[2],
            expected["deck"],
            tolerance_m,
            "Z location",
        )
    if role == "grid":
        hits: list[Violation] = []
        for axis, value in zip("XYZ", obj.location, strict=True):
            hits.extend(
                _multiple(
                    obj,
                    "GRID_SNAP",
                    value,
                    expected["grid"],
                    tolerance_m,
                    f"{axis} location",
                )
            )
        return hits
    return []


def _close(
    obj: SceneObject,
    code: str,
    expected: float,
    actual: float,
    tolerance_m: float,
    label: str,
) -> list[Violation]:
    if abs(actual - expected) <= tolerance_m:
        return []
    return [
        Violation(
            code=code,
            object_name=obj.name,
            expected=expected,
            actual=actual,
            message=(
                f"{obj.name} {label} is {actual:g} m, "
                f"canon expects {expected:g} m."
            ),
        )
    ]


def _multiple(
    obj: SceneObject,
    code: str,
    actual: float,
    step: float,
    tolerance_m: float,
    label: str,
) -> list[Violation]:
    if step <= 0:
        return []
    remainder = abs(actual / step - round(actual / step)) * step
    if remainder <= tolerance_m:
        return []
    return [
        Violation(
            code=code,
            object_name=obj.name,
            expected=step,
            actual=actual,
            message=(
                f"{obj.name} {label} {actual:g} m is not a multiple of "
                f"canon step {step:g} m."
            ),
        )
    ]


def _diameter_xy(dimensions: tuple[float, float, float]) -> float:
    width, depth, _height = dimensions
    return (abs(width) + abs(depth)) / 2.0


def _vec3(value: object) -> tuple[float, float, float]:
    seq = tuple(value)  # type: ignore[arg-type]
    if len(seq) != 3:
        raise ValueError(f"Expected 3 numbers, got {value!r}")
    return (float(seq[0]), float(seq[1]), float(seq[2]))
