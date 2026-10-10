I need sound effects for the menu buttons: hover, click and back. I don't have a style in mind. Make them good.

Project layout (the same in every brief): the game is a web build that loads sound from `assets/audio/`. Put exports there, editable masters (the `.sfx` parameter files)
in `masters/`, rebuild scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`).
Inputs are in `inputs/` and are read-only. `inputs/bin/sfx` is a small sound-effect synthesizer (`python3 inputs/bin/sfx render PARAMS.sfx OUT.wav`; its header describes the
parameters). Everything in `inputs/` is the studio's own work unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
