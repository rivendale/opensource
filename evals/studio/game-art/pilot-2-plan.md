# game-art follow-up pilot: plan, written before any run

This file is committed before the first run so that the thresholds cannot move after the results are seen. It tests the skill changes made after the first pilot
(see [the first tally](pilot-2026-10-12-tally.md)); it is a pilot, not a release gate.

## Fixed for every run

| | |
|---|---|
| skill | `skills/game-art` at `a1931a6` |
| model | `claude-sonnet-4-5-20250929` (the first pilot's model, so the comparison is on the skill) |
| runner | the merged runner on `main` (the verdict-completed, stderr-redacted, diagnostics-retained version) and the same pinned image |
| checker library | `main` at the commit that merged this file; the `restated`, `directions` and `empty_root` changes are in it |
| calls | one provider route, a per-run cap taken from the first pilot's largest run (297,428 tokens) plus 50% |
| tool errors | a nonzero tool exit is not a stop; two runs without a verdict, or any key incident, is |

## Runs (20)

| case | runs | what it tests | order |
|---|---|---|---|
| `all-2c-rebuilt-from-an-empty-root` | 3 | the rebuild wording and the new grader (first, so a grader fault shows early) | 1 |
| `leg-1-coin-pickup`, `leg-1-key-pickup`, `leg-1-potion-pickup` | 3 each (9) | the quality bar on subjects the skill's authors never saw as a failure | 2 (one of each first, then repeats) |
| `art-2a-magenta-matte` | 2 | the bar must yield to supplied art (every pixel kept) | 3 |
| `all-2b-exports-from-a-script` | 2 | the same, with a recolour of supplied art, and the multi-row manifest helper | 3 |
| `all-1a-brief-restated` | 2 | the quality bar on the subject of the first pilot's three gems | 4 |
| `all-1b-directions-before-art` | 2 | an open style still gets directions (the opposite-direction check) | 4 |

## Pre-registered readings

Each uses an absolute floor, so a set that scores zero cannot wave itself through. A threshold missed is reported as missed.

1. **Fidelity (art-2a, all-2b; 4 runs).** All four checker verdicts must be `passed`. One failure on silhouette, alpha or cloak colour means the quality bar is overriding supplied art: stop and report.
2. **Empty-root rebuild (all-2c; 3 runs).** `rebuild` must pass in at least 2 of 3. The first pilot's `all-2b` scripts passed only because the checker kept every folder; this is the first run of the stricter rule.
3. **Legibility (leg-1; 9 runs).** Two readers view every delivered icon blind (run order and case hidden) at 1x on mid-grey and on light grey and answer one question: *would a player know this is a [subject]?*
   At least 5 of 9 yes, and no more than 2 no. The first pilot's three gems were 0 yes, 1 marginal, 2 no. The two readers' agreement is reported; a disagreement is reported as a split, not averaged.
4. **Directions (all-1b; 2 runs).** Both must pass `directions` and export nothing.
5. **All-1a (2 runs).** Checker verdict passed in both. Their legibility is reported beside the first pilot's, not pooled with leg-1, because the gem is the subject the bar was written from.
6. **Tool errors (all 20).** Counted per run from the transcript. The first pilot's median was two recovered errors per run. Targets: no `credits` flag error, no `/tmp` write, no `magick` before `convert`, no manifest-helper bypass and no `--exports` in a subfolder, in at least 18 of the 20 runs each.
7. **Unmeasured PASS claims.** Any report line that states a measurement with no command in the transcript is counted; the target is zero in 20.

## What is not claimed

No automated legibility rule exists; the legibility column is a human view and says so. Twenty runs of one model on one skill commit say nothing about other models. A result inside the
thresholds is a pilot result, not a score of the skill.
