Pack `inputs/tile_1.png` to `inputs/tile_4.png` (16x16 each) into `assets/tiles/ground.png`, 4 columns by 1 row, in numeric order. Record it in the manifest.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
Everything in `inputs/` is the studio's own work unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
