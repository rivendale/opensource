# Studio evaluation cases

Cases for the studio skills in [skills/SPEC-studio.md](../../skills/SPEC-studio.md), written from that file by someone other than the skills' builder.
`evals/studio/<skill>/cases/<case>/` holds, as the spec's runner contract says: `brief.md` (what the operator asks), `inputs/` (read-only), `expected.json`
(the rules and thresholds, never shown to the skill) and `check.py` (the checker). The measurements are in [lib/studio_lib.py](lib/studio_lib.py).

```
python3 evals/studio/game-art/cases/<case>/check.py SCRATCH_DIR evals/studio/game-art/cases/<case>/expected.json
```

It prints `{"case": id, "rules": [{"id", "pass", "measured", "threshold"}]}` and exits 0 when every rule passes. A rule that cannot be measured fails and
says why; a checker never skips a rule. Needs Python 3.12 with Pillow and numpy (in the pinned image). A kept build script is run with the same interpreter and the same installed packages as the checker, an empty `HOME` and no other inherited variables, so Pillow installed in the user's site-packages also works. `STUDIO_LIB` can point `check.py` at the library
when the checker is mounted away from the repository.

## game-art

The cases are in [game-art/cases](game-art/cases). Each `expected.json` has `item` (the failure-list item it tests, `art-N` or `all-N`, or `control`), `kind`
(`M`: measured on files in the scratch directory by the checker; `T`: judged from what the skill recorded, here the manifest, against fixtures in `inputs/`;
`G`: needs a model or a GPU and is run by the operator) and `tools` (what must be in the image).

| item | cases | what the brief sets up |
|---|---|---|
| art-1 size, frames, palette, grid | art-1a, art-1b | a palette-locked 4x downscale where a blurred resize adds colors; a six-frame strip |
| art-2 transparency | art-2a, art-2b | a magenta matte with a pink scarf next to it; four icons on white with near-white highlights |
| art-3 frames | art-3a, art-3b | twelve frames whose file names sort wrongly as text; eight figures on different baselines and offsets |
| art-5 model and weights license | art-5a, art-5b | a stand-in generator whose default model is non-commercial (5a) or has no stated license (5b), for a game that is sold |
| art-8 one change per round | art-8a, art-8b | a mask-limited recolor of a hat, of a cloak within a palette |
| all-2 masters and rebuild scripts | all-2a, all-2b | layers that tempt a copy into `assets/`; three variants that must come from a script that rebuilds the same bytes |
| controls | art-c1 to art-c6 | the same checkers on briefs with no trap |

Not written yet: art-4 (text in images), art-6 (how a reference image entered), art-7 (style drift across a set) and the shared items 1, 3 and 4 (brief
restated and directions offered, an instruction inside an input, a paid service nobody named). Several of those need the transcript; a checker may read it
as `.run/transcript.md` in the scratch directory if the runner puts it there after the agent exits, which the runner contract does not yet say.

## How the checkers were checked

`python3 evals/studio/game-art/build/selfcheck.py` builds, for every case, a correct output tree and several defective ones (a blurred resize, a magenta rim, a
swapped order, a default model used, a hat and the boots both changed, layers left in `assets/`, a script that gives different bytes each run) and requires
the checker to pass the first and to fail each defect on exactly the rules it breaks. `build/make_cases.py` rewrites the case directories, including the
input images, from the same code, so the inputs are reproducible.

Every case was also solved once from its `brief.md` and `inputs/` alone by an agent that had not seen `expected.json` or any checker; all 18 solutions pass
their checkers. The first run found one checker that was too strict (a coin may touch the edge of its canvas); it was fixed before the cases were committed.
