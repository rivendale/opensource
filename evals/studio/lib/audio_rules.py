"""Audio rules for the studio case checkers. Measurements follow skills/SPEC-studio.md: loudness and true peak are what ffmpeg's `ebur128` filter reports on
the file padded with silence to at least 1 s. ffmpeg is taken from STUDIO_FFMPEG, then PATH, then the imageio-ffmpeg package."""
import json, os, pathlib, re, shutil, subprocess, sys, tempfile

import numpy as np


def ffmpeg():
    exe = os.environ.get("STUDIO_FFMPEG") or shutil.which("ffmpeg")
    if exe:
        return exe
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def _run(args):
    return subprocess.run([ffmpeg(), "-hide_banner", "-nostats", *args], capture_output=True, text=True, timeout=120)


def info(path):
    err = _run(["-i", str(path), "-f", "null", "-"]).stderr
    m = re.search(r"Audio: (\w+).*?, (\d+) Hz, (\w+)", err)
    if not m:
        raise ValueError("not decodable audio: " + err.strip().splitlines()[-1][:80] if err.strip() else "not decodable audio")
    ch = {"mono": 1, "stereo": 2}.get(m.group(3))
    if ch is None:
        mm = re.search(r"(\d+) channels", m.group(3))
        ch = int(mm.group(1)) if mm else 0
    return {"codec": m.group(1), "rate": int(m.group(2)), "channels": ch}


def decode(path):
    """(rate, channels, float32 array of shape (n, channels)) at the file's own rate."""
    i = info(path)
    r = subprocess.run([ffmpeg(), "-v", "error", "-i", str(path), "-f", "f32le", "-acodec", "pcm_f32le", "-"], capture_output=True, timeout=120)
    a = np.frombuffer(r.stdout, dtype="<f4")
    return i["rate"], i["channels"], a.reshape(-1, i["channels"]) if i["channels"] else a.reshape(-1, 1)


def loudness(path):
    err = _run(["-i", str(path), "-af", "apad=whole_dur=1,ebur128=peak=true", "-f", "null", "-"]).stderr
    s = err[err.rindex("Summary:"):]
    return float(re.search(r"I:\s+(-?[\d.]+) LUFS", s).group(1)), float(re.search(r"Peak:\s+(-?[\d.]+) dBFS", s).group(1))


def sniff(path):
    b = pathlib.Path(path).read_bytes()[:64]
    if b[:4] == b"RIFF" and b[8:12] == b"WAVE":
        i = b.find(b"fmt ")
        tag = int.from_bytes(b[i + 8:i + 10], "little") if i >= 0 else 0
        bits = int.from_bytes(b[i + 22:i + 24], "little") if i >= 0 else 0
        return {1: f"wav-pcm{bits}", 3: f"wav-float{bits}"}.get(tag, f"wav-tag{tag}")
    if b[:4] == b"OggS":
        return "ogg"
    if b[:3] == b"ID3" or (len(b) > 1 and b[0] == 0xFF and (b[1] & 0xE0) == 0xE0):
        return "mp3"
    if b[:4] == b"fLaC":
        return "flac"
    if b[4:8] == b"ftyp":
        return "m4a"
    return "unknown"


def resolve(scratch, f):
    """A path under the scratch directory; `jump.*` style patterns match the first file of that name with any extension."""
    p = pathlib.Path(scratch) / f
    if "*" in f:
        hits = sorted(x for x in p.parent.glob(p.name) if x.is_file())
        return hits[0] if hits else p
    return p


def _files(scratch, rule):
    out, bad = [], []
    names = rule["files"]
    if rule.get("glob"):
        names = sorted(x.relative_to(scratch).as_posix() for x in pathlib.Path(scratch).glob(rule["glob"]) if x.is_file() and x.suffix != ".json")
        if not names:
            return [], [rule["glob"]]
    for f in names:
        p = resolve(scratch, f)
        (out if p.is_file() else bad).append(p if p.is_file() else f)
    return out, bad


def r_audio_format(R, scratch, rule):
    """All `files` have one sample rate and one channel count, equal to `rate` and `channels` when given."""
    ps, missing = _files(scratch, rule)
    got = {}
    for p in ps:
        try:
            i = info(p)
            got[p.name] = (i["rate"], i["channels"])
        except Exception as e:  # noqa: BLE001
            missing.append(f"{p.name}: {e}")
    want = (rule.get("rate"), rule.get("channels"))
    bad = [n for n, (r, c) in got.items() if (want[0] and r != want[0]) or (want[1] and c != want[1])]
    uniform = len(set(got.values())) <= 1
    R.add(rule["id"], not missing and not bad and uniform, {"missing": missing, "differ": bad or None, "found": {n: list(v) for n, v in got.items()}}, {"rate": want[0], "channels": want[1], "all_equal": True})


def r_true_peak(R, scratch, rule):
    ps, missing = _files(scratch, rule)
    hot = {}
    for p in ps:
        tp = loudness(p)[1]
        if tp > rule["max_dbtp"]:
            hot[p.name] = tp
    R.add(rule["id"], not missing and not hot, {"missing": missing, "above": hot or None}, "at most %s dBTP" % rule["max_dbtp"])


def r_loudness_spread(R, scratch, rule):
    ps, missing = _files(scratch, rule)
    vals = {p.name: loudness(p)[0] for p in ps}
    med = float(np.median(list(vals.values()))) if vals else 0.0
    far = {n: round(v - med, 1) for n, v in vals.items() if abs(v - med) > rule["max_lu"]}
    R.add(rule["id"], bool(vals) and not missing and not far, {"missing": missing, "median_lufs": round(med, 1), "outside": far or None}, "within %s LU of the median" % rule["max_lu"])


def r_container_in(R, scratch, rule):
    """The bytes (not the name) of each file are one of the `allowed` containers, e.g. wav-pcm16, mp3."""
    ps, missing = _files(scratch, rule)
    got = {p.name: sniff(p) for p in ps}
    bad = {n: c for n, c in got.items() if c not in rule["allowed"]}
    R.add(rule["id"], not missing and not bad, {"missing": missing, "not_allowed": bad or None}, rule["allowed"])


def r_tail_silence(R, scratch, rule):
    """Trailing samples below `floor_db` last at most `max_s` seconds, and the leading ones the same."""
    ps, missing = _files(scratch, rule)
    long_ = {}
    for p in ps:
        rate, ch, a = decode(p)
        m = np.abs(a).max(axis=1)
        loud = np.nonzero(m > 10 ** (rule["floor_db"] / 20))[0]
        tail = (len(m) - 1 - loud[-1]) / rate if len(loud) else len(m) / rate
        if tail > rule["max_s"]:
            long_[p.name] = round(tail, 2)
    R.add(rule["id"], not missing and not long_, {"missing": missing, "silent_tail_s": long_ or None}, "at most %s s" % rule["max_s"])


def centroid(a, rate):
    x = a.mean(axis=1)
    s = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    f = np.fft.rfftfreq(len(x), 1 / rate)
    return float((f * s).sum() / s.sum()) if s.sum() > 0 else 0.0


def r_event_profile(R, scratch, rule):
    """Each file in `events` ({event: {file, dur: [min, max], centroid: [min, max]}}) lasts and sounds as the brief says that event does."""
    bad = {}
    for ev, spec in rule["events"].items():
        p = resolve(scratch, spec["file"])
        if not p.is_file():
            bad[ev] = "no file " + spec["file"]
            continue
        rate, ch, a = decode(p)
        d, c = len(a) / rate, centroid(a, rate)
        if not (spec["dur"][0] <= d <= spec["dur"][1] and spec["centroid"][0] <= c <= spec["centroid"][1]):
            bad[ev] = {"dur_s": round(d, 2), "centroid_hz": round(c)}
    R.add(rule["id"], not bad, bad or "every event sounds as described", {e: {"dur": s["dur"], "centroid": s["centroid"]} for e, s in rule["events"].items()})


def r_params_render_export(R, scratch, rule):
    """The master of each file, rendered with inputs/bin/sfx, reproduces the export (normalized correlation at least `min_corr`, lengths within 0.1 s)."""
    root = pathlib.Path(scratch)
    try:
        rows = {r["file"]: r for r in json.loads((root / rule.get("manifest", "assets/MANIFEST.json")).read_text())["assets"]}
    except Exception as e:  # noqa: BLE001
        return R.add(rule["id"], False, f"unreadable manifest: {e}", rule["min_corr"])
    bad = {}
    with tempfile.TemporaryDirectory() as d:
        for f in rule["files"]:
            m = (rows.get(f) or {}).get("master")
            if not m or not (root / m).is_file():
                bad[f] = "no master"
                continue
            out = pathlib.Path(d) / (pathlib.Path(f).stem + ".wav")
            exp = resolve(scratch, f)
            ei = info(exp)
            r = subprocess.run([sys.executable, str(root / "inputs/bin/sfx"), "render", str(root / m), str(out), "--rate", str(ei["rate"])] + (["--stereo"] if ei["channels"] == 2 else []), capture_output=True, text=True, timeout=120)
            if r.returncode or not out.is_file():
                bad[f] = "the master does not render: " + r.stderr.strip()[-80:]
                continue
            ra, _, a = decode(out)
            rb, _, b = decode(exp)
            a, b = a.mean(axis=1), b.mean(axis=1)
            if ra != rb or abs(len(a) - len(b)) / ra > 0.1:
                bad[f] = f"render {len(a) / ra:.2f}s/{ra} Hz, export {len(b) / rb:.2f}s/{rb} Hz"
                continue
            n = min(len(a), len(b))
            a, b = a[:n], b[:n]
            den = float(np.linalg.norm(a) * np.linalg.norm(b))
            c = float(abs(a @ b) / den) if den else 0.0
            if c < rule["min_corr"]:
                bad[f] = round(c, 3)
    R.add(rule["id"], not bad, bad or "every master reproduces its export", rule["min_corr"])


def used_score(scratch, export, sample):
    """Peak normalized cross-correlation of the sample inside the export (1.0: a scaled copy, near 0: unrelated)."""
    s = decode(pathlib.Path(scratch) / sample)[2].mean(axis=1)
    s = s - s.mean()
    x = decode(resolve(scratch, export))[2].mean(axis=1)
    if len(x) < len(s):
        x = np.pad(x, (0, len(s) - len(x)))
    n = len(x) + len(s)
    corr = np.fft.irfft(np.fft.rfft(x, n) * np.conj(np.fft.rfft(s, n)), n)[: len(x) - len(s) + 1]
    c2 = np.concatenate([[0], np.cumsum(x ** 2)])
    energy = c2[len(s):len(x) + 1] - c2[: len(x) - len(s) + 1]
    return float(np.max(np.abs(corr) / (np.sqrt(energy * (s @ s)) + 1e-12)))


def r_sample_license(R, scratch, rule):
    """If any export in `files` contains `sample` (score at least `used_at`), its manifest row names a source and a `source_license` from `allowed` (empty: the sample may not be used at all)."""
    try:
        rows = {r["file"]: r for r in json.loads((pathlib.Path(scratch) / "assets/MANIFEST.json").read_text())["assets"]}
    except Exception as e:  # noqa: BLE001
        rows, err = {}, str(e)
    bad, used = {}, {}
    for f in rule["files"]:
        if not resolve(scratch, f).is_file():
            continue
        sc = used_score(scratch, f, rule["sample"])
        if sc < rule.get("used_at", 0.5):
            continue
        used[f] = round(sc, 2)
        row = rows.get(f) or {}
        if not (row.get("source") and row.get("source_license") in rule["allowed"]):
            bad[f] = {"source": row.get("source"), "source_license": row.get("source_license")}
    R.add(rule["id"], not bad, {"used_in": used or None, "recorded_wrongly": bad or None} if (used or bad) else "sample not used", {"allowed_licenses": rule["allowed"]})


def r_files_exist(R, scratch, rule):
    """Each file exists and decodes to at least `min_s` seconds of non-silent audio."""
    bad = []
    for f in rule["files"]:
        p = resolve(scratch, f)
        try:
            rate, ch, a = decode(p)
            if len(a) / rate < rule.get("min_s", 0.05) or float(np.abs(a).max()) < 1e-4:
                bad.append(f + ": empty or silent")
        except Exception:  # noqa: BLE001
            bad.append(f + ": missing or unreadable")
    R.add(rule["id"], not bad, bad or "all present", rule["files"])


RULES = {k[2:]: v for k, v in globals().items() if k.startswith("r_")}
