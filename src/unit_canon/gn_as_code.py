"""Geometry Nodes as-code defaults.

GN group-input sockets take their default_value from the one canon file.
Call ``socket_specs()`` when building a node tree; call ``apply_to_interface``
on an existing Blender 4 ``node_tree.interface``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Protocol

from unit_canon.load import load
from unit_canon.model import Canon
from unit_canon.paths import GN_INPUTS, PathBinding


class SocketLike(Protocol):
    name: str
    default_value: Any
    subtype: str
    description: str
    min_value: float


class InterfaceLike(Protocol):
    items_tree: Iterable[Any]

    def new_socket(self, name: str, in_out: str, socket_type: str) -> SocketLike:
        ...


@dataclass(frozen=True, slots=True)
class GnSocketSpec:
    """One Group Input socket whose default is a canon measure."""

    key: str
    name: str
    value: float
    description: str
    socket_type: str = "NodeSocketFloat"
    subtype: str = "DISTANCE"
    min_value: float = 0.0
    path_id: str = ""


def _spec(binding: PathBinding, canon: Canon) -> GnSocketSpec:
    value = binding.getter(canon)
    if not isinstance(value, (int, float)):
        raise TypeError(f"{binding.path_id} is not numeric: {value!r}")
    return GnSocketSpec(
        key=binding.canon_key,
        name=binding.name,
        value=float(value),
        description=binding.description,
        path_id=binding.path_id,
    )


def socket_specs(canon: Canon | None = None) -> tuple[GnSocketSpec, ...]:
    """GN Group Input specs. Defaults come only from the canon file."""
    canon = canon or load()
    return tuple(_spec(binding, canon) for binding in GN_INPUTS)


def defaults(canon: Canon | None = None) -> dict[str, float]:
    """Map canon keys to GN default values."""
    return {spec.key: spec.value for spec in socket_specs(canon)}


def defaults_by_socket_name(canon: Canon | None = None) -> dict[str, float]:
    """Map Blender socket names to GN default values."""
    return {spec.name: spec.value for spec in socket_specs(canon)}


def apply_to_interface(
    interface: InterfaceLike,
    canon: Canon | None = None,
    *,
    create_missing: bool = True,
) -> list[str]:
    """Write canon defaults onto a Geometry Node Tree interface.

    Matches sockets by name. When ``create_missing`` is true, missing
    sockets are added as float distance inputs. Returns the socket names
    that were written.
    """
    specs = socket_specs(canon)
    existing = {
        item.name: item
        for item in interface.items_tree
        if getattr(item, "name", None)
    }
    written: list[str] = []
    for spec in specs:
        socket = existing.get(spec.name)
        if socket is None:
            if not create_missing:
                continue
            if not hasattr(interface, "new_socket"):
                raise AttributeError(
                    "Interface has no new_socket; cannot create "
                    f"{spec.name!r}."
                )
            socket = interface.new_socket(
                name=spec.name,
                in_out="INPUT",
                socket_type=spec.socket_type,
            )
            existing[spec.name] = socket
        socket.default_value = spec.value
        if hasattr(socket, "subtype"):
            socket.subtype = spec.subtype
        if hasattr(socket, "description"):
            socket.description = spec.description
        if hasattr(socket, "min_value"):
            socket.min_value = spec.min_value
        written.append(spec.name)
    return written
