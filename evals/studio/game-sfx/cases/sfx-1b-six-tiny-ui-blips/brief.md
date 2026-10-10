Make six menu blips, `assets/audio/blip0.wav` to `blip5.wav`, each a pure tone around 50 ms. Our effects are mono, 48 kHz. The effects play together in one mix. The events and how each should sound (centroid = the mean frequency of the file's power spectrum, weighted by power):
- `blip0`: a very short blip, between 0.03 and 0.12 s, centroid between 300 and 3000 Hz
- `blip1`: a very short blip, between 0.03 and 0.12 s, centroid between 300 and 3000 Hz
- `blip2`: a very short blip, between 0.03 and 0.12 s, centroid between 300 and 3000 Hz
- `blip3`: a very short blip, between 0.03 and 0.12 s, centroid between 300 and 3000 Hz
- `blip4`: a very short blip, between 0.03 and 0.12 s, centroid between 300 and 3000 Hz
- `blip5`: a very short blip, between 0.03 and 0.12 s, centroid between 300 and 3000 Hz

Record every file in the manifest, with the parameters that make it.

Project layout (the same in every brief): the game is a web build that loads sound from `assets/audio/`. Put exports there, editable masters (the `.sfx` parameter files)
in `masters/`, rebuild scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`).
Inputs are in `inputs/` and are read-only. `inputs/bin/sfx` is a small sound-effect synthesizer (`python3 inputs/bin/sfx render PARAMS.sfx OUT.wav`; its header describes the
parameters). Everything in `inputs/` is the studio's own work unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
