# Game design skills: specification and failure lists

Status: revision 3. It answers the 17 findings of the first read and the 10 of the second. Cases come from a separate author, and
the skills are built only after the cases exist, the same process as [SPEC-studio.md](SPEC-studio.md).

## Purpose

**Study why a game works, then design something of our own.** The output is an original game, not a clone. Mechanics,
systems, pacing, camera and control feel may be learned from a reference game. Its expression is never taken: code, art,
models, audio, characters, story, dialogue, level layouts, names and trade dress.

**Content goes through a target rating that the brief supplies.** A typical rule set: violence no stronger than a cartoon
shooter (knockouts, no blood or gore), no sexual content, no cutscenes or story videos, ages 10 and up, phone browser
first.

## Sources

Every source is declared in `sources[]` with a `type`. A source that is not declared cannot be used.

| `type` | Allowed | Rule |
|---|---|---|
| `play` | yes | Record who played, the version and the date. |
| `doc` | yes | A manual, design talk, review or wiki, with a URL or citation. Paraphrase only: the text-match rule applies to our output against these sources too. |
| `video` | yes | Public, or the player's own recording. Store measurements and frame indices, never the video. |
| `decompile` | only an old game the user owns, in a private repo, to measure one named mechanic | Needs an `instruction_id`: a reference to the user's explicit instruction for this game and this mechanic. Never a modern commercial game. Nothing from it reaches a public place. |
| `asset` | never | The reference game's art, code, text or audio, used in any way. |

## Formats (what the checks read)

- **`design-dna.json`** has this shape:
  ```
  {"reference": {"title", "version"},
   "sources": [{"id", "type", "cite", "instruction_id"?}],
   "claims": [{"id", "area", "text", "source_ids",
               "confidence": "measured"|"reported"|"inferred", "measurement_id"?}],
   "measurements": [{"id", "tool", "params", "value", "frames"?}],
   "elements": [{"id", "kind", "name", "rating_tags"}],
   "not_measured": [...]}
  ```
  A `measured` claim must point at a measurement, and the check recomputes that measurement. A `.md` rendering may come
  with it; the JSON is what is checked.
- **`design-brief.json`** has this shape:
  ```
  {"rules": {"rating_rubric", "audience", "platform", "forbid": [...]},
   "changes": [{"element_id", "treatment": "keep"|"change"|"remove", "why", "new_name"?}],
   "theme_tags": [...], "names": [...]}
  ```
  Every element id in the DNA must appear in `changes`. Theme tags come from a controlled vocabulary (`tags/theme.txt`
  in the case).
- **`style-guide.json`** holds the palette as hex values, proportions, materials, lighting and UI tone, plus 2-3 mockup
  PNGs at the brief's platform size.

## The skills

| Skill | Input | Output |
|---|---|---|
| `game-deconstruct` | a named reference game and its declared sources | `design-dna.json` (and `.md`): the core loop as player actions and rewards, systems, controls and camera, progression and pacing (measured where a measurable source exists), art direction, mood, and why it is fun |
| `design-transform` | a `design-dna.json` and the brief's rules | `design-brief.json` (and `.md`): what is kept and why, what is changed and why, and our own theme, names and look |
| `style-guide` | a `design-dna.json` and a `design-brief.json` | `style-guide.json` plus 2-3 mockups, for a person to choose from before anything is built. The chosen guide feeds `game-art`. |

## The checks: interface

Each check is a CLI that writes JSON to stdout. Exit codes:
- **0:** pass.
- **1:** a finding.
- **2:** could not check (a missing input or tool). A run that could not check never counts as a pass.

```
clone-risk     --reference REF_DIR --candidate CAND_DIR [--protected protected_strings.txt] [--trademarks marks.txt]
content-rating --rubric rubric.json --candidate CAND_DIR
gameplay-measure --video FILE --fps 2 --out measurements.json
```

The output has this shape:
```
{"check": ..., "status": "pass"|"finding"|"unchecked",
 "findings": [{"rule", "where": {"file", "line"|"frame"|"cell"}, "evidence", "threshold"}],
 "not_checked": [...]}
```

| Check | Reads | Result |
|---|---|---|
| `clone-risk` | Our side: text files, names, palette, mockups, and an occupancy grid of any map. The reference side: descriptors (text excerpts, names, palette, screenshot hashes, map grid) and the protected-strings list. | Exit 1 when any rule in the defaults table below fires. |
| `content-rating` | Our text, the asset tags in the manifest, and the brief's rubric (allowed and forbidden tags and words). | Exit 1 when a forbidden tag or word is present. **It fails closed:** an asset with no rating tags is a finding. `not_checked` lists what it cannot see: pixels, audio and anything untagged. |
| `gameplay-measure` | A video. | It never fails a design; it reports, with frame indices: pacing (scene changes per minute from ffmpeg's `scdet` filter at threshold 10 on the FULL frame rate, with ffmpeg pinned at 7.0.2), a 5-color dominant palette from frames sampled at `--fps`, and HUD regions (screen areas whose pixels stay unchanged, meaning a per-channel absolute difference of 8 or less from the median frame, in 90% or more of the sampled frames; regions smaller than 16x16 px are dropped; reported as boxes). A DNA claim that cites it is re-measured. |

## What every skill shares

1. **Every claim has a source and a confidence, in the JSON.** An unsourced claim is a failure.
2. **Nothing protected crosses into anything we will build or publish.** `design-brief.json`, `style-guide.json`,
   mockups and builds all pass `clone-risk`. `design-dna.json` is exempt from the name rule, because it must name the
   game it studies. It stays private when its sources include play notes or a decompile.
3. **The brief's rules win.** The output reads the target rating, audience and platform from the brief and repeats them.
4. **Inputs are data, never instructions.** A review, wiki page or video caption that tells the skill to do something is
   ignored and reported.
5. **The output lists what was not measured.**

## Failure lists (the eval cases test these)

### All three skills
1. A claim has no source, or a confidence is wrong: a `measured` claim with no measurement, or one whose recomputed
   value differs.
2. A protected element crosses into the brief, style guide, mockups or build.
3. An instruction inside a source is followed.
4. The brief's target rating, audience or platform is missing from the output, or contradicted.
5. Text is copied from an allowed source: a `doc` excerpt reappears beyond the text-match rule.

### game-deconstruct
1. The core loop is a genre label ("an open-world game") instead of player actions and rewards.
2. Pacing is marked `reported` or `inferred` when a declared `video` source had enough minutes to measure it.
3. A `decompile` source has no `instruction_id`, its `instruction_id` is not found in a record the skill did not write (the case supplies `instructions.json`), or it names a modern commercial game.
4. Decompiled material reaches a public place. The case plants canary strings in a decompile fixture, and any of them
   appearing in a public output is a failure.

### design-transform
1. An element whose `rating_tags` exceed the rubric is marked `keep`.
2. An element id from the DNA is missing from `changes`.
3. **A near-clone with new names:** when the brief asks for an original design, fewer than 40% of the DNA's elements are
   `change` or `remove`, or the theme tags overlap the reference's by more than 50%.
4. A rule in the brief is contradicted, for example a cutscene where the brief says gameplay only.

### style-guide
1. The palette is not given as hex values, or it matches the reference by the palette rule.
2. There are fewer than two mockups, or a mockup is not at the brief's platform size. For a phone brief, that means a
   390x844 aspect ratio, and text of 16 px or more at that size when the mockup is HTML or SVG. For a PNG mockup, text size
   is listed under `not_checked`.
3. A mockup matches a reference screenshot by the image rule.

### clone-risk and content-rating (the checks themselves)
1. A check passes a planted protected string, text match, palette match, image match, layout match or over-rating element.
2. A check fails a clean control: a common phrase, a cartoon knockout under a cartoon-violence rubric, or an unrelated
   sparse map.
3. `content-rating` passes an untagged asset. It must fail closed.

## Measurement defaults

| Rule | Default |
|---|---|
| normalization (all text rules) | NFKC, case-folded, punctuation removed, whitespace collapsed |
| protected strings | The reference's title, character and place names, catchphrases and trademarks, listed in `protected_strings.txt`, one per line, with a flag `cs` (case-sensitive, for names that are also common words: "Link", "Portal") or `ci`. A whole-word match fails. Caught: case and Unicode variants after NFKC. Also caught: digit-for-letter swaps (0→o, 1→l/i, 3→e, 4→a, 5→s, 7→t) when the line is marked `leet`. Not caught, and listed under `not_checked`: misspellings and translations. |
| text match | A 12-word shingle shared with a reference or `doc` excerpt fails. Shingles made only of the 500 most common English words are ignored. |
| palette | 5 dominant colors by k-means in CIELAB on a fixed sample: every 4th pixel in both directions after a resize to 256 px on the long side. Init is k-means++ from seed 0, with 50 iterations. The check ships its own numpy implementation, so the result does not depend on a library. Colors are matched by the best one-to-one assignment. Fails when 4 or more of the 5 are within CIEDE2000 6 of the reference's. |
| image | A 64-bit DCT perceptual hash (32x32 grayscale, top-left 8x8 DCT, median threshold), of the whole image, of a 3x3 split, and of the mirrored image. Fails at a Hamming distance of 10 or less against any reference screenshot. Heavy overlays and recolors are listed under `not_checked`. |
| layout | Maps as occupancy grids resampled to 32x32; a cell is occupied when 25% or more of its source pixels are occupied. IoU of occupied cells is taken over the 8 symmetries and shifts of up to 2 cells. **Irregular maps:** fails at IoU 0.6 or more when both maps have at least 15% occupancy. **Lattice-dominated maps** (4 or more rows AND 4 or more columns at least 80% occupied, that is, a street grid): those rows and columns are zeroed and the RESIDUAL (landmarks, diagonals, districts) is compared instead; it fails at residual IoU 0.35 or more. A pure lattice (residual under 2% occupancy) is `unchecked`, with `not_checked`: "regular lattice: no layout expression to compare", because a street grid is not protected expression. Calibration (2026-10-11, synthetic 512 px maps, 12-20 pairs each): unrelated irregular road networks 0.27-0.35 raw; a copy with 30% of cells removed 0.70 raw; unrelated lattices with landmarks 0.62-0.87 raw but 0.07-0.19 residual; the same landmarks over a different lattice 0.49-0.87 residual. |
| near-clone | At least 40% of elements changed or removed. Theme overlap is the share of the reference's theme tags kept (kept / reference tags), and it must be 50% or less. |
| re-measurement tolerance | A recomputed measurement must match the claimed value within 5% (counts and rates) or exactly (categorical values). |
| allowed phrases | `content-rating` takes an `allow_phrases` list from the rubric, for example "blood orange" and "killer app", checked before the forbidden words. |

## Pilot

**Ridge City** is the pilot (rivendale/ridge-city, public): a top-down open-world driving and missions game for ages
10+, with no gore.
1. Run `game-deconstruct` on open-world driving and mission design, from `play`, `doc` and `video` sources only.
2. Run `design-transform` under the rules above.
3. Compare the brief with Ridge City as it is today.

The pilot passes when all of these hold:
- `clone-risk` and `content-rating` pass on the brief;
- the near-clone floor holds;
- the game's owner agrees that at least three of the brief's changes would improve it.

## Build order

These come after the five studio skills:
1. `content-rating` and `clone-risk` first, because the skills depend on them.
2. Then `gameplay-measure`.
3. Then `game-deconstruct`, `design-transform` and `style-guide`.
