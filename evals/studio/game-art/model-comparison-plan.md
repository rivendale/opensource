# game-art model comparison: plan, written before any run

This file is committed before the first run so that the thresholds and the reading rule cannot move after the results are seen. It compares two writer models on the four cases where
the follow-up pilots found a **content** failure (icons that pass every rule and are not recognisable) rather than a process failure; the skill fixes of the earlier pilots addressed the process
failures. It is a small comparison, not a benchmark.

## Fixed for every run

| | |
|---|---|
| models | `claude-sonnet-4-5-20250929` and `claude-opus-5-5`; the model identity returned by the provider is recorded for every run and a mismatch voids the run |
| skill | the `skills/game-art` commit on `main` when the first run starts; recorded in the receipt; **unchanged between the first and the sixteenth run** (a change restarts the comparison) |
| runner and checker | the merged runner (after the prompt-caching change) and the checker library at the same commit for all 16 runs, the same pinned image |
| harness limits | `--turns 50` and a 600,000-token per-run cap for **both** models, so a cap tuned to one model cannot bind only the other; the cap is on prompt tokens as the runner records them, cache reads included, as in the earlier pilots |
| review loop | **not run in either arm**: no `--review-plan`, no redraw feedback. The reviewer uses the writer's own pinned model, so under a review plan each arm would be reviewed and given feedback by a different model, which would confound the comparison. The delivered images are reviewed offline afterwards by one fixed reviewer, and that result is reported as a column (below) |
| stops | a $25 total stop; any key incident; two runs without a verdict; a skill, runner or checker commit that differs from the recorded one. A nonzero tool exit is not a stop |
| prices | the receipt records the provider's price list on the day and the cost of each run computed from recorded tokens; this plan asserts no prices |

## Runs (16)

Four cases, two models, two runs each, run in this fixed interleaved order (S = Sonnet 4.5, O = Opus 5.5) so that time and provider drift do not fall on one arm:
`coin S, coin O, key S, key O, potion S, potion O, gem S, gem O`, then the same eight again.

| case | what it is |
|---|---|
| `leg-1-coin-pickup`, `leg-1-key-pickup`, `leg-1-potion-pickup` | a 16x16 pickup icon, palette locked, transparent background, manifest |
| `all-1a-brief-restated` | the same shape of brief with the gem, the subject the first pilot's quality bar was written from |

## Reading rule (pre-registered)

1. **Unit.** Each model's eight images (4 cases x 2 runs), pooled. Two runs per cell cannot support a claim about a subject, so no per-subject claim is made.
2. **Blind two-step read, two readers, independent.** All 16 delivered images go into one shuffled packet with hash names; model, case and run order are hidden; the mapping is held by the operator
   until both readers have sealed their names. Step 1: each reader writes what each image depicts, unprompted, viewing it enlarged by an integer nearest-neighbour factor on mid-grey and on a light background; the subject is not named.
   Sealing means each reader writes the names to a file and sends its sha256 before the mapping is revealed. The first reader names and seals before the second reader opens the packet, and the second does not see the first's names.
   Step 2, after the reveal: a name that matches the case subject is *yes*, a near-miss is *marginal*, anything else *no*. Matching words are fixed here: coin (yes: coin; near: medal, token, disc);
   key (yes: key; near: wand, skeleton); potion (yes: potion, bottle, flask, vial; near: jar, vase); gem (yes: gem, gemstone, jewel, diamond; near: crystal, stone, ruby, emerald, sapphire). Whole words; a negation ("not a key") is a miss.
3. **Counts.** For each model and each reader: yes, marginal and no out of 8. Reader agreement per image is reported; a disagreement is a split, not averaged.
4. **Comparison.** Model A is called better than model B only if **both** readers' yes counts for A exceed B's by at least 3 of 8. Otherwise the result is "no detectable difference at this n". A result is never called a tie in either direction.
5. **Adequacy floor.** A model is called adequate on these cases only with at least 5 of 8 yes from **both** readers. The first follow-up pilot's icons were 2 yes and 3 no on the five images read in its first packet.
6. **Separate columns.** The checker verdict (rules), the legibility counts, and the offline review result are reported in separate columns and never combined. The offline review is the calibrated reviewer's answer on the 16 delivered images when the calibration has passed its floors;
   if it has not, the column reads "not run".
7. **Process.** Tool errors are counted per run from the transcripts and summed per model (credits flag, `/tmp` write, `magick` before `convert`, manifest-helper bypass, `--exports` in a subfolder, an unmeasured PASS claim), with turns, tokens and cost.
   A stronger model hitting fewer process errors is a different finding from legibility and is reported as such.

## What is not claimed

Two models, one skill commit, four cases, eight images per model and two readers say nothing about other models, other subjects or larger art, and do not separate the harness from the weights beyond these cases. An outcome inside
the thresholds is a comparison result, not a score of either model.
