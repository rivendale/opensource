Revision round: the hero in `inputs/hero_v1.png` should have a blue cloak (`inputs/cloak_mask.png` shows the cloak). Use only the colors in `inputs/palette.hex`, change nothing else, and export
`assets/sprites/hero_v3.png`. Record it in the manifest.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
