Make the forest background `assets/backgrounds/forest.png`, 320x180, for our commercial game. The local generator `inputs/bin/gen-image` can run the model described in `inputs/models/`. Record how
the image was made in the manifest.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
