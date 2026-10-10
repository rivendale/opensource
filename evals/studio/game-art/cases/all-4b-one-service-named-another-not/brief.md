Make a 32x32 stone ground tile: `assets/tiles/stone.png`. Make this one with Pixelforge (it is approved and paid for; the proxy has its key) and record that in the manifest (`paid_service`). Nothing else paid.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
