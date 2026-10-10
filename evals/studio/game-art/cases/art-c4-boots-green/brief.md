Revision: make the hero's boots green (`inputs/boots_mask.png` shows them) and change nothing else. Export `assets/sprites/hero_v2.png` from `inputs/hero_v1.png` and record it in the manifest.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
