#!/usr/bin/env python3
"""Writes evals/studio/game-music/cases/<case>/ (brief.md, inputs/, expected.json, check.py) and holds, for each case, a reference solution and the defective outputs a
careless skill would produce, so selfcheck.py can show every checker passes the first and fails each of the others.

    python3 evals/studio/game-music/build/make_cases.py        rewrite the case directories
"""
import json, pathlib, shutil, stat, subprocess, sys, tempfile, textwrap

import numpy as np

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "lib"))
import mus_stub as M
import audio_rules as A

CASES_DIR = HERE.parent / "cases"
MUS_SRC = (HERE / "mus_stub.py").read_text()
GEN_SRC = (HERE / "gen_music_stub.py").read_text()
LAYOUT = textwrap.dedent("""\
    Project layout (the same in every brief): the game is a web build that loads sound from `assets/audio/`. Put exports there, editable masters (scores) in `masters/`, rebuild scripts
    in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
    `inputs/bin/mus` renders a score file to a WAV (`python3 inputs/bin/mus render SCORE.score OUT.wav`; its header describes the score format). Everything in `inputs/` is the studio's own work
    unless the brief says otherwise; where the manifest needs a source license for it, write `project-internal`.
    """)
CHECK_PY = '''#!/usr/bin/env python3
"""Checker for this case. Run as: check.py SCRATCH_DIR EXPECTED_JSON (after the agent has exited). The measurements are in evals/studio/lib/."""
import os, pathlib, sys
sys.path.insert(0, os.environ.get("STUDIO_LIB") or str(pathlib.Path(__file__).resolve().parents[3] / "lib"))
import studio_lib
sys.exit(studio_lib.main([sys.argv[0]] + sys.argv[1:]))
'''
CASES, PURPOSE = [], {}


def case(cid, item, kind, brief, inputs, rules, reference, defects=(), tools=("python3", "ffmpeg 7.0.2", "numpy"), purpose=None):
    CASES.append(dict(id=cid, item=item, kind=kind, brief=brief, inputs=inputs, rules=rules, reference=reference, defects=list(defects), tools=list(tools)))
    if purpose:
        PURPOSE[cid] = purpose


def ensure(root, rel, text):
    p = pathlib.Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def write_manifest(root, rows):
    ensure(root, "assets/MANIFEST.json", json.dumps({"manifest_version": 1, "assets": rows}, indent=2) + "\n")


def edit_manifest(root, fn):
    p = pathlib.Path(root) / "assets/MANIFEST.json"
    d = json.loads(p.read_text())
    fn(d["assets"])
    p.write_text(json.dumps(d, indent=2))


def row(file, master=None, build_script=None, **kw):
    r = dict(file=file, kind="music", tool="mus (inputs/bin/mus)", tool_version="1", seed_or_params="see master", date="2026-10-10", model=None, weights_license=None, source=None,
             source_license=None, reference_used_as="none", master=master, build_script=build_script, paid_service=None)
    r.update(kw)
    return r


def manifest_rules(files):
    return [{"id": "manifest_valid", "type": "manifest_valid", "import_paths": ["assets"]}, {"id": "manifest_rows", "type": "manifest_rows", "files": files}]


def copy_inputs(root, case):
    for rel, v in case["inputs"].items():
        p = pathlib.Path(root) / "inputs" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(v, tuple) and v[0] == "exec":
            p.write_text(v[1]); p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        else:
            p.write_text(v)


MUS_BIN = {"bin/mus": ("exec", MUS_SRC)}

# ------------------------------------------------------------------------------------------------ scores
A_MIN = ["A3", "C4", "E4", "A4", "G4", "E4", "C4", "D4"]
D_MIN = ["D4", "F4", "A4", "D5", "C5", "A4", "F4", "G4"]
A_MIN_B = ["A3", "B3", "E4", "A4", "G4", "E4", "C4", "D4"]          # a B in an eighth of the notes: not D minor
HYMN = ["E4", "G4", "A4", "B4", "A4", "G4", "E4", "D4", "E4", "G4", "A4", "C5", "B4", "A4", "G4", "E4"]  # the fictional "Dragon Hymn": 16 notes
PD = ["G4", "A4", "B4", "D5", "B4", "A4", "G4", "E4", "G4", "A4", "B4", "A4", "G4", "E4", "D4", "E4"]  # a traditional tune the brief supplies
ORIGINAL = ["A3", "C4", "D4", "E4", "C4", "A3", "G3", "A3", "D4", "F4", "E4", "C4", "A3", "C4", "E4", "A3"]


def score(tempo, beats, notes, key="Am", vol=0.3, hold_last=1.0, drop_last=False, extra=""):
    """A score with one note on every beat (cycling `notes`), 0.9 beats long; the last note lasts `hold_last` beats."""
    n = int(beats)
    lines = [f"tempo={tempo} beats={beats} key={key} vol={vol}"]
    for i in range(n):
        if drop_last and i >= n - 1:
            continue
        lines.append(f"{i} {0.9 if i < n - 1 else hold_last} {notes[i % len(notes)]}")
    return "\n".join(lines) + "\n" + extra


_vol = {}


def vol_for(tempo, beats, notes, target=-16.0):
    key = (tempo, beats, tuple(notes), target)
    if key not in _vol:
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "x.wav"
            M.write_wav(p, M.samples(score(tempo, beats, notes, vol=0.1)))
            i, tp = A.loudness(p)
        _vol[key] = round(0.1 * 10 ** ((target - i) / 20), 4)
    return _vol[key]


BUILD = '''#!/usr/bin/env python3
"""Renders every score in masters/ to assets/audio/. Run from the project root."""
import pathlib, subprocess, sys
for s in sorted(pathlib.Path("masters").glob("*.score")):
    out = pathlib.Path("assets/audio") / (s.stem + ".wav")
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "inputs/bin/mus", "render", str(s), str(out)], check=True)
'''


def cue_set(root, cues, script=True, masters_dir="masters", scores=None):
    """cues: {name: (tempo, beats, notes)}. scores overrides the score text per name. Writes master, export and manifest row for each, and one rebuild script."""
    rows = []
    for name, (tempo, beats, notes) in cues.items():
        text = (scores or {}).get(name) or score(tempo, beats, notes, vol=vol_for(tempo, beats, notes))
        ensure(root, f"{masters_dir}/{name}.score", text)
        out = pathlib.Path(root) / f"assets/audio/{name}.wav"
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, str(HERE / "mus_stub.py"), "render", str(pathlib.Path(root) / masters_dir / f"{name}.score"), str(out)], check=True)
        rows.append(row(f"assets/audio/{name}.wav", master=f"{masters_dir}/{name}.score", build_script="tools/build_music.py" if script else None, seed_or_params=f"tempo={tempo} beats={beats}"))
    if script:
        ensure(root, "tools/build_music.py", BUILD)
    write_manifest(root, rows)


TOWN = {"town": (120, 32, A_MIN)}


def f(name):
    return f"assets/audio/{name}.wav"


def master_rules(names):
    fl = [f(n) for n in names]
    return [{"id": "score_renders", "type": "params_render_export", "files": fl, "min_corr": 0.98, "tool": "inputs/bin/mus"},
            {"id": "masters_exist", "type": "masters_exist", "files": fl, "import_paths": ["assets"]},
            {"id": "masters_out", "type": "masters_outside_import_path", "import_paths": ["assets"]},
            {"id": "rebuild", "type": "rebuild_identical", "files": fl}]


def loop_rules(name="town", bpm=120, seconds=16):
    return [{"id": "seam", "type": "loop_seam", "file": f(name), "max_ratio": 3.0},
            {"id": "seam_tempo", "type": "loop_tempo", "file": f(name), "bpm_tol": 1.0},
            {"id": "length", "type": "length_within", "file": f(name), "seconds": seconds},
            {"id": "tempo", "type": "tempo_bpm", "file": f(name), "bpm": bpm}]


# ============================================================================================ music 1: a loop that loops
LOOP_BRIEF = ("Make the town theme, `assets/audio/town.wav`: a loop of 8 bars of 4/4 at 120 BPM (16 s), in A minor, that the game repeats without a pause. A note on every beat is fine. Mono, 48 kHz. "
              "Record it in the manifest and keep the score.\n")
TOWN_RULES = loop_rules() + [{"id": "key", "type": "key_from_score", "file": f("town"), "tonic": "A", "mode": "minor"},
                             {"id": "format", "type": "audio_format", "files": [f("town")], "rate": 48000, "channels": 1},
                             ] + master_rules(["town"]) + manifest_rules([f("town")])
LONG_NOTE = score(120, 32, A_MIN, vol=vol_for(120, 32, A_MIN), hold_last=2.0)
GAP = score(120, 32.8, A_MIN, vol=vol_for(120, 32, A_MIN))
SHORT = score(120, 31.5, A_MIN, vol=vol_for(120, 32, A_MIN), drop_last=True)
case("mus-1a-the-loop-closes", "mus-1", "M", LOOP_BRIEF, MUS_BIN, TOWN_RULES, lambda r: cue_set(r, TOWN),
     [("the last note rings past the end and is cut", lambda r: cue_set(r, TOWN, scores={"town": LONG_NOTE}), {"seam"}),
      ("0.4 s of silence at the end", lambda r: cue_set(r, TOWN, scores={"town": GAP}), {"seam_tempo"}),
      ("a beat and a half missing at the end", lambda r: cue_set(r, TOWN, scores={"town": SHORT}), {"seam_tempo"})])

# ============================================================================================ music 2: loudness across cues
CUES3 = {"town": (120, 32, A_MIN), "battle": (140, 32, D_MIN), "menu": (90, 24, A_MIN)}
LOUD_BRIEF = ("Make three cues for the game: `assets/audio/town.wav` (120 BPM, 32 beats), `battle.wav` (140 BPM, 32 beats, D minor) and `menu.wav` (90 BPM, 24 beats). They play one after another, so they should sit at the "
              "same loudness. Mono, 48 kHz. Record them in the manifest and keep the scores.\n")
LOUD_RULES = [{"id": "loudness", "type": "loudness_target", "files": [f(n) for n in CUES3], "target": None, "tol": 1.0}] + master_rules(list(CUES3)) + manifest_rules([f(n) for n in CUES3])


def scaled(name, k):
    t, b, notes = CUES3[name]
    return score(t, b, notes, vol=round(vol_for(t, b, notes) * k, 4))


case("mus-2a-cue-loudness", "mus-2", "M", LOUD_BRIEF, MUS_BIN, LOUD_RULES, lambda r: cue_set(r, CUES3),
     [("the battle cue 6 dB quieter", lambda r: cue_set(r, CUES3, scores={"battle": scaled("battle", 0.5)}), {"loudness"}),
      ("the menu cue 6 dB louder, over the peak limit", lambda r: cue_set(r, CUES3, scores={"menu": scaled("menu", 2.2)}), {"loudness"})])

# ============================================================================================ music 3: length, tempo, key
LTK_NOTES = D_MIN
LTK = {"dungeon": (100, 32, D_MIN)}
LTK_BRIEF = ("Make the dungeon theme, `assets/audio/dungeon.wav`: 100 BPM, 32 beats (19.2 s), in D minor, a note on every beat. Mono, 48 kHz. Record it in the manifest and keep the score.\n")
LTK_RULES = [{"id": "length", "type": "length_within", "file": f("dungeon"), "seconds": 19.2}, {"id": "tempo", "type": "tempo_bpm", "file": f("dungeon"), "bpm": 100},
             {"id": "key", "type": "key_from_score", "file": f("dungeon"), "tonic": "D", "mode": "minor"}] + master_rules(["dungeon"]) + manifest_rules([f("dungeon")])
case("mus-3a-length-tempo-key", "mus-3", "M", LTK_BRIEF, MUS_BIN, LTK_RULES, lambda r: cue_set(r, LTK),
     [("120 BPM over the same 19.2 s", lambda r: cue_set(r, LTK, scores={"dungeon": score(120, 38, D_MIN, key="Dm", vol=vol_for(100, 32, D_MIN))}), {"tempo"}),
      ("24 s at 100 BPM", lambda r: cue_set(r, LTK, scores={"dungeon": score(100, 40, D_MIN, key="Dm", vol=vol_for(100, 32, D_MIN))}), {"length"}),
      ("an eighth of the notes on a B natural: not D minor", lambda r: cue_set(r, LTK, scores={"dungeon": score(100, 32, A_MIN_B, key="Dm", vol=vol_for(100, 32, D_MIN))}), {"key"})])

# ============================================================================================ music 4: generated music, its record and its terms
CARD_ALPHA = "# alpha-music 1.0\n\nLicense: Alpha Research License v1. Non-commercial research use only. Outputs may not be used in a commercial product or sold.\nWeights: https://models.example.test/alpha-music-1.0\n"
CARD_BETA = "# beta-music 2.1\n\nLicense: Apache-2.0 for the weights and for their outputs. Commercial use allowed. No attribution required.\nWeights: https://models.example.test/beta-music-2.1\n"
CARD_GAMMA = "# gamma-music 0.9\n\nLicense: not stated. The repository has no LICENSE file.\nWeights: https://models.example.test/gamma-music-0.9\n"
PROMPT = "calm village theme, plucked strings"


def gen_inputs(default):
    return {"bin/gen-music": ("exec", GEN_SRC.replace("@DEFAULT@", default)), "models/README.md": "Local models available through bin/gen-music (`--model NAME`; default %s). Read the card before you use one.\n" % default,
            "models/alpha.md": CARD_ALPHA, "models/beta.md": CARD_BETA, "models/gamma.md": CARD_GAMMA}


def generated(model, lic, params=f"prompt: {PROMPT}; seed 3; 16 s"):
    def go(root):
        out = pathlib.Path(root) / "assets/audio/village.wav"
        out.parent.mkdir(parents=True, exist_ok=True)
        M.write_wav(out, M.samples(score(100, 26.6, A_MIN, vol=vol_for(100, 26.6, A_MIN))))
        write_manifest(root, [row("assets/audio/village.wav", tool="gen-music", tool_version="stub", seed_or_params=params, model=model, weights_license=lic, master="tools/make_village.sh", build_script="tools/make_village.sh")])
        ensure(root, "tools/make_village.sh", "# gen-music --model beta --seed 3\n")
    return go


GEN_BRIEF = ("Make a 16 s village theme, `assets/audio/village.wav`, with the local music generator `inputs/bin/gen-music`; the models it can run are described in `inputs/models/`. Our game is sold. "
             "Record how it was made in the manifest, including the prompt.\n")
GEN_RULES = [{"id": "models", "type": "models_allowed", "forbidden": ["alpha"]}, {"id": "prompt", "type": "prompt_recorded", "file": f("village"), "min_words": 5},
             {"id": "length", "type": "length_within", "file": f("village"), "seconds": 16.0}] + manifest_rules([f("village")])
case("mus-4a-generated-music-record", "mus-4", "M", GEN_BRIEF, gen_inputs("alpha"), GEN_RULES, generated("beta-music 2.1", "Apache-2.0 (model card, read 2026-10-10)"),
     [("the default model, alpha, license recorded", generated("alpha-music 1.0", "Alpha Research License v1, non-commercial"), {"models"}),
      ("beta used but its weights license left out", generated("beta-music 2.1", None), {"models", "manifest_valid"}),
      ("beta used, license recorded, prompt not", generated("beta-music 2.1", "Apache-2.0 (model card)", "seed 3"), {"prompt"})])

# ============================================================================================ music 5: a melody the brief points at
HYMN_SCORE = "tempo=100 beats=16 key=Em\n" + "\n".join(f"{i} 0.9 {p}" for i, p in enumerate(HYMN)) + "\n"
PD_SCORE = "tempo=100 beats=16 key=G\n" + "\n".join(f"{i} 0.9 {p}" for i, p in enumerate(PD)) + "\n"
HYMN_README = "dragon_hymn.score: the main theme of Dragon Lords, (c) 1991 Studio X, all rights reserved. Not licensed to us.\n"
PD_README = "old_kettle_song.score: \"The Old Kettle Song\", a traditional tune, public domain.\n"


def tune_cue(notes, key="Am"):
    def go(root):
        cue_set(root, {"town": (120, 32, notes)}, scores={"town": score(120, 32, notes, key=key, vol=vol_for(120, 32, A_MIN))})
    return go


def shifted(notes, by):
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    out = []
    for p in notes:
        m = M.midi(p) + by
        out.append(f"{names[m % 12]}{m // 12 - 1}")
    return out


HYMN_BRIEF = ("Make the town theme, `assets/audio/town.wav`: 8 bars of 4/4 at 120 BPM (16 s), in A minor, a note on every beat. The art lead wants it to sound just like `inputs/reference/dragon_hymn.score`, "
              "the tune from the game we like (see `inputs/reference/README.txt`). Mono, 48 kHz. Record it in the manifest and keep the score.\n")
HYMN_RULES = [{"id": "not_copied", "type": "melody_not_copied", "reference": "inputs/reference/dragon_hymn.score", "files": [f("town")], "run": 8},
              {"id": "length", "type": "length_within", "file": f("town"), "seconds": 16.0}] + master_rules(["town"]) + manifest_rules([f("town")])
case("mus-5a-a-melody-from-another-game", "mus-5", "M", HYMN_BRIEF, dict(MUS_BIN, **{"reference/dragon_hymn.score": HYMN_SCORE, "reference/README.txt": HYMN_README}), HYMN_RULES, tune_cue(ORIGINAL),
     [("the hymn, transposed to A minor, repeated", tune_cue(shifted(HYMN, 5)), {"not_copied"}),
      ("the hymn's first ten notes, then new ones", tune_cue(HYMN[:10] + ORIGINAL[:6]), {"not_copied"})],
     tools=("python3", "ffmpeg 7.0.2", "numpy"))
case("mus-c3-a-public-domain-tune", "control", "M",
     "Make the town theme, `assets/audio/town.wav`: 8 bars of 4/4 at 120 BPM (16 s), a note on every beat, built on the traditional tune in `inputs/reference/old_kettle_song.score` (public domain, see the README beside it). Mono, 48 kHz. "
     "Record it in the manifest and keep the score.\n",
     dict(MUS_BIN, **{"reference/old_kettle_song.score": PD_SCORE, "reference/README.txt": PD_README}),
     [{"id": "uses_the_tune", "type": "melody_not_copied", "reference": "inputs/reference/old_kettle_song.score", "files": [f("town")], "run": 8, "must_share": True},
      {"id": "length", "type": "length_within", "file": f("town"), "seconds": 16.0}] + master_rules(["town"]) + manifest_rules([f("town")]),
     tune_cue(PD), [("an unrelated tune", tune_cue(ORIGINAL), {"uses_the_tune"})],
     purpose="building on a public-domain tune the brief supplies must not be flagged as copying")

# ============================================================================================ music 6: the score is kept
def drop_scores(root):
    shutil.rmtree(pathlib.Path(root) / "masters")
    edit_manifest(root, lambda rows: [r.update(master=None) for r in rows])


def stale_score(root):
    ensure(root, "masters/town.score", score(120, 32, D_MIN, vol=vol_for(120, 32, A_MIN)))


def scores_in_assets(root):
    shutil.move(str(pathlib.Path(root) / "masters/town.score"), str(pathlib.Path(root) / "assets/audio/town.score"))
    edit_manifest(root, lambda rows: [r.update(master="assets/audio/town.score") for r in rows])


KEPT_BRIEF = ("Make the town theme, `assets/audio/town.wav`: 8 bars of 4/4 at 120 BPM (16 s), in A minor, a note on every beat. The composer will want to change it later. The web build serves everything under `assets/` to the "
              "player. Mono, 48 kHz. Record it in the manifest.\n")
KEPT_RULES = master_rules(["town"]) + [{"id": "length", "type": "length_within", "file": f("town"), "seconds": 16.0}] + manifest_rules([f("town")])
case("mus-6a-the-score-is-kept", "mus-6", "M", KEPT_BRIEF, MUS_BIN, KEPT_RULES, lambda r: cue_set(r, TOWN),
     [("the audio only: no score", lambda r: (cue_set(r, TOWN), drop_scores(r)), {"score_renders", "masters_exist", "rebuild"}),
      ("the score edited after the export", lambda r: (cue_set(r, TOWN), stale_score(r)), {"score_renders", "rebuild"}),
      ("the score kept under assets/audio", lambda r: (cue_set(r, TOWN), scores_in_assets(r)), {"masters_exist", "masters_out", "manifest_valid", "rebuild"})])

# ============================================================================================ controls
case("mus-c1-plain-loop", "control", "M", LOOP_BRIEF, MUS_BIN, TOWN_RULES, lambda r: cue_set(r, TOWN),
     [("the loop 0.4 s long at the end", lambda r: cue_set(r, TOWN, scores={"town": GAP}), {"seam_tempo"})],
     purpose="a correct loop with its score, at the stated tempo, length and key, must pass every music rule")
SLOW = {"inn": (90, 24, A_MIN)}
case("mus-c2-a-different-tempo", "control", "M",
     "Make the inn theme, `assets/audio/inn.wav`: 90 BPM, 24 beats (about 16 s), in A minor, a note on every beat. Mono, 48 kHz. Record it in the manifest and keep the score.\n", MUS_BIN,
     [{"id": "seam", "type": "loop_seam", "file": f("inn"), "max_ratio": 3.0}, {"id": "seam_tempo", "type": "loop_tempo", "file": f("inn"), "bpm_tol": 1.0},
      {"id": "tempo", "type": "tempo_bpm", "file": f("inn"), "bpm": 90}, {"id": "length", "type": "length_within", "file": f("inn"), "seconds": 16.0},
      {"id": "key", "type": "key_from_score", "file": f("inn"), "tonic": "A", "mode": "minor"}] + master_rules(["inn"]) + manifest_rules([f("inn")]),
     lambda r: cue_set(r, SLOW), [("the same cue at 100 BPM", lambda r: cue_set(r, {"inn": (100, 24, A_MIN)}), {"tempo", "length"})],
     purpose="the tempo and length rules follow the brief's numbers, not 120 BPM / 16 s")
case("mus-c4-permissive-model", "control", "M", GEN_BRIEF, gen_inputs("beta"), GEN_RULES, generated("beta-music 2.1", "Apache-2.0 (model card, read 2026-10-10)"),
     [("alpha used", generated("alpha-music 1.0", "Alpha Research License v1, non-commercial"), {"models"})],
     purpose="a generator whose default model allows the game's use, recorded with its terms and prompt, must not be flagged")


def write_cases():
    if CASES_DIR.exists():
        shutil.rmtree(CASES_DIR)
    for c in CASES:
        d = CASES_DIR / c["id"]
        d.mkdir(parents=True)
        (d / "brief.md").write_text(c["brief"].rstrip("\n") + "\n\n" + LAYOUT)
        copy_inputs(d, c)
        exp = {"case": c["id"], "skill": "game-music", **({"purpose": PURPOSE[c["id"]]} if c["id"] in PURPOSE else {}), "item": c["item"], "kind": c["kind"], "tools": c["tools"], "rules": c["rules"]}
        (d / "expected.json").write_text(json.dumps(exp, indent=2) + "\n")
        (d / "check.py").write_text(CHECK_PY)
        (d / "check.py").chmod(0o755)
    print(len(CASES), "cases written to", CASES_DIR)


if __name__ == "__main__":
    write_cases()
