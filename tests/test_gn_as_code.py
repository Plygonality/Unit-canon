"""gn-as-code defaults are the canon file, applied onto a node interface."""

from __future__ import annotations

from dataclasses import dataclass, field

from unit_canon.gn_as_code import apply_to_interface, defaults, socket_specs
from unit_canon.load import load


@dataclass
class FakeSocket:
    name: str
    default_value: float = 0.0
    subtype: str = ""
    description: str = ""
    min_value: float = -1.0
    socket_type: str = "NodeSocketFloat"
    in_out: str = "INPUT"


@dataclass
class FakeInterface:
    items_tree: list[FakeSocket] = field(default_factory=list)

    def new_socket(self, name: str, in_out: str, socket_type: str) -> FakeSocket:
        socket = FakeSocket(name=name, in_out=in_out, socket_type=socket_type)
        self.items_tree.append(socket)
        return socket


def test_defaults_match_canon() -> None:
    canon = load()
    values = defaults()
    assert values["meters_per_grid"] == canon.meters_per_grid
    assert values["deck_height"] == canon.deck_height
    assert values["airlock_diameter"] == canon.airlock_diameter
    assert values["human_figure.standing_height"] == canon.human_figure.standing_height
    assert values["human_figure.eye_height"] == canon.human_figure.eye_height
    assert values["human_figure.shoulder_width"] == canon.human_figure.shoulder_width


def test_socket_specs_are_distance_floats() -> None:
    for spec in socket_specs():
        assert spec.socket_type == "NodeSocketFloat"
        assert spec.subtype == "DISTANCE"
        assert spec.value > 0
        assert spec.path_id.startswith("gn.input.")


def test_apply_creates_missing_sockets() -> None:
    interface = FakeInterface()
    written = apply_to_interface(interface)
    canon = load()
    assert "Meters Per Grid" in written
    assert "Deck Height" in written
    by_name = {socket.name: socket for socket in interface.items_tree}
    assert by_name["Meters Per Grid"].default_value == canon.meters_per_grid
    assert by_name["Deck Height"].default_value == canon.deck_height
    assert by_name["Airlock Diameter"].default_value == canon.airlock_diameter
    assert by_name["Human Standing Height"].default_value == (
        canon.human_figure.standing_height
    )
    assert by_name["Meters Per Grid"].subtype == "DISTANCE"
    assert by_name["Meters Per Grid"].min_value == 0.0


def test_apply_updates_existing_sockets() -> None:
    interface = FakeInterface(
        items_tree=[
            FakeSocket(name="Deck Height", default_value=99.0),
            FakeSocket(name="Unrelated", default_value=1.0),
        ]
    )
    apply_to_interface(interface, create_missing=False)
    by_name = {socket.name: socket for socket in interface.items_tree}
    assert by_name["Deck Height"].default_value == load().deck_height
    assert by_name["Unrelated"].default_value == 1.0
    assert "Airlock Diameter" not in by_name
