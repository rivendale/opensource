Pack the twelve walk frames `inputs/frame_1.png` to `inputs/frame_12.png` into one sheet, `assets/sprites/walk.png`: 6 columns by 2 rows, 32x32 per frame, in numeric
order (1 first, 12 last), left to right, top to bottom. Do not change the frames. Record it in the manifest.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
