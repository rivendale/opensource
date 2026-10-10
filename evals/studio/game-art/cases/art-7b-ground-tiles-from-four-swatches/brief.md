Draw three ground tiles that belong together, 16x16 each: `assets/tiles/ground_a.png`, `ground_b.png` and `ground_c.png`. Use only the four swatches in `inputs/swatches.hex`, and use at least two of them
in each tile. Record them in the manifest.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
Everything in `inputs/` is the studio's own work unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
