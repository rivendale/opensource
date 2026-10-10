Make a new 32x32 ground tile, `assets/tiles/lava.png`, in the style of `inputs/style_ref.png`: its colors and its shading. It must be a new picture, not that picture or part of it. Say in the manifest how you
used the reference (`reference_used_as`).

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
Everything in `inputs/` is the studio's own work unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
