Make three cues for the game: `assets/audio/town.wav` (120 BPM, 32 beats), `battle.wav` (140 BPM, 32 beats, D minor) and `menu.wav` (90 BPM, 24 beats). They play one after another, so they should sit at the same loudness. Mono, 48 kHz. Record them in the manifest and keep the scores.

Project layout (the same in every brief): the game is a web build that loads sound from `assets/audio/`. Put exports there, editable masters (scores) in `masters/`, rebuild scripts
in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
`inputs/bin/mus` renders a score file to a WAV (`python3 inputs/bin/mus render SCORE.score OUT.wav`; its header describes the score format). Everything in `inputs/` is the studio's own work
unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
