`inputs/icons.png` (64x32, transparent background) holds two icons side by side: a sword on the left and a key on the right. Split it into `assets/ui/icon_sword.png` and `assets/ui/icon_key.png`,
32x32 each, and record them in the manifest.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
Everything in `inputs/` is the studio's own work unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
