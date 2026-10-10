Make a 10 s promo for our game, which we sell: `assets/video/trailer.mp4`, 1280x720, 25 fps, 16:9, H.264 and AAC at 48 kHz, using the harbor and market footage and the free music with the narration. The platform wants -14 LUFS integrated, true peak at most -1 dBTP. Keep the narration by itself as `assets/audio/narration.wav` (render `inputs/script.txt` with `inputs/bin/tts`). Record both files in the manifest, naming every input used.

Project layout (the same in every brief): exports go in `assets/` (video in `assets/video/`, audio in `assets/audio/`), editable masters and project files in `masters/`, rebuild scripts in
`tools/` (a script is run from the project root with `ffmpeg` on the path and no network), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`; a row can
name several inputs in `source` and their licenses in `source_license`, separated by semicolons). Inputs are in `inputs/` and are read-only. Everything in `inputs/` is the studio's own work
unless its README says otherwise.
