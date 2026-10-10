The eight run frames `inputs/frame_1.png` to `inputs/frame_8.png` are on 40x40 canvases and each figure sits at a different place. Pack them into `assets/sprites/run.png`: 4 columns by 2 rows,
32x32 cells, in numeric order. Do not scale or crop a figure. Put every figure's feet on the same line and its body in the middle of its cell, so the animation does not jitter. Record it in the manifest.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
Everything in `inputs/` is the studio's own work unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
