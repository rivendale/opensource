Revision round for the hero: `inputs/hero_v1.png` is the current sprite. Make the hat red and change nothing else. Export it as `assets/sprites/hero_v2.png` and record it in the manifest.
`inputs/hat_mask.png` shows where the hat is.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
