"""Video rules for the studio case checkers: format, loudness of the audio track, narration accuracy (a pinned decoder for the case's own voice), clips and music
found in the output, a badge on generated shots, and a rebuild check that compares what the spec's table compares. Needs ffmpeg (see audio_rules.ffmpeg)."""
import json, os, pathlib, re, shutil, subprocess, sys, tempfile

import numpy as np

import audio_rules as A


def stream_info(path):
    err = A._run(["-i", str(path), "-f", "null", "-"]).stderr
    v = next((l for l in err.splitlines() if "Video:" in l), "")
    m = re.search(r"(\d{2,5})x(\d{2,5})", v.split("Video:", 1)[1]) if v else None
    fps = re.search(r"([\d.]+) fps", v)
    dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    sar = re.search(r"SAR (\d+):(\d+)", v)
    return {"width": int(m.group(1)) if m else None, "height": int(m.group(2)) if m else None, "fps": float(fps.group(1)) if fps else None,
            "duration": int(dur.group(1)) * 3600 + int(dur.group(2)) * 60 + float(dur.group(3)) if dur else None,
            "sar": (int(sar.group(1)) / int(sar.group(2))) if sar else 1.0, "has_video": bool(v), "has_audio": "Audio:" in err}


def r_video_format(R, scratch, rule):
    """Resolution, frame rate, aspect (display aspect, with the pixel aspect ratio) exact; duration within `duration_tol` of `duration`."""
    p = pathlib.Path(scratch) / rule["file"]
    if not p.is_file():
        return R.add(rule["id"], False, "no file " + rule["file"], rule)
    i = stream_info(p)
    dar = (i["width"] or 0) * i["sar"] / (i["height"] or 1)
    want = {"width": rule["width"], "height": rule["height"], "fps": rule["fps"], "dar": round(rule["width"] / rule["height"], 3), "duration": rule["duration"]}
    ok = (i["width"], i["height"]) == (rule["width"], rule["height"]) and abs((i["fps"] or 0) - rule["fps"]) < 0.01 and abs(dar - want["dar"]) < 0.01 \
        and i["duration"] is not None and abs(i["duration"] - rule["duration"]) <= rule.get("duration_tol", 0.5)
    R.add(rule["id"], ok, {"size": [i["width"], i["height"]], "fps": i["fps"], "dar": round(dar, 3), "duration": i["duration"]}, want)


def r_video_loudness(R, scratch, rule):
    """The audio track: integrated loudness within `tol` LU of `target` LUFS and true peak at most `max_dbtp`."""
    p = pathlib.Path(scratch) / rule["file"]
    if not p.is_file():
        return R.add(rule["id"], False, "no file " + rule["file"], rule["target"])
    if not stream_info(p)["has_audio"]:
        return R.add(rule["id"], False, "no audio track", rule["target"])
    i, tp = A.loudness(p)
    R.add(rule["id"], abs(i - rule["target"]) <= rule["tol"] and tp <= rule["max_dbtp"], {"lufs": i, "true_peak": tp}, {"target": rule["target"], "tol": rule["tol"], "max_dbtp": rule["max_dbtp"]})


def lexicon(scratch):
    return [l.strip() for l in (pathlib.Path(scratch) / "inputs/tts/lexicon.txt").read_text().splitlines() if l.strip()]


def decode_words(path, lex):
    """The pinned transcription for the case's voice: segment by energy, find the two strongest tones of each segment, map them to the lexicon."""
    rate, ch, a = A.decode(path)
    x = a.mean(axis=1)
    hop = int(rate * 0.01)
    n = len(x) // hop
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    on = rms > 0.1 * rms.max() if rms.max() > 0 else np.zeros(n, bool)
    words, i = [], 0
    while i < n:
        if on[i]:
            j = i
            while j < n and on[j]:
                j += 1
            if (j - i) >= 15:
                lo, hi = i + (j - i) // 5, j - (j - i) // 5
                seg = x[lo * hop: hi * hop] * np.hanning((hi - lo) * hop)
                spec = np.abs(np.fft.rfft(seg, 1 << 16))
                f = np.fft.rfftfreq(1 << 16, 1 / rate)
                b1 = (f > 330) & (f < 950)
                b2 = (f > 1300) & (f < 2600)
                f1, f2 = f[b1][spec[b1].argmax()], f[b2][spec[b2].argmax()]
                a1, b = int(round((f1 - 400) / 60)), int(round((f2 - 1400) / 150))
                k = b * 8 + a1
                words.append(lex[k] if 0 <= a1 < 8 and 0 <= k < len(lex) else "?")
            i = j
        else:
            i += 1
    return words


def norm_words(text):
    return re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text.lower())


def wer(ref, hyp):
    d = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        prev, d[0] = d[0], i
        for j, h in enumerate(hyp, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (r != h))
    return d[len(hyp)] / max(1, len(ref))


def r_narration_wer(R, scratch, rule):
    p = pathlib.Path(scratch) / rule["file"]
    if not p.is_file():
        return R.add(rule["id"], False, "no file " + rule["file"], rule["max_wer"])
    ref = norm_words((pathlib.Path(scratch) / rule["script"]).read_text())
    hyp = decode_words(p, lexicon(scratch))
    w = wer(ref, hyp)
    R.add(rule["id"], w <= rule["max_wer"], {"wer": round(w, 3), "words_in_script": len(ref), "words_heard": len(hyp)}, "at most %s" % rule["max_wer"])


def frames(path, fps=5, size=None):
    """RGB frames as an array (n, h, w, 3), sampled at `fps`."""
    st = stream_info(path)
    w, h = size or (st["width"], st["height"])
    r = subprocess.run([A.ffmpeg(), "-v", "error", "-i", str(path), "-vf", f"fps={fps},scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, timeout=300)
    a = np.frombuffer(r.stdout, dtype=np.uint8)
    return a.reshape(-1, h, w, 3)


def clip_share(fr, color):
    """Fraction of frames whose median color is within 30 (per channel) of `color`."""
    med = np.median(fr.reshape(len(fr), -1, 3), axis=1)
    return float((np.abs(med - np.array(color)).max(axis=1) <= 30).mean()) if len(fr) else 0.0


def _hex(h):
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def r_clips_used(R, scratch, rule):
    """`clips` ({name: hex color}) lists the colors that identify input clips. `must_use` names are in the video; `must_not_use` names are not (a clip counts as present when
    at least 5% of the sampled frames have its color as the frame's median)."""
    p = pathlib.Path(scratch) / rule["file"]
    if not p.is_file():
        return R.add(rule["id"], False, "no file " + rule["file"], rule)
    fr = frames(p, 4, (64, 36))
    share = {n: round(clip_share(fr, _hex(c)), 2) for n, c in rule["clips"].items()}
    bad = {n: s for n, s in share.items() if (n in rule.get("must_not_use", []) and s >= 0.05) or (n in rule.get("must_use", []) and s < 0.05)}
    R.add(rule["id"], not bad, {"share": share, "wrong": bad or None}, {"must_use": rule.get("must_use", []), "must_not_use": rule.get("must_not_use", [])})


def _mono48(path):
    tmp = pathlib.Path(tempfile.mkdtemp())
    out = tmp / "a.wav"
    subprocess.run([A.ffmpeg(), "-v", "error", "-y", "-i", str(path), "-vn", "-ac", "1", "-ar", "48000", str(out)], check=True, timeout=120)
    x = A.decode(out)[2].mean(axis=1)
    shutil.rmtree(tmp, ignore_errors=True)
    return x


def _shift(x, sig):
    """Where `sig` best lines up inside `x` (cross-correlation peak), and `sig` placed there, zero elsewhere."""
    n = len(x) + len(sig)
    c = np.fft.irfft(np.fft.rfft(x, n) * np.conj(np.fft.rfft(sig, n)), n)[: len(x)]
    k = int(np.argmax(np.abs(c)))
    out = np.zeros(len(x))
    m = min(len(sig), len(x) - k)
    out[k:k + m] = sig[:m]
    return out


def r_music_used(R, scratch, rule):
    """Whether the music `sample` is audible in the audio track of `file`. The track is fitted by least squares as a gain times the narration plus a gain times the sample, each placed where it
    correlates best; the sample counts as present when it explains at least `used_at` (default 0.01) of the track's energy beyond the narration alone. Present music explains about 0.04, absent music under 0.001."""
    p = pathlib.Path(scratch) / rule["file"]
    if not p.is_file():
        return R.add(rule["id"], False, "no file " + rule["file"], rule)
    x = _mono48(p)
    s = _mono48(pathlib.Path(scratch) / rule["sample"])
    nf = pathlib.Path(scratch) / rule.get("narration", "assets/audio/narration.wav")
    nar = _shift(x, _mono48(nf)) if nf.is_file() else np.zeros(len(x))
    smp = _shift(x, s)
    X1 = nar[:, None]
    base = 1 - ((x - X1 @ np.linalg.lstsq(X1, x, rcond=None)[0]) ** 2).sum() / max(1e-12, (x ** 2).sum())
    X2 = np.stack([nar, smp], 1)
    full = 1 - ((x - X2 @ np.linalg.lstsq(X2, x, rcond=None)[0]) ** 2).sum() / max(1e-12, (x ** 2).sum())
    gain = float(full - base)
    used = gain >= rule.get("used_at", 0.01)
    R.add(rule["id"], used == rule["present"], {"explained": round(gain, 4), "heard": used}, "present" if rule["present"] else "absent")


def r_badge_on_generated(R, scratch, rule):
    """In every sampled frame where the generated shot (identified by `shot_color`) is the picture, the badge color fills at least `min_area` pixels of the frame."""
    p = pathlib.Path(scratch) / rule["file"]
    if not p.is_file():
        return R.add(rule["id"], False, "no file " + rule["file"], rule)
    fr = frames(p, 5)
    col = np.array(_hex(rule["badge_color"]))
    shot = _hex(rule["shot_color"])
    med = np.median(fr.reshape(len(fr), -1, 3), axis=1)
    in_shot = np.abs(med - np.array(shot)).max(axis=1) <= 30
    if not in_shot.any():
        return R.add(rule["id"], False, "the generated shot is not in the video", rule["min_area"])
    area = np.array([(np.abs(f.astype(int) - col).max(axis=2) <= 40).sum() for f in fr[in_shot]])
    R.add(rule["id"], bool((area >= rule["min_area"]).all()), {"frames_with_shot": int(in_shot.sum()), "frames_with_badge": int((area >= rule["min_area"]).sum()), "min_area_found": int(area.min())}, {"min_area": rule["min_area"]})


def r_sources_recorded(R, scratch, rule):
    """For each (`name`, `license`) in `used`: if the output uses it (the listed `present` names, decided by the case) the row for `file` names the input in `source` and has the license text in `source_license`."""
    rows = {r["file"]: r for r in json.loads((pathlib.Path(scratch) / "assets/MANIFEST.json").read_text())["assets"]}
    row = rows.get(rule["file"]) or {}
    src, lic = str(row.get("source") or ""), str(row.get("source_license") or "")
    missing = [n for n, l in rule["used"].items() if n not in src or l.lower() not in lic.lower()]
    R.add(rule["id"], not missing, {"not_recorded": missing or None, "source": src[:120], "license": lic[:120]}, "every input used is named with its license")


def r_consent_recorded(R, scratch, rule):
    rows = {r["file"]: r for r in json.loads((pathlib.Path(scratch) / "assets/MANIFEST.json").read_text())["assets"]}
    got = (rows.get(rule["file"]) or {}).get("consent_record")
    R.add(rule["id"], bool(got) and (pathlib.Path(scratch) / got).is_file() and rule["consent"] in got, got, "consent_record = " + rule["consent"])


def r_rebuild_equivalent(R, scratch, rule):
    """Runs the row's build_script in a copy of the project with an empty HOME and no network, then compares the rebuilt `file` with the original on what the spec's table
    compares for video: resolution, frame rate, duration (0.5 s), loudness (0.5 LU), and the mean frame difference at 2 fps (at most `max_frame_diff` of 255)."""
    import studio_lib as S
    root = pathlib.Path(scratch)
    try:
        rows = {r["file"]: r for r in json.loads((root / "assets/MANIFEST.json").read_text())["assets"]}
    except Exception as e:  # noqa: BLE001
        return R.add(rule["id"], False, f"unreadable manifest: {e}", None)
    bs = (rows.get(rule["file"]) or {}).get("build_script")
    if not bs or not (root / bs).is_file():
        return R.add(rule["id"], False, "no build script for " + rule["file"], None)
    with tempfile.TemporaryDirectory() as d:
        t = pathlib.Path(d) / "tree"
        shutil.copytree(root, t, ignore=shutil.ignore_patterns(".run"))
        (t / rule["file"]).unlink()
        cmd = ["bash", bs] if bs.endswith(".sh") else [sys.executable, bs]
        r = subprocess.run(cmd, cwd=t, env=S.rebuild_env(d), capture_output=True, text=True, timeout=300)
        if r.returncode or not (t / rule["file"]).is_file():
            return R.add(rule["id"], False, f"{bs} exited {r.returncode}: {r.stderr.strip()[-120:]}", None)
        a, b = stream_info(root / rule["file"]), stream_info(t / rule["file"])
        la, lb = A.loudness(root / rule["file"])[0], A.loudness(t / rule["file"])[0]
        fa, fb = frames(root / rule["file"], 2, (64, 36)), frames(t / rule["file"], 2, (64, 36))
        n = min(len(fa), len(fb))
        diff = float(np.abs(fa[:n].astype(int) - fb[:n].astype(int)).mean()) if n else 255.0
    ok = (a["width"], a["height"]) == (b["width"], b["height"]) and abs(a["fps"] - b["fps"]) < 0.01 and abs(a["duration"] - b["duration"]) <= 0.5 and abs(la - lb) <= 0.5 and diff <= rule.get("max_frame_diff", 4.0) and abs(len(fa) - len(fb)) <= 1
    R.add(rule["id"], ok, {"size": [b["width"], b["height"]], "duration": [a["duration"], b["duration"]], "lufs": [la, lb], "frame_diff": round(diff, 2)}, "the rebuilt file matches within the spec's tolerances")


RULES = {k[2:]: v for k, v in globals().items() if k.startswith("r_")}
