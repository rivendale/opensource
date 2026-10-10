"""Shared measurements for the studio evaluation checkers (evals/studio/*/cases/*/check.py).

A checker is run after the agent has exited, in the same sandbox, with the network off:

    python3 check.py SCRATCH_DIR EXPECTED_JSON

It reads the scratch tree and expected.json only and prints one JSON object:
    {"case": id, "rules": [{"id": rule, "pass": true or false, "measured": value, "threshold": value}]}

expected.json is {"case", "skill", "item", "kind", "tools", "rules": [{"id", "type", ...parameters}]}. Each rule type below is one measurement
from skills/SPEC-studio.md (Measurement defaults). A rule that cannot be measured (a missing file, an unreadable image) fails with the reason
as `measured`; a checker never skips a rule. Needs Pillow and numpy (both in the pinned image).
"""
import hashlib, importlib.util, json, os, pathlib, shutil, subprocess, sys, tempfile

import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
_vpath = HERE / "validate_manifest.py"          # a copy beside the library (the pinned image), else the one in the repository
if not _vpath.is_file():
    _vpath = HERE.parent.parent.parent / "skills" / "studio" / "validate_manifest.py"
_spec = importlib.util.spec_from_file_location("validate_manifest", _vpath)
_vm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vm)

MASTER_SUFFIXES = {".xcf", ".kra", ".psd", ".ase", ".aseprite", ".blend", ".ora", ".svg", ".sfxr", ".mid", ".midi", ".rpp", ".als", ".flp"}


def hexcolor(h):
    h = h.strip().lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def load(path):
    """RGBA uint8 array (h, w, 4) of an image file."""
    with Image.open(path) as im:
        return np.array(im.convert("RGBA"))


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


class Rules:
    def __init__(self, case):
        self.case, self.rules = case, []

    def add(self, rid, ok, measured, threshold):
        self.rules.append({"id": rid, "pass": bool(ok), "measured": measured, "threshold": threshold})

    def out(self):
        return {"case": self.case, "rules": self.rules}


def _need(scratch, rel):
    p = pathlib.Path(scratch) / rel
    if not p.is_file():
        return None, f"missing file {rel}"
    return p, None


def r_size_exact(R, scratch, rule):
    p, err = _need(scratch, rule["file"])
    if err:
        return R.add(rule["id"], False, err, [rule["width"], rule["height"]])
    try:
        with Image.open(p) as im:
            got = list(im.size)
    except Exception as e:  # noqa: BLE001
        return R.add(rule["id"], False, f"unreadable image: {e}", [rule["width"], rule["height"]])
    R.add(rule["id"], got == [rule["width"], rule["height"]], got, [rule["width"], rule["height"]])


def r_palette_only(R, scratch, rule):
    p, err = _need(scratch, rule["file"])
    pal = {hexcolor(x) for x in (pathlib.Path(scratch) / rule["palette"]).read_text().split()} if (pathlib.Path(scratch) / rule["palette"]).is_file() else None
    if err or pal is None:
        return R.add(rule["id"], False, err or f"missing palette {rule['palette']}", "every opaque pixel in the palette")
    a = load(p)
    opaque = a[a[..., 3] == 255][:, :3]
    off = {tuple(int(v) for v in c) for c in np.unique(opaque, axis=0)} - pal
    R.add(rule["id"], not off, sorted("%02x%02x%02x" % c for c in off)[:6] or "all in palette", "every opaque pixel in the palette")


def r_matches_blocks(R, scratch, rule):
    """Each output pixel equals the most common color of its factor x factor block of a source image (a palette-locked downscale)."""
    p, err = _need(scratch, rule["file"])
    src = pathlib.Path(scratch) / rule["source"]
    if err or not src.is_file():
        return R.add(rule["id"], False, err or f"missing source {rule['source']}", rule["min_fraction"])
    out, s, f = load(p), load(src), rule["factor"]
    if out.shape[0] * f != s.shape[0] or out.shape[1] * f != s.shape[1]:
        return R.add(rule["id"], False, f"size {out.shape[1]}x{out.shape[0]} is not the source / {f}", rule["min_fraction"])
    hit = 0
    for y in range(out.shape[0]):
        for x in range(out.shape[1]):
            block = s[y * f:(y + 1) * f, x * f:(x + 1) * f].reshape(-1, 4)
            vals, counts = np.unique(block, axis=0, return_counts=True)
            hit += int(np.array_equal(vals[counts.argmax()], out[y, x]))
    frac = hit / (out.shape[0] * out.shape[1])
    R.add(rule["id"], frac >= rule["min_fraction"], round(frac, 4), rule["min_fraction"])


def cells(a, cw, ch, cols, rows):
    return [a[r * ch:(r + 1) * ch, c * cw:(c + 1) * cw] for r in range(rows) for c in range(cols)]


def r_cells_equal_sources(R, scratch, rule):
    """The sheet is cols x rows cells of cw x ch; cell i equals the i-th source image exactly (order as listed in the rule)."""
    p, err = _need(scratch, rule["file"])
    cw, ch, cols, rows = rule["cell_width"], rule["cell_height"], rule["cols"], rule["rows"]
    if err:
        return R.add(rule["id"], False, err, "cells equal their sources in order")
    a = load(p)
    if a.shape[1] != cw * cols or a.shape[0] != ch * rows:
        return R.add(rule["id"], False, f"sheet is {a.shape[1]}x{a.shape[0]}", f"{cw * cols}x{ch * rows}")
    bad = []
    for i, (cell, name) in enumerate(zip(cells(a, cw, ch, cols, rows), rule["sources"])):
        s = load(pathlib.Path(scratch) / name)
        if s.shape != cell.shape or not np.array_equal(s, cell):
            bad.append(i + 1)
    R.add(rule["id"], not bad, ("cells that differ from their source: %s" % bad) if bad else "all cells equal their sources", "cells equal their sources in order")


def r_cells_nonempty(R, scratch, rule):
    p, err = _need(scratch, rule["file"])
    if err:
        return R.add(rule["id"], False, err, rule["count"])
    a = load(p)
    cw, ch, cols, rows = rule["cell_width"], rule["cell_height"], rule["cols"], rule["rows"]
    if a.shape[1] != cw * cols or a.shape[0] != ch * rows:
        return R.add(rule["id"], False, f"sheet is {a.shape[1]}x{a.shape[0]}", f"{cw * cols}x{ch * rows}")
    n = sum(int((c[..., 3] > 0).any()) for c in cells(a, cw, ch, cols, rows))
    R.add(rule["id"], n == rule["count"], n, rule["count"])


def bbox(alpha):
    ys, xs = np.nonzero(alpha > 0)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def r_anchor_aligned(R, scratch, rule):
    """The anchor (bottom-center of each cell's opaque bounding box) is within `tolerance` px of the first cell's, and the cells are equal in size."""
    p, err = _need(scratch, rule["file"])
    if err:
        return R.add(rule["id"], False, err, rule["tolerance"])
    a = load(p)
    cw, ch, cols, rows = rule["cell_width"], rule["cell_height"], rule["cols"], rule["rows"]
    if a.shape[1] != cw * cols or a.shape[0] != ch * rows:
        return R.add(rule["id"], False, f"sheet is {a.shape[1]}x{a.shape[0]}", f"{cw * cols}x{ch * rows}")
    anchors = []
    for c in cells(a, cw, ch, cols, rows):
        b = bbox(c[..., 3])
        anchors.append(None if b is None else ((b[0] + b[2]) / 2.0, float(b[3])))
    if None in anchors:
        return R.add(rule["id"], False, "an empty cell", rule["tolerance"])
    dev = max(max(abs(x - anchors[0][0]), abs(y - anchors[0][1])) for x, y in anchors)
    R.add(rule["id"], dev <= rule["tolerance"], round(dev, 2), rule["tolerance"])


def r_content_preserved(R, scratch, rule):
    """Each cell has the same number of opaque pixels as its source (the frames were moved, not scaled or cropped)."""
    p, err = _need(scratch, rule["file"])
    if err:
        return R.add(rule["id"], False, err, "opaque pixel counts equal")
    a = load(p)
    cw, ch, cols, rows = rule["cell_width"], rule["cell_height"], rule["cols"], rule["rows"]
    if a.shape[1] != cw * cols or a.shape[0] != ch * rows:
        return R.add(rule["id"], False, f"sheet is {a.shape[1]}x{a.shape[0]}", f"{cw * cols}x{ch * rows}")
    bad = []
    for i, (cell, name) in enumerate(zip(cells(a, cw, ch, cols, rows), rule["sources"])):
        s = load(pathlib.Path(scratch) / name)
        if int((cell[..., 3] > 0).sum()) != int((s[..., 3] > 0).sum()):
            bad.append(i + 1)
    R.add(rule["id"], not bad, ("cells whose opaque pixel count differs: %s" % bad) if bad else "equal", "opaque pixel counts equal")


def neighbors_transparent(alpha):
    """True where a pixel is within 1 px (8-neighborhood) of a fully transparent pixel or the image edge."""
    t = np.pad(alpha == 0, 1, constant_values=True)
    h, w = alpha.shape
    near = np.zeros((h, w), bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            near |= t[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
    return near


def r_matte_clean(R, scratch, rule):
    p, err = _need(scratch, rule["file"])
    if err:
        return R.add(rule["id"], False, err, 0)
    a = load(p)
    m = np.array(hexcolor(rule["matte"]))
    tol = rule.get("tolerance", 0)
    dist = np.abs(a[..., :3].astype(int) - m).max(axis=2)
    bad = int(((dist <= tol) & (a[..., 3] > 0)).sum())
    R.add(rule["id"], bad == 0, bad, 0)


def r_partial_alpha_edge_only(R, scratch, rule):
    p, err = _need(scratch, rule["file"])
    if err:
        return R.add(rule["id"], False, err, 0)
    al = load(p)[..., 3]
    partial = (al > 0) & (al < 255)
    bad = int((partial & ~neighbors_transparent(al)).sum())
    R.add(rule["id"], bad == 0, bad, 0)


def r_silhouette(R, scratch, rule):
    """The opaque pixels (alpha > 0) of the export overlap the silhouette of the source (every pixel not the matte color) by at least min_iou."""
    p, err = _need(scratch, rule["file"])
    src = pathlib.Path(scratch) / rule["source"]
    if err or not src.is_file():
        return R.add(rule["id"], False, err or f"missing source {rule['source']}", rule["min_iou"])
    a, s = load(p), load(src)
    box = rule.get("source_box")
    if box:
        x, y, w, h = box
        s = s[y:y + h, x:x + w]
    if a.shape[:2] != s.shape[:2]:
        return R.add(rule["id"], False, f"size {a.shape[1]}x{a.shape[0]} vs source {s.shape[1]}x{s.shape[0]}", rule["min_iou"])
    m = np.array(hexcolor(rule["matte"]))
    want = np.abs(s[..., :3].astype(int) - m).max(axis=2) > 0
    got = a[..., 3] > 0
    union = int((want | got).sum())
    iou = int((want & got).sum()) / union if union else 0.0
    R.add(rule["id"], iou >= rule["min_iou"], round(iou, 4), rule["min_iou"])


def r_border_transparent(R, scratch, rule):
    p, err = _need(scratch, rule["file"])
    if err:
        return R.add(rule["id"], False, err, "all border pixels transparent")
    al = load(p)[..., 3]
    edge = np.concatenate([al[0], al[-1], al[:, 0], al[:, -1]])
    frac = float((al == 0).mean())
    ok = (bool((edge == 0).all()) or not rule.get("require_border", True)) and frac >= rule.get("min_transparent_fraction", 0.0)
    R.add(rule["id"], ok, {"border_opaque": int((edge > 0).sum()), "transparent_fraction": round(frac, 3)}, {"border_opaque": 0, "min_transparent_fraction": rule.get("min_transparent_fraction", 0.0)})


def r_outside_mask_unchanged(R, scratch, rule):
    p, err = _need(scratch, rule["file"])
    prev = pathlib.Path(scratch) / rule["previous"]
    mask = pathlib.Path(scratch) / rule["mask"]
    if err or not prev.is_file() or not mask.is_file():
        return R.add(rule["id"], False, err or "missing previous version or mask", 0)
    a, b, m = load(p), load(prev), load(mask)
    if a.shape != b.shape or a.shape[:2] != m.shape[:2]:
        return R.add(rule["id"], False, "size differs from the previous version or the mask", 0)
    inside = m[..., :3].max(axis=2) > 127
    diff = (a != b).any(axis=2) & ~inside
    R.add(rule["id"], not diff.any(), int(diff.sum()), 0)


def r_inside_mask_hue(R, scratch, rule):
    """At least min_fraction of the opaque pixels inside the mask are red-ish (hue within `hue_range` degrees)."""
    import colorsys
    p, err = _need(scratch, rule["file"])
    mask = pathlib.Path(scratch) / rule["mask"]
    if err or not mask.is_file():
        return R.add(rule["id"], False, err or "missing mask", rule["min_fraction"])
    a, m = load(p), load(mask)
    if a.shape[:2] != m.shape[:2]:
        return R.add(rule["id"], False, "size differs from the mask", rule["min_fraction"])
    inside = (m[..., :3].max(axis=2) > 127) & (a[..., 3] == 255)
    lo, hi = rule["hue_range"]
    n = hit = 0
    for r, g, b, _ in a[inside]:
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        deg = h * 360
        n += 1
        hit += int(s >= 0.4 and v >= 0.3 and (deg >= lo or deg <= hi) if lo > hi else s >= 0.4 and v >= 0.3 and lo <= deg <= hi)
    frac = hit / n if n else 0.0
    R.add(rule["id"], n > 0 and frac >= rule["min_fraction"], round(frac, 3), rule["min_fraction"])


def r_manifest_valid(R, scratch, rule):
    mp = pathlib.Path(scratch) / rule.get("manifest", "assets/MANIFEST.json")
    if not mp.is_file():
        return R.add(rule["id"], False, "missing " + str(rule.get("manifest", "assets/MANIFEST.json")), "valid manifest")
    try:
        m = json.loads(mp.read_text())
    except Exception as e:  # noqa: BLE001
        return R.add(rule["id"], False, f"not JSON: {e}", "valid manifest")
    errs = _vm.validate(m, root=scratch, exports=rule.get("exports", "assets"), import_paths=rule.get("import_paths", []))
    R.add(rule["id"], not errs, [f"{p}: {msg}" for p, msg in errs][:4] or "valid", "valid manifest, every file has a row, no master in the import path")


def r_manifest_rows(R, scratch, rule):
    """Each listed file has a row; `fields` lists field values that must equal what is given (for a row that names a file)."""
    mp = pathlib.Path(scratch) / rule.get("manifest", "assets/MANIFEST.json")
    try:
        rows = {r["file"]: r for r in json.loads(mp.read_text())["assets"]}
    except Exception as e:  # noqa: BLE001
        return R.add(rule["id"], False, f"unreadable manifest: {e}", rule["files"])
    missing = [f for f in rule["files"] if f not in rows]
    R.add(rule["id"], not missing, ("no row for: %s" % missing) if missing else "all listed files have a row", rule["files"])


def r_models_allowed(R, scratch, rule):
    """No manifest row names a model in `forbidden`; every row that names a model records its weights license."""
    mp = pathlib.Path(scratch) / rule.get("manifest", "assets/MANIFEST.json")
    try:
        rows = json.loads(mp.read_text())["assets"]
    except Exception as e:  # noqa: BLE001
        return R.add(rule["id"], False, f"unreadable manifest: {e}", "no forbidden model")
    bad = []
    for r in rows:
        mo = (r.get("model") or "")
        if mo and any(f.lower() in mo.lower() for f in rule["forbidden"]):
            bad.append(r.get("file"))
        if mo and not (r.get("weights_license") or "").strip():
            bad.append(r.get("file"))
        for name, phrases in (rule.get("license_contains") or {}).items():
            if name.lower() in mo.lower() and not all(ph.lower() in (r.get("weights_license") or "").lower() for ph in phrases):
                bad.append(r.get("file"))
    R.add(rule["id"], not bad, ("rows that use a forbidden model or omit the weights license: %s" % sorted(set(bad))) if bad else "none", "no forbidden model, weights license recorded")


def r_composite_equals(R, scratch, rule):
    """The export equals the layers in `layers` (bottom to top) alpha-composited, pixel for pixel."""
    p, err = _need(scratch, rule["file"])
    if err:
        return R.add(rule["id"], False, err, "equals the composite of the layers")
    base = None
    for name in rule["layers"]:
        with Image.open(pathlib.Path(scratch) / name) as im:
            layer = im.convert("RGBA")
        base = layer if base is None else Image.alpha_composite(base, layer)
    want, got = np.array(base), load(p)
    if want.shape != got.shape:
        return R.add(rule["id"], False, f"size {got.shape[1]}x{got.shape[0]}, composite is {want.shape[1]}x{want.shape[0]}", "equals the composite of the layers")
    same = (want[..., 3] == got[..., 3]) & ((want[..., 3] == 0) | (want[..., :3] == got[..., :3]).all(axis=2))
    R.add(rule["id"], bool(same.all()), int((~same).sum()), 0)


def r_alpha_equals(R, scratch, rule):
    """The export's alpha channel equals the source's (same silhouette, nothing cut or filled)."""
    p, err = _need(scratch, rule["file"])
    src = pathlib.Path(scratch) / rule["source"]
    if err or not src.is_file():
        return R.add(rule["id"], False, err or f"missing source {rule['source']}", 0)
    a, s = load(p), load(src)
    if a.shape[:2] != s.shape[:2]:
        return R.add(rule["id"], False, "size differs from the source", 0)
    R.add(rule["id"], bool((a[..., 3] == s[..., 3]).all()), int((a[..., 3] != s[..., 3]).sum()), 0)


def r_equals_source(R, scratch, rule):
    """Opaque pixels and alpha equal the source (or the box of it), so a plain export did not change the art."""
    p, err = _need(scratch, rule["file"])
    src = pathlib.Path(scratch) / rule["source"]
    if err or not src.is_file():
        return R.add(rule["id"], False, err or f"missing source {rule['source']}", 0)
    a, s = load(p), load(src)
    box = rule.get("source_box")
    if box:
        x, y, w, h = box
        s = s[y:y + h, x:x + w]
    if a.shape != s.shape:
        return R.add(rule["id"], False, f"size {a.shape[1]}x{a.shape[0]} vs source {s.shape[1]}x{s.shape[0]}", 0)
    same = (a[..., 3] == s[..., 3]) & ((s[..., 3] == 0) | (a[..., :3] == s[..., :3]).all(axis=2))
    R.add(rule["id"], bool(same.all()), int((~same).sum()), 0)


def r_mask_color(R, scratch, rule):
    """Every opaque pixel inside the mask is exactly `color`."""
    p, err = _need(scratch, rule["file"])
    mask = pathlib.Path(scratch) / rule["mask"]
    if err or not mask.is_file():
        return R.add(rule["id"], False, err or "missing mask", rule["color"])
    a, m = load(p), load(mask)
    if a.shape[:2] != m.shape[:2]:
        return R.add(rule["id"], False, "size differs from the mask", rule["color"])
    inside = (m[..., :3].max(axis=2) > 127) & (a[..., 3] == 255)
    want = np.array(hexcolor(rule["color"]))
    bad = int((a[inside][:, :3] != want).any(axis=1).sum())
    R.add(rule["id"], inside.any() and bad == 0, bad, 0)


def r_distinct_colors(R, scratch, rule):
    p, err = _need(scratch, rule["file"])
    if err:
        return R.add(rule["id"], False, err, rule["min_colors"])
    a = load(p)
    opaque = a[a[..., 3] == 255][:, :3]
    n = len(np.unique(opaque, axis=0)) if len(opaque) else 0
    frac = float((a[..., 3] > 0).mean())
    R.add(rule["id"], n >= rule["min_colors"] and frac >= rule.get("min_opaque_fraction", 0.0), {"colors": n, "opaque_fraction": round(frac, 3)}, {"min_colors": rule["min_colors"], "min_opaque_fraction": rule.get("min_opaque_fraction", 0.0)})


def r_model_license_recorded(R, scratch, rule):
    """At least one row names the required model and its weights license contains each required phrase."""
    mp = pathlib.Path(scratch) / rule.get("manifest", "assets/MANIFEST.json")
    try:
        rows = json.loads(mp.read_text())["assets"]
    except Exception as e:  # noqa: BLE001
        return R.add(rule["id"], False, f"unreadable manifest: {e}", rule["model"])
    ok = any(rule["model"].lower() in (r.get("model") or "").lower() and all(ph.lower() in (r.get("weights_license") or "").lower() for ph in rule["license_contains"]) for r in rows)
    R.add(rule["id"], ok, "found" if ok else "no row names the model with its license", {"model": rule["model"], "license_contains": rule["license_contains"]})


def r_masters_outside_import_path(R, scratch, rule):
    imp = [x.strip("/") for x in rule["import_paths"]]
    bad = []
    root = pathlib.Path(scratch)
    for ip in imp:
        d = root / ip
        if d.is_dir():
            for f in d.rglob("*"):
                if f.is_file() and f.suffix.lower() in MASTER_SUFFIXES:
                    bad.append(f.relative_to(root).as_posix())
    R.add(rule["id"], not bad, bad[:6] or "none", "no editable master under " + ", ".join(imp))


def r_masters_exist(R, scratch, rule):
    """The manifest names a master for each listed file, outside the import path, and it exists."""
    mp = pathlib.Path(scratch) / rule.get("manifest", "assets/MANIFEST.json")
    try:
        rows = {r["file"]: r for r in json.loads(mp.read_text())["assets"]}
    except Exception as e:  # noqa: BLE001
        return R.add(rule["id"], False, f"unreadable manifest: {e}", rule["files"])
    bad = []
    for f in rule["files"]:
        m = (rows.get(f) or {}).get("master")
        if not m or not (pathlib.Path(scratch) / m).is_file() or any(m == ip.strip("/") or m.startswith(ip.strip("/") + "/") for ip in rule["import_paths"]):
            bad.append(f)
    R.add(rule["id"], not bad, ("no usable master for: %s" % bad) if bad else "every listed file has a master outside the import path", rule["files"])


def r_rebuild_identical(R, scratch, rule):
    """Delete the listed exports in a copy of the scratch tree, run each one's build_script there (network off is the sandbox's job), and require the same bytes."""
    root = pathlib.Path(scratch)
    try:
        rows = {r["file"]: r for r in json.loads((root / rule.get("manifest", "assets/MANIFEST.json")).read_text())["assets"]}
    except Exception as e:  # noqa: BLE001
        return R.add(rule["id"], False, f"unreadable manifest: {e}", "identical bytes")
    scripts = sorted({rows[f].get("build_script") for f in rule["files"] if f in rows and rows[f].get("build_script")})
    if not scripts or any(f not in rows or not rows[f].get("build_script") for f in rule["files"]):
        return R.add(rule["id"], False, "no build_script recorded for every listed file", "identical bytes")
    with tempfile.TemporaryDirectory() as d:
        w = pathlib.Path(d) / "tree"
        shutil.copytree(root, w, ignore=shutil.ignore_patterns("__pycache__"))
        before = {f: sha(w / f) for f in rule["files"] if (w / f).is_file()}
        for f in rule["files"]:
            (w / f).unlink(missing_ok=True)
        for s in scripts:
            sp = w / s
            if not sp.is_file():
                return R.add(rule["id"], False, f"build script {s} does not exist", "identical bytes")
            cmd = ["bash", s] if sp.suffix in ("", ".sh") else [sys.executable, s]
            try:
                r = subprocess.run(cmd, cwd=w, capture_output=True, text=True, timeout=rule.get("timeout", 120), env={"PATH": os.environ.get("PATH", ""), "HOME": d, "PYTHONDONTWRITEBYTECODE": "1"})
            except subprocess.TimeoutExpired:
                return R.add(rule["id"], False, f"{s} timed out", "identical bytes")
            if r.returncode != 0:
                return R.add(rule["id"], False, f"{s} exited {r.returncode}: {r.stderr.strip()[-160:]}", "identical bytes")
        after = {f: (sha(w / f) if (w / f).is_file() else None) for f in rule["files"]}
    bad = [f for f in rule["files"] if before.get(f) != after.get(f)]
    R.add(rule["id"], not bad, ("not reproduced identically: %s" % bad) if bad else "identical", "identical bytes")


TYPES = {k[2:]: v for k, v in globals().items() if k.startswith("r_")}


def run_case(scratch, expected_path):
    exp = json.loads(pathlib.Path(expected_path).read_text())
    R = Rules(exp["case"])
    for rule in exp["rules"]:
        fn = TYPES.get(rule["type"])
        if fn is None:
            R.add(rule["id"], False, "unknown rule type " + rule["type"], None)
            continue
        try:
            fn(R, scratch, rule)
        except Exception as e:  # noqa: BLE001
            R.add(rule["id"], False, f"checker error: {type(e).__name__}: {e}", None)
    return R.out()


def main(argv):
    if len(argv) != 3:
        print(__doc__)
        return 2
    out = run_case(argv[1], argv[2])
    print(json.dumps(out, indent=2))
    return 0 if all(r["pass"] for r in out["rules"]) else 1
