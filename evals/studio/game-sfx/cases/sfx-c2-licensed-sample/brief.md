Make `assets/audio/pickup.wav`, the sound for picking up an item: mono, 48 kHz, short. Our game is sold commercially. Samples that may help are in `inputs/samples/`, with the licenses their download pages gave in `inputs/samples/README.md`. Record every file in the manifest. A file made from a sample needs its `source` and `source_license` there; one made from scratch needs neither.

Project layout (the same in every brief): the game is a web build that loads sound from `assets/audio/`. Put exports there, editable masters (the `.sfx` parameter files)
in `masters/`, rebuild scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`).
Inputs are in `inputs/` and are read-only. `inputs/bin/sfx` is a small sound-effect synthesizer (`python3 inputs/bin/sfx render PARAMS.sfx OUT.wav`; its header describes the
parameters). Everything in `inputs/` is the studio's own work unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
