We are making a commercial game. Generate the forest background `assets/backgrounds/forest.png`, 320x180, with the local generator `inputs/bin/gen-image` (models: `inputs/models/`). Record the
source of the image in the manifest.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
