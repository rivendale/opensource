"""Phone-profile rules for the game-prototype items 7 to 11. Each rule runs lib/web_probe.mjs (headless Chrome, touch events only, the device profile applied before
navigation) on the project directory and judges its measurements. Needs node, puppeteer-core (STUDIO_NODE_MODULES) and Chrome for Testing 150 (STUDIO_CHROME)."""
import json, os, pathlib, subprocess, tempfile

HERE = pathlib.Path(__file__).resolve().parent
NODE = os.environ.get("STUDIO_NODE") or "node"
_cache = {}


def probe(scratch, rule):
    key = (str(scratch), json.dumps(rule.get("spec"), sort_keys=True))
    if key not in _cache:
        with tempfile.TemporaryDirectory() as d:
            sp = pathlib.Path(d) / "spec.json"
            sp.write_text(json.dumps(rule["spec"]))
            r = subprocess.run([NODE, str(HERE / "web_probe.mjs"), str(pathlib.Path(scratch).resolve()), str(sp)], capture_output=True, text=True, timeout=120)
        if r.returncode:
            raise RuntimeError("probe failed: " + r.stderr.strip()[-300:])
        _cache[key] = json.loads(r.stdout.strip().splitlines()[-1])
    return _cache[key]


def r_web_touch_actions(R, scratch, rule):
    """Item 7: with touch events only (no key is ever sent), tapping the control for each action in the brief makes its observable appear."""
    o = probe(scratch, rule)
    taps = o.get("taps", {})
    missing = [a for a in rule["spec"]["actions"] if not taps.get(a)]
    R.add(rule["id"], not missing, {"not_done_by_touch": missing or None, "taps": taps}, "every core-loop action observable by touch")


def _all_controls(o):
    for name, p in o["profiles"].items():
        for c in p["controls"]:
            yield name, c
    for c in o.get("rotated", []):
        yield "rotated 390x844 -> 844x390", c


def r_web_controls_visible(R, scratch, rule):
    """Item 8: every control is found and shown in the 390x844, 844x390, 1194x834 and 1280x720 coarse-pointer profiles and after a rotation without reload."""
    o = probe(scratch, rule)
    bad = sorted({f"{c['name']}@{p}" for p, c in _all_controls(o) if not (c["found"] and c["shown"])})
    coarse = [p for p, v in o["profiles"].items() if not v["coarse"]]
    R.add(rule["id"], not bad and not coarse, {"missing_or_hidden": bad or None, "profiles_not_coarse": coarse or None}, "visible in all four profiles and after rotation")


def r_web_targets(R, scratch, rule):
    """Item 9: each control is at least 44x44 CSS px, inside the viewport, and uncovered at its center and four points inset 4 px (control.contains(hit))."""
    o = probe(scratch, rule)
    small, off, covered = set(), set(), set()
    for p, c in _all_controls(o):
        if not (c["found"] and c["shown"]):
            continue          # item 8's finding, not item 9's
        tag = f"{c['name']}@{p}"
        if c["w"] < 44 or c["h"] < 44:
            small.add(f"{tag} {c['w']}x{c['h']}")
        if not c["inside"]:
            off.add(tag)
        if c["covered_points"]:
            covered.add(f"{tag} ({c['covered_points']} of 5 points)")
    R.add(rule["id"], not (small or off or covered), {"under_44px": sorted(small) or None, "outside_viewport": sorted(off) or None, "covered": sorted(covered) or None}, "44x44, inside the viewport, uncovered")


def r_web_hints(R, scratch, rule):
    """Item 10: no visible text names a keyboard or mouse action unless touch wording is in the same element or the one beside it."""
    o = probe(scratch, rule)
    R.add(rule["id"], not o.get("hints"), {"keyboard_only_hints": o.get("hints") or None}, "no keyboard/mouse-only hint on a touch profile")


def r_web_page_stable(R, scratch, rule):
    """Item 11: after a one-finger drag and a two-finger pinch on the play surface, scroll position and visualViewport.scale are unchanged."""
    o = probe(scratch, rule)
    s = o.get("page_stable") or {}
    if "error" in s or not s:
        return R.add(rule["id"], False, s.get("error", "no measurement"), "page unchanged by a drag and a pinch")
    b, d, p = s["before"], s["afterDrag"], s["afterPinch"]
    moved = (d["x"], d["y"]) != (b["x"], b["y"]) or (p["x"], p["y"]) != (b["x"], b["y"])
    zoomed = abs(p["s"] - b["s"]) > 0.01 or abs(d["s"] - b["s"]) > 0.01
    R.add(rule["id"], not moved and not zoomed, {"scrolled": moved, "scale": [b["s"], p["s"]]}, "scroll and scale unchanged")


def r_web_zoom_not_blocked(R, scratch, rule):
    """Item 11, second half: the page does not block zoom (no maximum-scale=1 or user-scalable=no): WCAG 1.4.4."""
    import re
    o = probe(scratch, rule)
    m = (o.get("viewport_meta") or "").lower().replace(" ", "")
    locked = bool(re.search(r"user-scalable=(no|0)", m)) or bool(re.search(r"maximum-scale=(1|1\.0|0\.\d+)(,|$)", m))
    R.add(rule["id"], not locked, o.get("viewport_meta"), "zoom not blocked")


def r_web_two_thumbs(R, scratch, rule):
    """Item 12: hold the movement control with one touch point and tap the action with a second; the action's observable appears and the movement does not stop."""
    o = probe(scratch, rule)
    s = o.get("two_thumbs") or {}
    if "error" in s or not s:
        return R.add(rule["id"], False, s.get("error", "no measurement"), "action done while movement is held")
    ok = s["moved_before"] and s["action_logged"] and s["moved_after"]
    R.add(rule["id"], ok, {k: s[k] for k in ("moved_before", "action_logged", "moved_after")} | {"player_x": s["x"]}, "movement continues and the action registers")


def r_web_long_press(R, scratch, rule):
    """Item 13: no core-loop control can be selected by a long press (effective user-select none), and a control that is or holds a link or an image default-prevents the contextmenu."""
    o = probe(scratch, rule)
    bad = []
    for c in o.get("long_press") or []:
        if not c["found"]:
            bad.append(c["name"] + ": no control found")
        elif c["has_text"] and c["user_select"] != "none":
            bad.append(f"{c['name']}: text is selectable (user-select {c['user_select']})")
        elif c["link_or_image"] and c["contextmenu_default_runs"]:
            bad.append(f"{c['name']}: a link or image opens the browser menu")
    R.add(rule["id"], not bad and bool(o.get("long_press")), {"problems": bad or None}, "no selection and no browser menu from a long press")


def r_web_safe_area(R, scratch, rule):
    """Item 14: with insets top 47, bottom 34 applied at load, each control lies inside the viewport minus the insets; a page with viewport-fit=cover uses env(safe-area-inset-*) somewhere in its files."""
    o = probe(scratch, rule)
    s = o.get("safe_area") or {}
    ins, W, H = s.get("insets", {}), 390, 844
    bad = []
    for c in s.get("controls", []):
        if not (c["found"] and c["shown"]):
            continue
        l, t, r, b = c["rect"]
        if t < ins["top"] or b > H - ins["bottom"] or l < ins["left"] or r > W - ins["right"]:
            bad.append(f"{c['name']} {c['rect']}")
    cover = "viewport-fit=cover" in (s.get("viewport_meta") or "").replace(" ", "")
    if not cover:
        bad = []          # without viewport-fit=cover the browser already keeps the layout viewport inside the safe area; nothing to measure
    no_env = cover and not s.get("source_uses_env")
    R.add(rule["id"], not bad and not no_env, {"outside_safe_area": bad or None, "viewport_fit_cover_without_env": no_env or None}, "inside the safe area; env() used with viewport-fit=cover")


RULES = {k[2:]: v for k, v in globals().items() if k.startswith("r_")}
