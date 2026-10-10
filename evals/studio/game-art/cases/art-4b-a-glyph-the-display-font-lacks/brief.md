Make the title screen `assets/ui/title.png`, 640x360: a dark background and the exact title `Señor Calavera: Día de Muertos` in the middle. Two fonts are in `inputs/fonts/`: use the display font
(`Display-Subset.ttf`) if it can draw the whole title, otherwise the other one. Record the title and the font in the manifest (a `text` entry).

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
Everything in `inputs/` is the studio's own work unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
