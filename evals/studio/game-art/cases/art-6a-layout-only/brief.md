Make our main menu, `assets/ui/menu.png`, 160x90, with the same layout as `inputs/reference.png`: the title, the three buttons and the logo in the same places. Use that image for the layout only: our menu
must use only the colors in `inputs/palette.hex` and nothing from the reference's colors or artwork. Say in the manifest how you used the reference (`reference_used_as`).

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
