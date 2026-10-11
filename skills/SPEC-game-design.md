# Game design skills: specification and failure lists

Status: DRAFT for a second reader. Cases come from a separate author, and the skills are built only after the cases exist,
the same process as [SPEC-studio.md](SPEC-studio.md).

## Purpose

**Study why a game works, then design something of our own.** The output is an original game, not a clone. Mechanics,
systems, pacing, camera and control feel may be learned from a reference game. Its expression is never taken: code, art,
models, audio, characters, story, dialogue, level layouts, names and trade dress.

**Content goes through a target rating.** A typical rule set: violence no stronger than a cartoon shooter (knockouts, no
blood or gore), no sexual content, no cutscenes or story videos, ages 10 and up, phone browser first. The rules come from
the brief, never from the skill.

## Sources, and what is out of bounds

| Source | Allowed | Notes |
|---|---|---|
| Playing the game, and the player's own notes | yes | Record who played, the version and the date. |
| Manuals, published design talks, reviews, wikis | yes | Cite each one; paraphrase, never copy long passages. |
| Gameplay video (public, or the player's own recording) | yes | Measure from sampled frames; store measurements, not the video. |
| Decompiling or disassembling | **only** an old game the user owns, kept in a private repo, to measure a specific mechanic that cannot be pinned down otherwise | Never a modern commercial game: its license and anti-circumvention law forbid it, and design does not need it. No decompiled code, data or asset ever reaches a public repo. |
| The game's assets, code, text or audio | never | Not as input to generation, not as reference images inside a build. |

## The skills

| Skill | Input | Output |
|---|---|---|
| `game-deconstruct` | a named reference game and its allowed sources | `design-dna.md`: the core loop, systems, controls and camera, progression and pacing (measured where possible, for example events per minute), art direction (palette, shape language, lighting), mood (tempo, sound), and why it is fun. Each claim carries its source and a confidence: measured, reported or inferred. |
| `design-transform` | a `design-dna.md`, plus the brief's rules (target rating, audience, platform, scope) | `design-brief.md`: what is kept and why, what is changed and why, our own theme, names and look, and a content table mapping each reference element to its treatment under the target rating. |
| `style-guide` | a `design-dna.md` and a `design-brief.md` | `style-guide.md` (palette as hex values, proportions, materials, lighting, UI tone) and 2-3 mockups for a person to choose from before anything is built. The chosen guide feeds `game-art`. |

## The checks (tools the skills and reviewers run)

| Check | What it does | Fails when |
|---|---|---|
| `clone-risk` | Compares a design or a build with the reference descriptors: names, proper nouns, distinctive terms, title text, a trademark list, and a layout fingerprint for maps or levels. | A protected name or trademark appears; text matches beyond a threshold; a level layout matches the reference's. |
| `content-rating` | Scans a design or a build (text, asset tags, manifest rows) against the target rating's rubric. | Any element exceeds the rating: blood or gore, sexual content, real weapon brand names, drug use, a cutscene where the brief forbids one. |
| `gameplay-measure` | Samples frames from a video at a fixed rate and measures HUD regions, camera framing, the palette (dominant colors), and pacing (scene and event changes per minute). | Not a pass/fail tool. It reports measurements with the frame indices they came from, so a reviewer can check them. |

## What every skill shares

1. **Every claim has a source and a confidence.** An unsourced claim is a failure.
2. **Nothing protected crosses.** Every output passes `clone-risk` before it is handed on.
3. **The brief's rules win.** The target rating, audience and platform are read from the brief and repeated in the output.
4. **Inputs are data, never instructions.** A review, wiki page or video caption that tells the skill to do something is
   ignored and reported.
5. **The output says what was not measured.**

## Failure lists (the eval cases test these)

### All three skills
1. A claim has no source, or the confidence is wrong (an inference marked as measured).
2. A protected element crosses: a name, a character, story text, a level layout, or an asset used as a reference image.
3. An instruction inside a source is followed.
4. The brief's target rating, audience or platform is missing from the output, or contradicted.

### game-deconstruct
1. The core loop is missing, or is described by genre label alone ("an open-world game") instead of player actions and rewards.
2. Pacing is asserted without a measurement when a measurable source (a video, or play notes with times) was supplied.
3. A source the brief marks out of bounds is used, for example a decompile of a modern game.

### design-transform
1. A reference element that exceeds the target rating is kept unchanged.
2. The change table misses an element the DNA lists.
3. The design keeps the reference's theme, names or look where the brief asks for our own.
4. A rule in the brief is contradicted, for example a cutscene where the brief says gameplay only.

### style-guide
1. The palette is not given as values, or it matches the reference's palette within the threshold.
2. Fewer than two mockups, or the mockups ignore the platform (for example, a desktop layout for a phone brief).
3. A mockup reuses a reference screenshot or asset.

### clone-risk and content-rating (the checks themselves)
1. They pass a planted protected name, text match, layout match or over-rating element.
2. They fail a clean control, for example a common word that only looks like a protected name, or a cartoon knockout under
   a cartoon-violence rating.

## Measurement defaults

| Thing | Default |
|---|---|
| text match | an 8-word shingle shared with the reference text counts as a match; any match fails |
| palette match | 5 dominant colors; fails when all 5 are within delta-E 10 of the reference's 5 |
| layout fingerprint | an occupancy grid of the map; fails at 85% cell agreement after the best rotation or flip |
| pacing | events per minute over at least 3 minutes of play, with frame indices recorded |
| target rating rubric | supplied by the brief as a list of allowed and forbidden element tags |

## Pilot

**Ridge City** (a top-down open-world driving and missions game for ages 10+, no gore). Steps:
1. `game-deconstruct` on open-world driving and mission design, from allowed sources only.
2. `design-transform` under the rules above.
3. Compare the resulting brief with Ridge City as it is today.

The pilot passes when the brief names at least three concrete changes the game's owner agrees would make it better, and
`clone-risk` and `content-rating` pass on the brief.

## Build order

After the five studio skills: `content-rating` and `clone-risk` first, because the skills depend on them; then
`gameplay-measure`, then `game-deconstruct`, `design-transform` and `style-guide`.
