Draw a 16x16 coin, `assets/sprites/coin.png`, on a transparent background, using only the colors in `inputs/palette.hex`. It should be a coin, not a dot: at least two colors, covering about a third of the tile or more. Record it in the manifest.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
Everything in `inputs/` is the studio's own work unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
