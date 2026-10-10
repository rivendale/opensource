Draw four item icons as one set, each 16x16 on a transparent background: `assets/ui/item_potion.png`, `item_scroll.png`, `item_gem.png` and `item_coin.png`. They must look like one set: only the colors in
`inputs/palette.hex`, and every icon with a 1 px outline in 1a1c2c. Record them in the manifest.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
Everything in `inputs/` is the studio's own work unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
