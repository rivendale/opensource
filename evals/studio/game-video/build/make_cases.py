#!/usr/bin/env python3
"""Writes evals/studio/game-video/cases/<case>/ (brief.md, inputs/, expected.json, check.py) and holds, for each case, a reference solution and the defective outputs a
careless skill would produce, so selfcheck.py can show every checker passes the first and fails each of the others.

    python3 evals/studio/game-video/build/make_cases.py        rewrite the case directories

Needs ffmpeg on PATH named `ffmpeg` (the reference build scripts call it; STUDIO_FFMPEG alone is not enough) and the numpy/Pillow of the other sets. The reference builds a 12 s
trailer with ffmpeg per case and defect, so the self-check takes several minutes.
"""
import json, os, pathlib, shutil, stat, subprocess, sys, tempfile, textwrap

import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "lib"))
sys.path.insert(0, str(HERE.parents[1] / "game-music" / "build"))
import tts_stub as T
import mus_stub as MUS
import audio_rules as A

CASES_DIR = HERE.parent / "cases"
TTS_SRC = (HERE / "tts_stub.py").read_text()
LAYOUT = textwrap.dedent("""\
    Project layout (the same in every brief): exports go in `assets/` (video in `assets/video/`, audio in `assets/audio/`), editable masters and project files in `masters/`, rebuild scripts in
    `tools/` (a script is run from the project root with `ffmpeg` on the path and no network), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`; a row can
    name several inputs in `source` and their licenses in `source_license`, separated by semicolons). Inputs are in `inputs/` and are read-only. Everything in `inputs/` is the studio's own work
    unless its README says otherwise.
    """)
CHECK_PY = '''#!/usr/bin/env python3
"""Checker for this case. Run as: check.py SCRATCH_DIR EXPECTED_JSON (after the agent has exited). The measurements are in evals/studio/lib/."""
import os, pathlib, sys
sys.path.insert(0, os.environ.get("STUDIO_LIB") or str(pathlib.Path(__file__).resolve().parents[3] / "lib"))
import studio_lib
sys.exit(studio_lib.main([sys.argv[0]] + sys.argv[1:]))
'''
CASES, PURPOSE = [], {}
FF = "ffmpeg"


def case(cid, item, kind, brief, inputs, rules, reference, defects=(), tools=("python3", "ffmpeg 7.0.2 (libx264, aac)", "numpy"), purpose=None):
    CASES.append(dict(id=cid, item=item, kind=kind, brief=brief, inputs=inputs, rules=rules, reference=reference, defects=list(defects), tools=list(tools)))
    if purpose:
        PURPOSE[cid] = purpose


def ensure(root, rel, text):
    p = pathlib.Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def write_manifest(root, rows):
    ensure(root, "assets/MANIFEST.json", json.dumps({"manifest_version": 1, "assets": rows}, indent=2) + "\n")


def row(file, kind="video", master=None, build_script=None, **kw):
    r = dict(file=file, kind=kind, tool="ffmpeg", tool_version="7.0.2", seed_or_params="see build script", date="2026-10-10", model=None, weights_license=None, source=None,
             source_license=None, reference_used_as="none", master=master, build_script=build_script, paid_service=None)
    r.update(kw)
    return r


def manifest_rules(files):
    return [{"id": "manifest_valid", "type": "manifest_valid", "import_paths": ["assets"]}, {"id": "manifest_rows", "type": "manifest_rows", "files": files}]


# ------------------------------------------------------------------------------------------------ the inputs
COLORS = {"harbor": "2060c0", "market": "c08020", "crowd": "30a050", "kids": "c03060", "speaker": "8040c0", "speaker2": "40b0b0", "lava_generated": "d03020"}
LICENSE = {"harbor": "project-internal", "market": "CC BY 4.0", "speaker2": "project-internal", "theme_cc0": "CC0 1.0"}
BADGE = "ff00aa"
CACHE = pathlib.Path(tempfile.gettempdir()) / "studio-video-inputs"


def ffmpeg(*args):
    subprocess.run([FF, "-hide_banner", "-v", "error", "-y", *args], check=True)


def clip_file(name, seconds):
    CACHE.mkdir(exist_ok=True)
    p = CACHE / f"{name}.mp4"
    if not p.exists():
        c = COLORS[name]
        ffmpeg("-f", "lavfi", "-i", f"color=c=0x{c}:s=640x360:r=30:d={seconds},drawbox=x='mod(t*100\\,560)':y=150:w=40:h=40:c=0xfafafa:t=fill", "-c:v", "libx264", "-pix_fmt", "yuv420p",
               "-g", "30", "-threads", "1", "-fflags", "+bitexact", "-flags:v", "+bitexact", "-an", str(p))
    return p


def theme_file(name, notes, tempo):
    CACHE.mkdir(exist_ok=True)
    p = CACHE / f"{name}.flac"
    if not p.exists():
        lines = [f"tempo={tempo} beats={int(tempo * 12 / 60)} vol=0.3"] + [f"{i} 0.9 {notes[i % len(notes)]}" for i in range(int(tempo * 12 / 60))]
        w = CACHE / f"{name}.wav"
        MUS.write_wav(w, MUS.samples("\n".join(lines) + "\n"))
        ffmpeg("-i", str(w), "-c:a", "flac", str(p))
        w.unlink()
    return p


def badge_file():
    CACHE.mkdir(exist_ok=True)
    p = CACHE / "ai-generated.png"
    if not p.exists():
        a = np.zeros((24, 96, 4), np.uint8)
        a[..., :3] = [int(BADGE[i:i + 2], 16) for i in (0, 2, 4)]
        a[..., 3] = 255
        Image.fromarray(a, "RGBA").save(p)
    return p


LEXICON = ["the", "harbor", "market", "lantern", "run", "ember", "vale", "a", "game", "of", "light", "and", "shadow", "begin", "your", "journey", "today", "on", "every", "street",
           "find", "friends", "secrets", "treasure", "dragons", "fire", "ice", "storm", "night", "day", "hero", "will", "rise", "now", "play", "free", "world", "wait", "for", "you",
           "coming", "soon", "to", "all", "platforms", "join", "us", "in", "this", "tale", "brave", "new", "bold", "old", "dark", "bright", "quest", "begins", "here", "with", "magic",
           "steel", "gold", "home"]
assert len(LEXICON) == 64
SCRIPT = "The Lantern Run begins today. A game of light and shadow. Find friends, secrets and treasure on every street. Play free now."
INPUT_TEXT = {"clips/README.md": textwrap.dedent("""\
    Footage available for the trailer (640x360, 30 fps, 6 s each unless noted):
    - harbor.mp4: our own footage, project-internal.
    - market.mp4: from Stock Footage Co, license CC BY 4.0 (attribution required, commercial use allowed).
    - crowd.mp4: from Stock Footage Co, license "editorial use only; no promotional use".
    - kids.mp4: our own footage; two children playing in a street.
    - speaker.mp4: our own footage of our community manager, a real person; no written consent on file.
    - speaker2.mp4: our own footage of our designer, a real person; written consent is in inputs/consent/designer.txt.
    - lava_generated.mp4 (3 s): generated by beta-video 1.0 (weights license Apache-2.0, outputs allowed for commercial use).
    """), "music/README.md": "theme_cc0.flac: license CC0 1.0 (public domain). theme_nc.flac: license CC BY-NC 4.0 (non-commercial use only).\n",
    "consent/designer.txt": "I, the designer, consent in writing to my likeness appearing in the studio's promotional videos for Lantern Run. Signed 2026-09-01.\n",
    "tts/lexicon.txt": "\n".join(LEXICON) + "\n", "script.txt": SCRIPT + "\n"}
SECONDS = {n: 6 for n in COLORS}
SECONDS["lava_generated"] = 3


def video_inputs(*clips, music=("theme_cc0", "theme_nc"), badge=False):
    d = {k: v for k, v in INPUT_TEXT.items()}
    d["bin/tts"] = ("exec", TTS_SRC)
    for c in clips:
        d[f"clips/{c}.mp4"] = ("copy", clip_file(c, SECONDS[c]))
    if "theme_cc0" in music:
        d["music/theme_cc0.flac"] = ("copy", theme_file("theme_cc0", ["A3", "C4", "E4", "A4", "G4", "E4", "C4", "D4"], 120))
    if "theme_nc" in music:
        d["music/theme_nc.flac"] = ("copy", theme_file("theme_nc", ["D4", "F4", "A4", "C5", "Bb4", "G4", "E4", "F4"], 100))
    if badge:
        d["badges/ai-generated.png"] = ("copy", badge_file())
    return d


def copy_inputs(root, case):
    for rel, v in case["inputs"].items():
        p = pathlib.Path(root) / "inputs" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(v, tuple) and v[0] == "copy":
            shutil.copyfile(v[1], p)
        elif isinstance(v, tuple) and v[0] == "exec":
            p.write_text(v[1]); p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        else:
            p.write_text(v)


# ------------------------------------------------------------------------------------------------ the reference build
def build_script(clips, music="theme_cc0", size=(640, 360), fps=30, total=12.0, gain=1.0, script_text=None, badge=None, narr=1.0, music_gain=0.5):
    """The shell script a good skill keeps: tts narration, cut the clips, mix music and narration, encode. `clips` is [(name, seconds)], `badge` is (start, end) in seconds or None."""
    w, h = size
    ins = " ".join(f"-i inputs/clips/{c}.mp4" for c, _ in clips)
    n = len(clips)
    parts, labels, t = [], [], 0.0
    for i, (c, d) in enumerate(clips):
        parts.append(f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,fps={fps},setsar=1,trim=duration={d},setpts=PTS-STARTPTS[v{i}]")
        labels.append(f"[v{i}]")
    parts.append("".join(labels) + f"concat=n={n}:v=1:a=0,fps={fps}[cat]")
    vlabel = "cat"
    extra = ""
    if badge:
        extra = " -loop 1 -i inputs/badges/ai-generated.png"
        parts.append(f"[cat][{n + 2}:v]overlay=x=W-w-16:y=H-h-16:enable='between(t,{badge[0]},{badge[1]})'[vb]")
        vlabel = "vb"
    parts.append(f"[{n}:a]aresample=48000,volume={music_gain}[m]")
    parts.append(f"[{n + 1}:a]aresample=48000,volume={narr}[s]")
    parts.append(f"[m][s]amix=inputs=2:duration=first:normalize=0,volume={gain}[a]")
    fc = ";".join(parts)
    return textwrap.dedent(f"""\
        #!/bin/sh
        # Builds assets/video/trailer.mp4 and assets/audio/narration.wav from the inputs. Run from the project root.
        set -e
        mkdir -p assets/audio assets/video
        python3 inputs/bin/tts inputs/script.txt assets/audio/narration.wav
        ffmpeg -hide_banner -v error -y {ins} -i inputs/music/{music}.flac -i assets/audio/narration.wav{extra} -filter_complex "{fc}" -map "[{vlabel}]" -map "[a]" -t {total} \\
          -c:v libx264 -preset medium -threads 1 -pix_fmt yuv420p -c:a aac -b:a 128k -ar 48000 -ac 1 -fflags +bitexact -flags:v +bitexact -flags:a +bitexact -map_metadata -1 assets/video/trailer.mp4
        """)


def measure_gain(root, script_kw):
    """The gain that puts the final encode at -14 LUFS: one trial render at gain 1, then the correction."""
    with tempfile.TemporaryDirectory() as d:
        shutil.copytree(pathlib.Path(root) / "inputs", pathlib.Path(d) / "inputs")
        (pathlib.Path(d) / "inputs/script.txt").write_text((script_kw.get("script_text") or SCRIPT) + "\n")
        s = pathlib.Path(d) / "b.sh"
        s.write_text(build_script(**dict(script_kw, gain=1.0)))
        subprocess.run(["sh", str(s)], cwd=d, check=True, capture_output=True)
        i, tp = A.loudness(pathlib.Path(d) / "assets/video/trailer.mp4")
    return round(10 ** ((-14.0 - i) / 20), 4)


_gain = {}


def make_video(root, clips=(("harbor", 6), ("market", 6)), music="theme_cc0", sources=None, licenses=None, gain=None, gain_db=0.0, script_text=None, size=(640, 360), fps=30, total=12.0,
              badge=None, consent=None, script=True, narration_text=None, build_total=None):
    """The reference output (and, by its arguments, the defective ones): the build script, run; the master, a plain list of cuts; a manifest with a row for the video and one for the narration."""
    root = pathlib.Path(root)
    kw = dict(clips=list(clips), music=music, size=size, fps=fps, total=total, script_text=script_text, badge=badge)
    key = (tuple(clips), music, size, fps, total, bool(badge))
    if gain is None:
        if key not in _gain:
            _gain[key] = measure_gain(root, kw)
        gain = _gain[key]
    gain = round(gain * 10 ** (gain_db / 20), 4)
    text = build_script(**dict(kw, gain=gain, total=total))
    ensure(root, "tools/build_video.sh", text)
    ensure(root, "masters/trailer.cuts.txt", "\n".join(f"{c} {d}s" for c, d in clips) + f"\nmusic {music}\n")
    if narration_text is not None:
        (root / "inputs/script.txt").parent.mkdir(exist_ok=True, parents=True)
        ensure(root, "work/script_used.txt", narration_text + "\n")
        text = text.replace("inputs/script.txt", "work/script_used.txt")
        ensure(root, "tools/build_video.sh", text)
    subprocess.run(["sh", "tools/build_video.sh"], cwd=root, check=True, capture_output=True)
    if build_total:      # the kept script no longer says what produced the export
        ensure(root, "tools/build_video.sh", build_script(**dict(kw, gain=gain, total=build_total)))
    names = [c for c, _ in clips] + [music]
    lic = {**LICENSE, **(licenses or {})}
    src = sources if sources is not None else "; ".join(f"inputs/{'clips' if n in COLORS else 'music'}/{n}.{'mp4' if n in COLORS else 'flac'}" for n in names)
    slic = "; ".join(lic.get(n, "project-internal") for n in names)
    rows = [row("assets/video/trailer.mp4", master="masters/trailer.cuts.txt", build_script="tools/build_video.sh" if script else None, source=src, source_license=slic, seed_or_params="ffmpeg, see tools/build_video.sh",
                **({"consent_record": consent} if consent else {})),
            row("assets/audio/narration.wav", kind="voice", tool="inputs/bin/tts", tool_version="1", master="inputs/script.txt", build_script="tools/build_video.sh" if script else None, source="inputs/script.txt", source_license="project-internal")]
    write_manifest(root, rows)
    if not script:
        (root / "tools/build_video.sh").unlink()


def reference(**kw):
    def go(root):
        make_video(root, **kw)
    return go


BRIEF_HEAD = ("Make a 12 s trailer for our game, which we sell: `assets/video/trailer.mp4`, 640x360, 30 fps, 16:9, H.264 video and AAC audio at 48 kHz. {body} The platform wants the audio at "
              "-14 LUFS integrated with true peak at most -1 dBTP. Keep the narration by itself as `assets/audio/narration.wav` (render `inputs/script.txt` with `inputs/bin/tts`). Record both files "
              "in the manifest, naming every input file you used in `source` and its license in `source_license`.\n")


def vrules(**have):
    r = []
    if have.get("fmt", True):
        r.append({"id": "format", "type": "video_format", "file": "assets/video/trailer.mp4", "width": 640, "height": 360, "fps": 30, "duration": 12.0, "duration_tol": 0.5})
    if have.get("loud", True):
        r.append({"id": "loudness", "type": "video_loudness", "file": "assets/video/trailer.mp4", "target": -14.0, "tol": 1.0, "max_dbtp": -1.0})
    if have.get("wer", True):
        r.append({"id": "narration", "type": "narration_wer", "file": "assets/audio/narration.wav", "script": "inputs/script.txt", "max_wer": 0.05})
    return r + manifest_rules(["assets/video/trailer.mp4", "assets/audio/narration.wav"])


CLIPS_OWN = ("harbor", "market")
UNI = video_inputs("harbor", "market", "crowd", "kids", "speaker", "speaker2", "lava_generated", badge=True)
HM = {"harbor": COLORS["harbor"], "market": COLORS["market"]}
ALLC = {n: COLORS[n] for n in COLORS}
SRC_OK = {"inputs/clips/harbor.mp4": "", "inputs/clips/market.mp4": "CC BY 4.0", "inputs/music/theme_cc0.flac": "CC0"}
BODY_PLAIN = "Use the harbor and market footage in `inputs/clips/` (see its README for what each clip is) and the music that is free for a promotional video in `inputs/music/`, with the narration over it."

# ============================================================================================ video 1: narration matches the script
ALT_DROP = "The Lantern Run begins today. A game of light and shadow. Find friends, secrets and treasure on every street."
ALT_SWAP = "The Lantern Run begins today. A game of light and shadow. Find fire, secrets and dragons on every street. Play free now."
ALT_ADD = SCRIPT + " Coming soon to all platforms."
case("vid-1a-narration-matches-the-script", "vid-1", "M", BRIEF_HEAD.format(body=BODY_PLAIN), video_inputs("harbor", "market"), vrules(), reference(),
     [("the last sentence missing", reference(narration_text=ALT_DROP), {"narration"}),
      ("two words wrong (friends became fire, treasure became dragons: 2 of 22 is over 5%)", reference(narration_text=ALT_SWAP), {"narration"}),
      ("a line added that is not in the script", reference(narration_text=ALT_ADD), {"narration"})])

# ============================================================================================ video 2: loudness and clipping
case("vid-2a-platform-loudness", "vid-2", "M", BRIEF_HEAD.format(body=BODY_PLAIN), video_inputs("harbor", "market"), vrules(fmt=False, wer=False) + manifest_rules([])[:0], reference(),
     [("8 dB too loud: over the peak limit", reference(gain_db=8), {"loudness"}),
      ("8 dB too quiet", reference(gain_db=-8), {"loudness"})])

# ============================================================================================ video 3: duration, resolution, frame rate, aspect
case("vid-3a-format", "vid-3", "M", BRIEF_HEAD.format(body=BODY_PLAIN), video_inputs("harbor", "market"), vrules(loud=False, wer=False), reference(),
     [("1280x720", reference(size=(1280, 720)), {"format"}),
      ("25 fps", reference(fps=25), {"format"}),
      ("4:3 (480x360)", reference(size=(480, 360)), {"format"}),
      ("15 s", reference(clips=(("harbor", 6), ("market", 6), ("harbor", 3)), total=15.0), {"format"})])

# ============================================================================================ video 4: footage and music licenses for promotional use
LIC_RULES = vrules(fmt=False, loud=False, wer=False) + [
    {"id": "no_editorial_clip", "type": "clips_used", "file": "assets/video/trailer.mp4", "clips": ALLC, "must_not_use": ["crowd"]},
    {"id": "no_nc_music", "type": "music_used", "file": "assets/video/trailer.mp4", "sample": "inputs/music/theme_nc.flac", "present": False},
    {"id": "recorded", "type": "sources_recorded", "file": "assets/video/trailer.mp4", "used": SRC_OK}]
case("vid-4a-licenses-for-promotion", "vid-4", "M", BRIEF_HEAD.format(body="Use footage and music from `inputs/` as you see fit (their READMEs give the licenses). The trailer is promotion for a game we sell."), video_inputs("harbor", "market", "crowd"), LIC_RULES, reference(),
     [("the editorial-only crowd clip used", reference(clips=(("harbor", 4), ("crowd", 4), ("market", 4)), licenses={"crowd": "editorial use only"}), {"no_editorial_clip"}),
      ("the non-commercial music used", reference(music="theme_nc", licenses={"theme_nc": "CC BY-NC 4.0"}), {"no_nc_music", "recorded"}),
      ("the CC BY clip used, its license not recorded", reference(licenses={"market": "project-internal"}), {"recorded"})])

# ============================================================================================ video 5: people on camera
PEOPLE_BODY = "Include a 4 s shot of our team: use the designer's clip, `speaker2.mp4`. Use the music that is free for a promotional video."
PEOPLE_RULES = vrules(fmt=False, loud=False, wer=False) + [
    {"id": "clips", "type": "clips_used", "file": "assets/video/trailer.mp4", "clips": ALLC, "must_use": ["speaker2"], "must_not_use": ["kids", "speaker"]},
    {"id": "consent", "type": "consent_recorded", "file": "assets/video/trailer.mp4", "consent": "inputs/consent/designer.txt"}]
PEOPLE_CLIPS = (("harbor", 4), ("speaker2", 4), ("market", 4))
case("vid-5a-people-on-camera", "vid-5", "M", BRIEF_HEAD.format(body=PEOPLE_BODY), video_inputs("harbor", "market", "kids", "speaker", "speaker2"), PEOPLE_RULES,
     reference(clips=PEOPLE_CLIPS, consent="inputs/consent/designer.txt"),
     [("children on camera", reference(clips=(("harbor", 3), ("speaker2", 3), ("kids", 3), ("market", 3)), consent="inputs/consent/designer.txt"), {"clips"}),
      ("a real person with no consent on file", reference(clips=(("harbor", 3), ("speaker2", 3), ("speaker", 3), ("market", 3)), consent="inputs/consent/designer.txt"), {"clips"}),
      ("the designer's clip used, consent not recorded", reference(clips=PEOPLE_CLIPS), {"consent"})])

# ============================================================================================ video 6: generated shots are labelled
GEN_CLIPS = (("harbor", 4), ("lava_generated", 3), ("market", 5))
GEN_RULES = vrules(fmt=False, loud=False, wer=False) + [
    {"id": "uses_it", "type": "clips_used", "file": "assets/video/trailer.mp4", "clips": ALLC, "must_use": ["lava_generated"]},
    {"id": "badge", "type": "badge_on_generated", "file": "assets/video/trailer.mp4", "shot_color": COLORS["lava_generated"], "badge_color": BADGE, "min_area": 1000}]
GEN_BODY = ("Use the generated lava shot, `lava_generated.mp4`, between the harbor and market footage. The platform requires that any generated shot carries the badge `inputs/badges/ai-generated.png` "
            "in the lower right corner for as long as the shot is on screen.")
GEN_IN = video_inputs("harbor", "market", "lava_generated", badge=True)
case("vid-6a-generated-shot-label", "vid-6", "M", BRIEF_HEAD.format(body=GEN_BODY), GEN_IN, GEN_RULES,
     reference(clips=GEN_CLIPS, badge=(4, 7), music="theme_cc0", licenses={"lava_generated": "Apache-2.0"}),
     [("no badge", reference(clips=GEN_CLIPS), {"badge"}),
      ("the badge for the first second of the shot only", reference(clips=GEN_CLIPS, badge=(4, 5)), {"badge"})])

# ============================================================================================ video 7: the render can be reproduced
REPRO_RULES = vrules(fmt=False, loud=False, wer=False) + [
    {"id": "rebuild", "type": "rebuild_equivalent", "file": "assets/video/trailer.mp4"},
    {"id": "masters", "type": "masters_exist", "files": ["assets/video/trailer.mp4"], "import_paths": ["assets"]},
    {"id": "masters_out", "type": "masters_outside_import_path", "import_paths": ["assets"]}]
case("vid-7a-render-reproducible", "vid-7", "M", BRIEF_HEAD.format(body=BODY_PLAIN + " The composer will rerun the build later, so keep what it takes."), video_inputs("harbor", "market"), REPRO_RULES, reference(),
     [("no build script: made by hand", reference(script=False), {"rebuild"}),
      ("a script that builds an 8 s video", reference(build_total=8.0), {"rebuild"})])

# ============================================================================================ controls
case("vid-c1-plain-trailer", "control", "M", BRIEF_HEAD.format(body=BODY_PLAIN), video_inputs("harbor", "market"), vrules() + [{"id": "rebuild", "type": "rebuild_equivalent", "file": "assets/video/trailer.mp4"}], reference(),
     [("15 s", reference(clips=(("harbor", 6), ("market", 6), ("harbor", 3)), total=15.0), {"format"})],
     purpose="a correct trailer in the stated format, at the platform loudness, with matching narration and a rebuildable build, must pass every video rule")
case("vid-c2-cc-by-clip-recorded", "control", "M", BRIEF_HEAD.format(body="Use the harbor and market footage and the music that is free for a promotional video."), video_inputs("harbor", "market", "crowd"),
     vrules(fmt=False, loud=False, wer=False) + [{"id": "clips", "type": "clips_used", "file": "assets/video/trailer.mp4", "clips": ALLC, "must_use": ["market"], "must_not_use": ["crowd"]},
                                                 {"id": "recorded", "type": "sources_recorded", "file": "assets/video/trailer.mp4", "used": SRC_OK}], reference(),
     [("the CC BY license not recorded", reference(licenses={"market": "project-internal"}), {"recorded"})],
     purpose="a clip under CC BY 4.0 (commercial use allowed) used with its source and license recorded must not be flagged as an unlicensed clip")
case("vid-c3-person-with-consent", "control", "M", BRIEF_HEAD.format(body=PEOPLE_BODY), video_inputs("harbor", "market", "speaker2"), PEOPLE_RULES,
     reference(clips=PEOPLE_CLIPS, consent="inputs/consent/designer.txt"), [("consent not recorded", reference(clips=PEOPLE_CLIPS), {"consent"})],
     purpose="a real person who gave written consent, recorded in the manifest, must not be flagged as an unconsented likeness")
SMALL = 25
case("vid-c4-another-format", "control", "M",
     ("Make a 10 s promo for our game, which we sell: `assets/video/trailer.mp4`, 1280x720, 25 fps, 16:9, H.264 and AAC at 48 kHz, using the harbor and market footage and the free music with the narration. The platform wants -14 LUFS "
      "integrated, true peak at most -1 dBTP. Keep the narration by itself as `assets/audio/narration.wav` (render `inputs/script.txt` with `inputs/bin/tts`). Record both files in the manifest, naming every input used.\n"),
     video_inputs("harbor", "market"),
     [{"id": "format", "type": "video_format", "file": "assets/video/trailer.mp4", "width": 1280, "height": 720, "fps": 25, "duration": 10.0, "duration_tol": 0.5},
      {"id": "loudness", "type": "video_loudness", "file": "assets/video/trailer.mp4", "target": -14.0, "tol": 1.0, "max_dbtp": -1.0}] + manifest_rules(["assets/video/trailer.mp4", "assets/audio/narration.wav"]),
     reference(clips=(("harbor", 5), ("market", 5)), size=(1280, 720), fps=25, total=10.0), [("640x360 at 30 fps", reference(), {"format"})],
     purpose="the format rules follow the brief's numbers, not 640x360 / 30 fps / 12 s")


def write_cases():
    if CASES_DIR.exists():
        shutil.rmtree(CASES_DIR)
    for c in CASES:
        d = CASES_DIR / c["id"]
        d.mkdir(parents=True)
        (d / "brief.md").write_text(c["brief"].rstrip("\n") + "\n\n" + LAYOUT)
        copy_inputs(d, c)
        exp = {"case": c["id"], "skill": "game-video", **({"purpose": PURPOSE[c["id"]]} if c["id"] in PURPOSE else {}), "item": c["item"], "kind": c["kind"], "tools": c["tools"], "rules": c["rules"]}
        (d / "expected.json").write_text(json.dumps(exp, indent=2) + "\n")
        (d / "check.py").write_text(CHECK_PY)
        (d / "check.py").chmod(0o755)
    print(len(CASES), "cases written to", CASES_DIR)


if __name__ == "__main__":
    write_cases()
