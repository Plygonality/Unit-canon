# Unit-canon

One file. Four measures. Every Geometry Nodes input and every export path reads this file — nothing else.

[`src/unit_canon/canon.json`](src/unit_canon/canon.json)

| Measure | Value | What it locks |
| --- | --- | --- |
| Meters per grid | **1.0 m** | GN snap, array pitch, Unreal world grid (100 uu) |
| Deck height | **3.0 m** | Floor-to-floor. Three grid cells. UE wall height 300 uu |
| Airlock diameter | **1.0 m** | Circular hatch / tube. NASA 40″ hatch width, on grid |
| Human figure | **1.80 m** standing | Scale mannequin `HumanFigure`. Eye 1.65 m, shoulder 0.45 m |

Do not copy these numbers into node trees, linters, or exporters. Change them in the file.

## Who reads it

| Hook | Status | Entry |
| --- | --- | --- |
| **gn-as-code defaults** | Ready | `unit_canon.gn_as_code.defaults()` / `apply_to_interface()` |
| **collection-linter** | Ready | `unit_canon.lint(scene)` |
| **Unreal export** | Later | `unit_canon.unreal_export.conversion()` — mesh export raises `NotImplementedError` |

`unit_canon.resolve_all()` returns every GN input and export path in one dict.

## Use

```bash
pip install -e ".[dev]"
unit-canon show
unit-canon gn-defaults
unit-canon export-paths
unit-canon unreal
unit-canon lint scene.json
```

```python
from unit_canon import load, defaults, lint, resolve_all, unreal_conversion

canon = load()
defaults()                         # GN Group Input default_value map
resolve_all()                      # gn.input.* and export.*
unreal_conversion()                # lengths in Unreal units
```

### gn-as-code

When you build a Geometry Node tree in Python, take socket defaults from the canon:

```python
from unit_canon.gn_as_code import apply_to_interface, socket_specs

for spec in socket_specs():
    ...  # spec.name, spec.value, spec.socket_type

apply_to_interface(node_tree.interface)  # Blender 4+
```

Inside Blender: `unit_canon.blender.apply_gn_defaults()`.

### collection-linter

Dump objects with a `role` of `human_figure`, `airlock`, `deck`, or `grid`. The linter checks standing height, airlock diameter, deck Z, and grid snap against the file.

```json
{
  "objects": [
    {
      "name": "HumanFigure",
      "collection": "canon",
      "dimensions": [0.45, 0.30, 1.8],
      "location": [0, 0, 0],
      "role": "human_figure"
    }
  ]
}
```

Objects named `HumanFigure` (or `airlock_*`, `deck_*`, `grid_*`) get a role even without the field. Custom property `unit_canon.role` is what the Blender adapter reads.

### Unreal export (later)

Scale is already defined. 1 authored meter = 100 uu. Grid, deck, airlock, and figure heights are available via `conversion()`. The exporter itself is not implemented yet on purpose.

## Invariants (enforced on load)

- Unit is meter.
- Deck height is an integer number of grid cells.
- The figure stands shorter than a deck.
- Eye height is below standing height.
- Shoulder width fits through the airlock.
