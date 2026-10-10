`inputs/hero_matte.png` is a 32x32 character on a solid magenta (ff00ff) background. Cut the character out and export `assets/sprites/hero.png` with a transparent background on
the same 32x32 canvas. Keep every pixel of the character. Record it in the manifest.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
