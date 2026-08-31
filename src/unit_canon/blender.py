"""Optional Blender adapter. Imports ``bpy`` only when called."""

from __future__ import annotations

from typing import Any

from unit_canon.collection_linter import (
    LintResult,
    Scene,
    SceneObject,
    lint,
)
from unit_canon.gn_as_code import apply_to_interface
from unit_canon.load import load
from unit_canon.model import Canon


def _bpy() -> Any:
    try:
        import bpy  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "Blender's bpy module is not available. "
            "Run this adapter inside Blender, or pass a dumped Scene "
            "to collection_linter.lint()."
        ) from exc
    return bpy


def apply_gn_defaults(
    node_tree: Any | None = None,
    canon: Canon | None = None,
    *,
    create_missing: bool = True,
) -> list[str]:
    """Set Geometry Nodes group-input defaults from the canon file."""
    bpy = _bpy()
    tree = node_tree
    if tree is None:
        obj = bpy.context.object
        if obj is None:
            raise RuntimeError("No active object; pass a node_tree.")
        modifier = next(
            (
                item
                for item in obj.modifiers
                if item.type == "NODES" and item.node_group
            ),
            None,
        )
        if modifier is None:
            raise RuntimeError("Active object has no Geometry Nodes modifier.")
        tree = modifier.node_group
    return apply_to_interface(
        tree.interface, canon, create_missing=create_missing
    )


def dump_scene(canon: Canon | None = None) -> Scene:
    """Dump the current Blender file as a linter Scene."""
    bpy = _bpy()
    canon = canon or load()
    objects: list[SceneObject] = []
    for obj in bpy.data.objects:
        collections = obj.users_collection
        collection_name = collections[0].name if collections else ""
        role = obj.get("unit_canon.role")
        if not role and obj.name == canon.human_figure.asset_name:
            role = "human_figure"
        objects.append(
            SceneObject(
                name=obj.name,
                collection=collection_name,
                dimensions=(
                    float(obj.dimensions.x),
                    float(obj.dimensions.y),
                    float(obj.dimensions.z),
                ),
                location=(
                    float(obj.location.x),
                    float(obj.location.y),
                    float(obj.location.z),
                ),
                role=role,
            )
        )
    return Scene(objects=tuple(objects))


def lint_current_file(
    canon: Canon | None = None,
    *,
    require_roles: bool = True,
) -> LintResult:
    """Lint the open Blender file against the unit canon."""
    return lint(
        dump_scene(canon),
        canon,
        require_roles=require_roles,
    )
