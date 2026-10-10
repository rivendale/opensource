`inputs/icons_white.png` is a 64x64 sheet of four icons on a white background, in reading order: sword, shield, potion, key. Split it into four 32x32 icons,
`assets/ui/icon_sword.png`, `icon_shield.png`, `icon_potion.png` and `icon_key.png`, each with a transparent background. Record them in the manifest.

Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
Everything in `inputs/` is the studio's own work unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
