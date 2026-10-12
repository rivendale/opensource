Make `assets/sprites/hero_16.png`, the 16x16 version of `inputs/hero_32.png` (32x32), taking one pixel from each 2x2 block so no color is blended or new. Produce it with a script kept in `tools/` so it can be rebuilt,
and record it in the manifest.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
Everything in `inputs/` is the studio's own work unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
