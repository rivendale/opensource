"""Music rules for the studio case checkers (loop seam, tempo, length, loudness target, key from the kept score, melody similarity, prompt recorded).
Measurements follow skills/SPEC-studio.md; the onset detector is the one defined here (short-time energy flux), pinned by this file."""
import json, pathlib, re

import numpy as np

import audio_rules as A


def mono(path):
    rate, ch, a = A.decode(path)
    return rate, a.mean(axis=1)


def _coarse(x, rate, hop_ms=5, refractory_ms=120):
    hop = int(rate * hop_ms / 1000)
    x = np.concatenate([np.zeros(hop * 4), x])
    n = len(x) // hop
    rms = np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(axis=1))
    flux = np.maximum(0, np.diff(rms, prepend=0))
    if flux.max() <= 0:
        return []
    thr = 0.3 * flux.max()
    out, last = [], -10 ** 9
    for i in range(1, n - 1):
        if flux[i] >= thr and flux[i] >= flux[i - 1] and flux[i] > flux[i + 1] and (i - last) * hop_ms >= refractory_ms:
            out.append((i - 4) * hop_ms / 1000)
            last = i
    return out


def onsets(x, rate, refractory_ms=120):
    """Times (s) of energy onsets. Coarse pass: positive flux of the 5 ms RMS curve above 30% of its maximum, local maxima at least 120 ms apart. Fine pass (so the
    timing error is far under 1 BPM at the tempos in the cases): around each coarse onset, the first millisecond at which a 2 ms RMS reaches 20% of its maximum
    over the next 25 ms."""
    out = []
    w = max(1, int(rate * 0.002))
    for t in _coarse(x, rate, refractory_ms=refractory_ms):
        a = max(0, int((t - 0.012) * rate))
        seg = x[a: a + int(0.04 * rate)]
        if len(seg) < 4 * w:
            out.append(t)
            continue
        c = np.concatenate([[0.0], np.cumsum(seg.astype(np.float64) ** 2)])
        step = max(1, int(rate * 0.001))
        idx = np.arange(0, len(seg) - w, step)
        r = np.sqrt((c[idx + w] - c[idx]) / w)
        peak = r[: int(0.025 * rate / step)].max()
        k = int(np.argmax(r >= 0.2 * peak)) if peak > 0 else 0
        out.append((a + idx[k]) / rate)
    return out


def _file(scratch, rule):
    p = A.resolve(scratch, rule["file"])
    return p if p.is_file() else None


def r_loop_seam(R, scratch, rule):
    """Playing the file twice: the largest step across the seam is at most `max_ratio` times the median sample-to-sample step in the 50 ms either side."""
    p = _file(scratch, rule)
    if not p:
        return R.add(rule["id"], False, "no file " + rule["file"], rule["max_ratio"])
    rate, x = mono(p)
    w = int(0.05 * rate)
    y = np.concatenate([x[-w:], x[:w]])
    steps = np.abs(np.diff(y))
    seam = float(steps[w - 1])
    med = float(np.median(steps)) or 1e-9
    R.add(rule["id"], seam <= rule["max_ratio"] * med, {"seam_step": round(seam, 5), "median_step": round(med, 5), "ratio": round(seam / med, 2)}, "at most %s x the median" % rule["max_ratio"])


def r_loop_tempo(R, scratch, rule):
    """Playing the file twice: the interval across the seam between the last and the first onset equals the median beat interval within `bpm_tol` BPM."""
    p = _file(scratch, rule)
    if not p:
        return R.add(rule["id"], False, "no file " + rule["file"], rule["bpm_tol"])
    rate, x = mono(p)
    T = len(x) / rate
    ons = onsets(np.concatenate([x, x]), rate)
    before = [o for o in ons if o < T - 0.02]
    after = [o for o in ons if o >= T - 0.02]
    if len(before) < 3 or not after:
        return R.add(rule["id"], False, "too few onsets found (%d)" % len(ons), rule["bpm_tol"])
    med = float(np.median(np.diff([o for o in ons if o < T - 0.02])))
    seam = after[0] - before[-1]
    bpm_med, bpm_seam = 60 / med, 60 / seam
    R.add(rule["id"], abs(bpm_seam - bpm_med) <= rule["bpm_tol"], {"beat_bpm": round(bpm_med, 1), "seam_bpm": round(bpm_seam, 1)}, "within %s BPM" % rule["bpm_tol"])


def r_tempo_bpm(R, scratch, rule):
    p = _file(scratch, rule)
    if not p:
        return R.add(rule["id"], False, "no file " + rule["file"], rule["bpm"])
    rate, x = mono(p)
    d = np.diff(onsets(x, rate))
    if len(d) < 3:
        return R.add(rule["id"], False, "too few onsets", rule["bpm"])
    bpm = 60 / float(np.median(d))
    R.add(rule["id"], abs(bpm - rule["bpm"]) <= rule.get("tol", 1.0), round(bpm, 1), {"bpm": rule["bpm"], "tol": rule.get("tol", 1.0)})


def r_length_within(R, scratch, rule):
    p = _file(scratch, rule)
    if not p:
        return R.add(rule["id"], False, "no file " + rule["file"], rule["seconds"])
    rate, x = mono(p)
    d = len(x) / rate
    tol = max(0.5, 0.02 * rule["seconds"])
    R.add(rule["id"], abs(d - rule["seconds"]) <= tol, round(d, 2), {"seconds": rule["seconds"], "tol": tol})


def r_loudness_target(R, scratch, rule):
    """Integrated loudness of each file within `tol` LU of `target` LUFS (the median of the set when `target` is null), and true peak at most `max_dbtp`."""
    bad, vals = {}, {}
    for f in rule["files"]:
        p = A.resolve(scratch, f)
        if p.is_file():
            vals[f] = A.loudness(p)
    target = rule["target"] if rule.get("target") is not None else float(np.median([v[0] for v in vals.values()])) if vals else 0.0   # no target: the median of the set
    for f in rule["files"]:
        if f not in vals:
            bad[f] = "missing"
            continue
        i, tp = vals[f]
        if abs(i - target) > rule["tol"]:
            bad[f] = {"lufs": i}
        elif tp > rule.get("max_dbtp", -1.0):
            bad[f] = {"true_peak": tp}
    R.add(rule["id"], not bad, bad or "all on target", {"target": rule.get("target") if rule.get("target") is not None else "median of the set", "tol": rule["tol"], "max_dbtp": rule.get("max_dbtp", -1.0)})


NAMES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
SCALES = {"minor": (0, 2, 3, 5, 7, 8, 10), "major": (0, 2, 4, 5, 7, 9, 11)}


def score_notes(path):
    notes, head = [], None
    for l in pathlib.Path(path).read_text().splitlines():
        l = l.strip()
        if not l or l.startswith("#"):
            continue
        if head is None:
            head = dict(kv.split("=", 1) for kv in l.split())
            continue
        s, d, p = l.split()
        if p == "R":
            continue
        n = NAMES[p[0]]
        i = 1
        while i < len(p) and p[i] in "#b":
            n += 1 if p[i] == "#" else -1
            i += 1
        notes.append((float(s), float(d), 12 * (int(p[i:]) + 1) + n))
    return head, notes


def manifest_master(scratch, f):
    rows = {r["file"]: r for r in json.loads((pathlib.Path(scratch) / "assets/MANIFEST.json").read_text())["assets"]}
    m = (rows.get(f) or {}).get("master")
    return pathlib.Path(scratch) / m if m and (pathlib.Path(scratch) / m).is_file() else None


def r_key_from_score(R, scratch, rule):
    """Read from the kept score (the manifest's master), never from the audio: at least 90% of note duration lies on the scale of `tonic` + `mode`."""
    m = manifest_master(scratch, rule["file"]) if (pathlib.Path(scratch) / "assets/MANIFEST.json").is_file() else None
    if not m:
        return R.add(rule["id"], False, "no kept score for " + rule["file"], rule["tonic"] + " " + rule["mode"])
    _, notes = score_notes(m)
    tonic = NAMES[rule["tonic"][0]] + (1 if "#" in rule["tonic"] else -1 if "b" in rule["tonic"][1:] else 0)
    scale = {(tonic + s) % 12 for s in SCALES[rule["mode"]]}
    tot = sum(d for _, d, _ in notes)
    on = sum(d for _, d, p in notes if p % 12 in scale)
    frac = on / tot if tot else 0.0
    R.add(rule["id"], frac >= 0.9, round(frac, 3), "at least 0.9 of note duration in " + rule["tonic"] + " " + rule["mode"])


def intervals(notes):
    seq = [p for _, _, p in sorted(notes, key=lambda n: (n[0], -n[2]))]
    return [b - a for a, b in zip(seq, seq[1:])]


def r_melody_not_copied(R, scratch, rule):
    """No run of `run` consecutive pitch intervals (transposition-invariant, rhythm ignored) is shared between the reference tune and the delivered score."""
    ref = intervals(score_notes(pathlib.Path(scratch) / rule["reference"])[1])
    worst = 0
    for f in rule["files"]:
        m = manifest_master(scratch, f)
        if not m:
            return R.add(rule["id"], False, "no kept score for " + f, rule["run"])
        got = intervals(score_notes(m)[1])
        best = 0
        for i in range(len(ref)):
            for j in range(len(got)):
                k = 0
                while i + k < len(ref) and j + k < len(got) and ref[i + k] == got[j + k]:
                    k += 1
                best = max(best, k)
        worst = max(worst, best)
    if rule.get("must_share"):
        return R.add(rule["id"], worst >= rule["run"], {"longest_shared_run": worst}, "at least %d (the brief supplies a public-domain tune to use)" % rule["run"])
    R.add(rule["id"], worst < rule["run"], {"longest_shared_run": worst}, "fewer than %d" % rule["run"])


def r_prompt_recorded(R, scratch, rule):
    """The row's `seed_or_params` holds the prompt as text: at least `min_words` words made of letters (a bare seed or a flag list is not a prompt)."""
    rows = {r["file"]: r for r in json.loads((pathlib.Path(scratch) / "assets/MANIFEST.json").read_text())["assets"]}
    got = str((rows.get(rule["file"]) or {}).get("seed_or_params") or "")
    words = [w for w in re.findall(r"[A-Za-z]{3,}", got)]
    R.add(rule["id"], len(words) >= rule["min_words"], {"words": len(words), "text": got[:80]}, "at least %d words of prompt text" % rule["min_words"])


RULES = {k[2:]: v for k, v in globals().items() if k.startswith("r_")}
