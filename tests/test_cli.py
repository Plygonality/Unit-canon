"""CLI surfaces the one file and the three hooks."""

from __future__ import annotations

import json
from pathlib import Path

from unit_canon.cli import main
from unit_canon.load import load


def test_show(capsys) -> None:
    assert main(["show"]) == 0
    payload = json.loads(capsys.readouterr().out)
    canon = load()
    assert payload["meters_per_grid"] == canon.meters_per_grid
    assert payload["deck_height"] == canon.deck_height
    assert payload["airlock_diameter"] == canon.airlock_diameter
    assert payload["human_figure"]["standing_height"] == (
        canon.human_figure.standing_height
    )


def test_gn_defaults(capsys) -> None:
    assert main(["gn-defaults"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["by_key"]["deck_height"] == load().deck_height


def test_export_paths(capsys) -> None:
    assert main(["export-paths"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["gn.input.meters_per_grid"] == load().meters_per_grid
    assert payload["export.unreal.deck_height_uu"] == load().deck_height * 100


def test_unreal(capsys) -> None:
    assert main(["unreal"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["implemented"] is False
    assert payload["conversion"]["grid_size_uu"] == load().meters_per_grid * 100


def test_lint_ok(tmp_path: Path, capsys) -> None:
    canon = load()
    scene = tmp_path / "scene.json"
    scene.write_text(
        json.dumps(
            {
                "objects": [
                    {
                        "name": "HumanFigure",
                        "dimensions": [0.45, 0.3, canon.human_figure.standing_height],
                        "location": [0, 0, 0],
                        "role": "human_figure",
                    },
                    {
                        "name": "airlock_main",
                        "dimensions": [
                            canon.airlock_diameter,
                            canon.airlock_diameter,
                            2.0,
                        ],
                        "location": [0, 0, 0],
                        "role": "airlock",
                    },
                    {
                        "name": "deck_0",
                        "dimensions": [4, 4, 0.2],
                        "location": [0, 0, 0],
                        "role": "deck",
                    },
                    {
                        "name": "grid_origin",
                        "dimensions": [1, 1, 1],
                        "location": [0, 0, 0],
                        "role": "grid",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    assert main(["lint", str(scene)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True


def test_lint_fails(tmp_path: Path, capsys) -> None:
    scene = tmp_path / "scene.json"
    scene.write_text(
        json.dumps(
            {
                "objects": [
                    {
                        "name": "HumanFigure",
                        "dimensions": [0.45, 0.3, 9.0],
                        "location": [0, 0, 0],
                        "role": "human_figure",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert main(["lint", str(scene), "--allow-missing-roles"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["violations"][0]["code"] == "HUMAN_HEIGHT"
