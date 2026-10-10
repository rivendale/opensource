Pack the six frames `inputs/frame_1.png` to `inputs/frame_6.png` into one horizontal strip, `assets/sprites/ball_roll.png`: 6 columns by 1 row, 32x32 per frame. Record it in the manifest.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
