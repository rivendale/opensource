Make the title screen `assets/ui/title.png`, 640x360: a dark background and the exact title `Lantern-Run: Ember Vale` in the middle. A font is in `inputs/fonts/`, and `inputs/bin/gen-image` can make
images and add words to them with `--text`. Record the title and the font you drew it with in the manifest (a `text` entry).

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
Everything in `inputs/` is the studio's own work unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
