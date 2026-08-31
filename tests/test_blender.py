"""Blender adapter stays optional; bpy is not required to use the canon."""

from __future__ import annotations

import pytest

from unit_canon import blender


def test_adapter_requires_bpy() -> None:
    with pytest.raises(RuntimeError, match="bpy"):
        blender.apply_gn_defaults()
    with pytest.raises(RuntimeError, match="bpy"):
        blender.dump_scene()
    with pytest.raises(RuntimeError, match="bpy"):
        blender.lint_current_file()
