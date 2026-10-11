# Running the studio cases in the evaluation lane

What the runner needs from this directory, and how to prove it before any model is called. The runner contract is in [SPEC-studio.md](../../skills/SPEC-studio.md#evaluation-lane).

## The checker library bundle

Every `check.py` imports the shared library. The runner mounts it read-only when it admits the answers (the same moment as `check.py` and `expected.json`), records the hash of its
`BUNDLE.json`, and sets `STUDIO_LIB` to its path for the checker.

```sh
python3 evals/studio/pack_lib.py /absolute/new-bundle-directory
```

The bundle is flat: the rule modules (`studio_lib.py`, `audio_rules.py`, `music_rules.py`, `video_rules.py`, `proto_rules.py` and, once merged, `web_rules.py`), the node helpers
(`web_probe.mjs`, `net_trap.js`), and the manifest validator and schema beside the library (`studio_lib.py` looks there first). A `check.py` run as
`python3 /audit/answers/check.py /scratch /audit/answers/expected.json` finds the library through `STUDIO_LIB` alone.

## What the image must hold

| for | needed |
|---|---|
| art checkers | python3 with numpy, Pillow, fontTools |
| audio, music, video checkers | ffmpeg 7.0.2 with libx264, AAC, libvorbis, libopus, libmp3lame (the static build has them), also reachable as `ffmpeg` on PATH for the kept build scripts |
| title OCR (ASCII titles) | tesseract with the English model |
| prototype (Node) checkers | node 22 or later |
| phone items (7 to 11) | puppeteer-core in a fixed directory (`STUDIO_NODE_MODULES`), Chrome for Testing 150.0.7871.46 (the full chrome-linux64 build the runner recipe installs; the headless shell gives the same verdicts) (`STUDIO_CHROME`), the libraries it loads |

The checker libraries (numpy, Pillow, fontTools) must be importable system-wide in the image, not from a user site: the checker runs with a clean environment that has no `PYTHONPATH` and an empty `HOME`. `replay_local.py` passes `PYTHONPATH`, `PYTHONUSERBASE`, `LD_LIBRARY_PATH` and the `STUDIO_*` variables through, so it can run on a host whose packages are per-user; the lane must not.

The checker also needs a `TMPDIR` outside `/scratch` (the checkers copy the tree to run a kept script; they skip a temporary directory inside it, but a result tree should not carry
checker debris). The checker library is tested on Python 3.11 with numpy 1.24.2, the versions in the runner's 2026-10-10 image, as well as 3.12.

## Prove it before a model is called: the replay

`selfcheck.py` in each set can write every reference and defect tree it builds, with the verdict the host checker gave:

```sh
python3 evals/studio/game-art/build/selfcheck.py --emit /absolute/replay-dir      # all cases of the set, or add a case-id prefix first
```

For each case this writes `reference.tar`, `defect-NN.tar` (the output tree without `inputs/` and `.run/`, which the runner stages and writes itself) and `replay.json`: for each tree the
transcript turns, the relay requests (the hosts the case's proxy log shows) and the expected verdict per rule id.

A runner replay mode should: stage the case as for a real run, extract the tar into `/scratch` as the agent's user, write the transcript and proxy log from `replay.json` through its
normal capture path, run the real checker, and require the verdict to equal `expect`, for every tree. `replay_local.py` does the same thing without a container, to check the bundle,
the environment and the file formats:

```sh
python3 evals/studio/replay_local.py /absolute/replay-dir /absolute/new-bundle-directory evals/studio/game-art/cases
```

A passing replay in the lane for one case per skill set, with the lane's verdicts equal to the host's, is the bar for calling the lane ready for a model.
