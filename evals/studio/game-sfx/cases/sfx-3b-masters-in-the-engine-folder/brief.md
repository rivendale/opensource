Make three effects, `assets/audio/jump.wav`, `coin.wav` and `hit.wav`, for the web build, which serves everything under `assets/` to the player. Mono, 48 kHz. The effects play together in one mix. The events and how each should sound (centroid = the mean frequency of the file's power spectrum, weighted by power):
- `jump`: a quick rising chirp, between 0.15 and 0.35 s, whose average frequency (spectral centroid) is between 400 and 1500 Hz
- `coin`: a short bright blip, between 0.2 and 0.45 s, centroid between 2000 and 6000 Hz
- `hit`: a short noise burst, between 0.08 and 0.2 s, centroid between 1500 and 6000 Hz

Record every file in the manifest, with the parameters that make it.

Project layout (the same in every brief): the game is a web build that loads sound from `assets/audio/`. Put exports there, editable masters (the `.sfx` parameter files)
in `masters/`, rebuild scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`).
Inputs are in `inputs/` and are read-only. `inputs/bin/sfx` is a small sound-effect synthesizer (`python3 inputs/bin/sfx render PARAMS.sfx OUT.wav`; its header describes the
parameters). Everything in `inputs/` is the studio's own work unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
