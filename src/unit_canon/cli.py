"""CLI for the unit canon."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from unit_canon.collection_linter import Scene, lint
from unit_canon.gn_as_code import defaults, defaults_by_socket_name
from unit_canon.load import CANON_FILE, load
from unit_canon.paths import resolve_all
from unit_canon.unreal_export import conversion, export_path_values


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="unit-canon",
        description=(
            "Single source of truth for meters per grid, deck height, "
            "airlock diameter, and the human figure."
        ),
    )
    parser.add_argument(
        "--canon",
        type=Path,
        default=None,
        help="Override canon.json (tests only; omit in production).",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("show", help="Print the canon file (default).")
    sub.add_parser("gn-defaults", help="Print Geometry Nodes input defaults.")
    sub.add_parser("export-paths", help="Print every export path value.")
    sub.add_parser("unreal", help="Print Unreal unit conversion (export later).")
    lint_parser = sub.add_parser(
        "lint", help="Lint a dumped scene JSON against the canon."
    )
    lint_parser.add_argument("scene", type=Path)
    lint_parser.add_argument(
        "--allow-missing-roles",
        action="store_true",
        help="Do not fail when a canon role is absent from the scene.",
    )

    args = parser.parse_args(argv)
    canon = load(args.canon)

    if args.command in (None, "show"):
        payload = json.loads(CANON_FILE.read_text(encoding="utf-8"))
        if args.canon is not None:
            payload = json.loads(args.canon.read_text(encoding="utf-8"))
        json.dump(payload, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if args.command == "gn-defaults":
        json.dump(
            {
                "by_key": defaults(canon),
                "by_socket_name": defaults_by_socket_name(canon),
            },
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
        return 0

    if args.command == "export-paths":
        json.dump(resolve_all(canon), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if args.command == "unreal":
        table = conversion(canon)
        json.dump(
            {
                "implemented": False,
                "note": "Unreal mesh export is a later pass.",
                "conversion": {
                    "uu_per_meter": table.uu_per_meter,
                    "grid_size_uu": table.grid_size_uu,
                    "deck_height_uu": table.deck_height_uu,
                    "airlock_diameter_uu": table.airlock_diameter_uu,
                    "human_standing_height_uu": table.human_standing_height_uu,
                    "human_eye_height_uu": table.human_eye_height_uu,
                    "human_shoulder_width_uu": table.human_shoulder_width_uu,
                    "human_asset_name": table.human_asset_name,
                },
                "export_paths": export_path_values(canon),
            },
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
        return 0

    if args.command == "lint":
        data = json.loads(args.scene.read_text(encoding="utf-8"))
        rows = data["objects"] if isinstance(data, dict) and "objects" in data else data
        result = lint(
            Scene.from_dicts(rows),
            canon,
            require_roles=not args.allow_missing_roles,
        )
        json.dump(
            {
                "ok": result.ok,
                "checked": result.checked,
                "violations": [
                    {
                        "code": item.code,
                        "message": item.message,
                        "object_name": item.object_name,
                        "expected": item.expected,
                        "actual": item.actual,
                    }
                    for item in result.violations
                ],
            },
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
        return 0 if result.ok else 1

    parser.error(f"Unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
