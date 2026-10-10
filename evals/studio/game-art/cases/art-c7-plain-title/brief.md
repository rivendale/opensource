Make the title screen `assets/ui/title.png`, 640x360: a dark background and the exact words `Ember Vale` in the middle, drawn with the font in `inputs/fonts/Body-Accents.ttf`. Record the title and the font
in the manifest (a `text` entry).

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
