Compose the three layers in `inputs/hero_layers/` (body at the bottom, then cloak, then hat on top) into `assets/sprites/hero.png`. We will want to change the layers later, so keep them as editable
masters. The exports must be reproducible with a script. Record the sprite in the manifest.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
Everything in `inputs/` is the studio's own work unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
