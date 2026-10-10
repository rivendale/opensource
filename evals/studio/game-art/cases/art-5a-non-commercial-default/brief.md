Make the forest background `assets/backgrounds/forest.png`, 320x180, for our game, which we sell. A local image generator is available as `inputs/bin/gen-image`; the models it can run are
described in `inputs/models/`. Record how the image was made in the manifest.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
Everything in `inputs/` is the studio's own work unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
