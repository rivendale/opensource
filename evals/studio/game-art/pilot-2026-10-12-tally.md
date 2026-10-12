# game-art pilot, 2026-10-12: tally of 15 runs

One skill (`skills/game-art`), one model (`claude-sonnet-4-5-20250929`), the studio runner, no external services. This is a **pilot**, not a score of the
skill: the skill text changed between run 1 and run 4, three of the four cases were run three times, and two of the fifteen runs never produced a verdict.
Every transcript was read by hand against its checker result before this table was written; the "legible at 1x" column is a human view of the delivered
image, answering one question: *would a player know this is a [subject] at 1x, on mid-grey and on a light background?*

| run | case | checker verdict | legible at 1x | notes |
|---|---|---|---|---|
| 1 | art-1a-palette-locked-downscale | passed 5/5 | not viewed | skill cd69414, runner 61af783; 205,207 tokens; the transcript showed a rebuild that was not byte-identical (timestamp chunks), an invented manifest date and a PASS reported without the measurement |
| 2 | all-1a-brief-restated | no verdict | n/a | the runner reported the checker's exit code 1 as a crash; no tree was kept |
| 3 | all-1a-brief-restated | failed | n/a | one response: restated, then asked which of four styles; no export. Under the corrected `restated` rule the other five rules still fail |
| 4 | all-1a-brief-restated | passed 6/6 | **no** | reads as a tree or a hot-air balloon: banded hues, a stem, no outline; 289,702 tokens |
| 5 | all-1a-brief-restated | passed 6/6 | marginal | a blue crystal by silhouette, but the dark shade is drawn outside the body (a spike on the right, sprite off-centre); 297,428 tokens |
| 6 | all-1a-brief-restated | passed 6/6 | **no** | reads as a bottle or a bud; 44 turns |
| 7 | all-1b-directions-before-art | passed | n/a | four headed directions, no tool calls, nothing exported |
| 8 | all-1b-directions-before-art | passed | n/a | the same |
| 9 | all-1b-directions-before-art | passed | n/a | the same |
| 10 | all-2b-exports-from-a-script | passed 10/10 | yes | the three PNGs are byte-identical to runs 11 and 12 |
| 11 | all-2b-exports-from-a-script | passed 10/10 | yes | |
| 12 | all-2b-exports-from-a-script | passed 10/10 | yes | |
| 13 | art-2a-magenta-matte | passed 6/6 | yes | matte clean, silhouette IoU 1.0; byte-identical to runs 14 and 15 |
| 14 | art-2a-magenta-matte | passed 6/6 | yes | |
| 15 | art-2a-magenta-matte | passed 6/6 | yes | |

Runs 4 to 15 used skill f41b514, runner 145e9d5, and the checker library at 897725c. Token counts for runs 6 to 15 were not recorded in the files read.
`rebuild_identical` for runs 10 to 12 was not re-run by the reader (no ImageMagick on the reading host); each agent's own byte comparison was identical.

## What the checker could not see

- **Legibility.** Three of the three `all-1a` gems passed every rule and one of them is a bottle. Size, palette and transparency are necessary, not sufficient;
  the brief does not say "reads as a gem" and no rule pretends to judge it. Report the two columns separately.
- **Rebuild from an empty root.** `all-2b` copies the whole project, deletes the export and re-runs the script, so a script that never creates `assets/sprites/`
  passes. `all-2c` below grades the stricter condition.
- **A directions rule that counted bullets.** `all-1b` passed any three bullets of at least five words; one direction described in three bullets would have passed.
  The rule now counts distinct named directions (see the change list).

## Tool errors, by how many runs they hit

Every one recovered within one to six turns and none changed a verdict. They are listed in the order they should be fixed in the skill.

| error | runs hit | which |
|---|---|---|
| `art.py credits` called with invented flags (`--manifest`, `--root`), exit 2 | 7 of the 9 runs that reached a credits step | 4, 6, 10, 12, 13, 14, 15 |
| `/tmp` is read-only in the runner (a rebuild test, a row file) | 6 | 4, 10, 12, 13, 14, 15 |
| `magick` tried before `convert` (the runner has ImageMagick 6) | 6 | 5, 6, 10, 13, 14, 15 |
| the manifest helper refuses one row at a time once the exports exist; the agent hand-wrote the manifest (as an array first) and found the validator's CLI by trial | 3 of 3 `all-2b` runs | 10, 11, 12 |
| `--exports` given the export's own folder, so `MANIFEST.json` landed in `assets/sprites/` and was moved | 2 of 3 `art-2a` runs | 13, 14 |
| `check --alpha transparent` refused without `--matte` when the brief names no matte | 2 of the 3 `all-1a` runs that checked (the third skipped the check) | 4, 6 |
| a report line that claims a measurement that was never run (a rebuild, a transparency check) | 2 | 1, 5 |
| ImageMagick 6 wrote a palette-mode PNG when remapping, about eight turns lost | 1 | 6 |
| build script does not create its own output folder, so a rebuild test in a clean directory failed | 2 failed, 1 latent | 5, 13 failed; 10 passed only because its test tree already had the folder |

## Grader changes this pilot produced

- `restated_before_acting`: reading an input (a read-only command, an image view) is not acting. The window ends at the first call that is not recognizably read-only.
  Run 3's restatement was complete and failed the old rule. Only `all-1a` uses the rule.
- `directions_offered` (all-1b and the audio set's `sfx-all1-style-open`): counts distinct named directions (headed, numbered with a label, or labelled top-level
  bullets), not bulleted lines. Re-grading the three real `all-1b` runs: four directions each, unchanged verdicts.
- `rebuild_identical` takes `empty_root: true`: the copy holds only `inputs/`, `tools/`, `masters/` and the manifest. New case `all-2c-rebuilt-from-an-empty-root`.
- The pilot's verdicts above were produced by the checkers in place at the time; the first two changes were checked against the real transcripts and move no verdict.
