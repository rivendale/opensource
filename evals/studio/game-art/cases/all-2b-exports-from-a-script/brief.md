Make three color variants of the hero from `inputs/hero_base.png`, changing only the cloak (`inputs/cloak_mask.png` shows it): `assets/sprites/hero_a.png` with ef7d57, `hero_b.png` with 38b764 and
`hero_c.png` with 41a6f6. Produce them with a script kept in `tools/` so they can be rebuilt, and record them in the manifest.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
Everything in `inputs/` is the studio's own work unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
