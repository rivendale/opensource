#!/usr/bin/env python3
"""Writes evals/studio/game-art/cases/<case>/ (brief.md, inputs/, expected.json, check.py) and holds, for each case, a reference solution and the
defective outputs a careless skill would produce, so selfcheck.py can show that every checker passes the first and fails each of the others.

    python3 evals/studio/game-art/build/make_cases.py        rewrite the case directories
"""
import json, os, pathlib, shutil, stat, sys, textwrap

import numpy as np
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import drawing as D

HERE = pathlib.Path(__file__).resolve().parent
CASES_DIR = HERE.parent / "cases"
LAYOUT = textwrap.dedent("""\
    Project layout (the same in every brief): the engine imports from `assets/`. Put exports in `assets/`, editable masters in `masters/`, rebuild
    scripts in `tools/` (a script is run from the project root), and the manifest at `assets/MANIFEST.json` (see `skills/studio/manifest.schema.json`). Inputs are in `inputs/` and are read-only.
    """)
CHECK_PY = '''#!/usr/bin/env python3
"""Checker for this case. Run as: check.py SCRATCH_DIR EXPECTED_JSON (after the agent has exited). The measurements are in evals/studio/lib/studio_lib.py."""
import os, pathlib, sys
sys.path.insert(0, os.environ.get("STUDIO_LIB") or str(pathlib.Path(__file__).resolve().parents[3] / "lib"))
import studio_lib
sys.exit(studio_lib.main([sys.argv[0]] + sys.argv[1:]))
'''
CASES = []


def case(cid, item, kind, brief, inputs, rules, reference, defects=(), tools=("python3", "pillow")):
    CASES.append(dict(id=cid, item=item, kind=kind, brief=brief, inputs=inputs, rules=rules, reference=reference, defects=list(defects), tools=list(tools)))


def img(a):
    return ("png", a)


def row(file, kind="sprite", master=None, build_script=None, **kw):
    r = dict(file=file, kind=kind, tool="python3 + Pillow", tool_version="3.12 / 12.3", seed_or_params="hand-drawn script", date="2026-10-10", model=None, weights_license=None,
             source=None, source_license=None, reference_used_as="none", master=master, build_script=build_script, paid_service=None)
    r.update(kw)
    return r


def write_png(root, rel, a):
    p = pathlib.Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    D.save(a, p)


def write_manifest(root, rows, rel="assets/MANIFEST.json"):
    p = pathlib.Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"manifest_version": 1, "assets": rows}, indent=2) + "\n")


def manifest_rules(files, rid="manifest"):
    return [{"id": rid + "_valid", "type": "manifest_valid", "import_paths": ["assets"]}, {"id": rid + "_rows", "type": "manifest_rows", "files": files}]


def ensure(root, rel, text):
    p = pathlib.Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def copy_inputs(root, case):
    for rel, v in case["inputs"].items():
        p = pathlib.Path(root) / "inputs" / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(v, tuple) and v[0] == "png":
            D.save(v[1], p)
        elif isinstance(v, tuple) and v[0] == "exec":
            p.write_text(v[1]); p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        else:
            p.write_text(v)


# ============================================================================================ art 1: size, frames, palette, grid
CRATE = D.upscale(D.crate16(), 4)
PAL = "\n".join(D.PALETTE) + "\n"


def ref_crate(root):
    write_png(root, "assets/tiles/crate.png", D.crate16())
    write_manifest(root, [row("assets/tiles/crate.png", "tile", master="inputs/crate.png")])


def bad_crate_blur(root):
    im = Image.open(pathlib.Path(root) / "inputs/crate.png").convert("RGBA").resize((16, 16), Image.BILINEAR)
    D.save(np.array(im), pathlib.Path(root) / "assets/tiles/crate.png")


def bad_crate_wrongsize(root):
    D.save(D.crate16()[:, :15].copy().repeat(1, 0), pathlib.Path(root) / "assets/tiles/crate.png")


def bad_crate_offpalette(root):
    a = D.crate16(); a[2, 2, :3] = (200, 30, 30)
    D.save(a, pathlib.Path(root) / "assets/tiles/crate.png")


case("art-1a-palette-locked-downscale", "art-1", "M",
     "The engine's tile size is 16x16. Make `assets/tiles/crate.png` the 16x16 version of `inputs/crate.png` (64x64), using only the colors in `inputs/palette.hex`. The edges must stay\n"
     "crisp: no blur, no new colors. Record it in the manifest.\n",
     {"crate.png": img(CRATE), "palette.hex": PAL},
     [{"id": "size", "type": "size_exact", "file": "assets/tiles/crate.png", "width": 16, "height": 16},
      {"id": "palette", "type": "palette_only", "file": "assets/tiles/crate.png", "palette": "inputs/palette.hex"},
      {"id": "faithful", "type": "matches_blocks", "file": "assets/tiles/crate.png", "source": "inputs/crate.png", "factor": 4, "min_fraction": 0.95}]
     + manifest_rules(["assets/tiles/crate.png"]),
     ref_crate, [("blurred downscale", bad_crate_blur, {"palette", "faithful"}), ("wrong size", bad_crate_wrongsize, {"size", "faithful"}), ("one off-palette pixel", bad_crate_offpalette, {"palette"})])

BALLS = {f"frame_{i}.png": img(D.numbered_frame(i)) for i in range(1, 7)}


def strip_cells(root, order, cw=32, ch=32, cols=6, rows=1, srcdir="inputs", names=None):
    sheet = np.zeros((ch * rows, cw * cols, 4), np.uint8)
    for k, i in enumerate(order):
        s = np.array(Image.open(pathlib.Path(root) / srcdir / f"frame_{i}.png").convert("RGBA"))
        r, c = divmod(k, cols)
        sheet[r * ch:r * ch + s.shape[0], c * cw:c * cw + s.shape[1]] = s
    return sheet


def ref_strip6(root):
    write_png(root, "assets/sprites/ball_roll.png", strip_cells(root, range(1, 7)))
    write_manifest(root, [row("assets/sprites/ball_roll.png", master="inputs/frame_1.png")])


def bad_strip_five(root):
    write_png(root, "assets/sprites/ball_roll.png", strip_cells(root, range(1, 6), cols=6))
    write_manifest(root, [row("assets/sprites/ball_roll.png", master="inputs/frame_1.png")])


def bad_strip_two_rows(root):
    write_png(root, "assets/sprites/ball_roll.png", strip_cells(root, range(1, 7), cols=3, rows=2))
    write_manifest(root, [row("assets/sprites/ball_roll.png", master="inputs/frame_1.png")])


case("art-1b-six-frame-strip", "art-1", "M",
     "Pack the six frames `inputs/frame_1.png` to `inputs/frame_6.png` into one horizontal strip, `assets/sprites/ball_roll.png`: 6 columns by 1 row, 32x32 per frame. Record it in the manifest.\n",
     BALLS,
     [{"id": "size", "type": "size_exact", "file": "assets/sprites/ball_roll.png", "width": 192, "height": 32},
      {"id": "six_frames", "type": "cells_nonempty", "file": "assets/sprites/ball_roll.png", "cell_width": 32, "cell_height": 32, "cols": 6, "rows": 1, "count": 6}]
     + manifest_rules(["assets/sprites/ball_roll.png"]),
     ref_strip6, [("five frames", bad_strip_five, {"six_frames"}), ("two rows of three", bad_strip_two_rows, {"size", "six_frames"})])

# ============================================================================================ art 2: transparency
HERO_M = D.hero_on_matte()
HERO_SRC = "inputs/hero_matte.png"


def keyed(root, tol, feather):
    a = np.array(Image.open(pathlib.Path(root) / HERO_SRC).convert("RGBA")).astype(int)
    m = np.array(D.rgb(D.MAGENTA))
    dist = np.abs(a[..., :3] - m).max(axis=2)
    out = a.copy()
    out[dist <= tol, 3] = 0
    if feather:
        edge = (out[..., 3] == 255) & _near(out[..., 3] == 0)
        out[edge, 3] = 128
    return out.astype(np.uint8)


def _near(t):
    t = np.pad(t, 1, constant_values=False)
    h, w = t.shape[0] - 2, t.shape[1] - 2
    n = np.zeros((h, w), bool)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            n |= t[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
    return n


def ref_hero_keyed(root):
    write_png(root, "assets/sprites/hero.png", keyed(root, 0, True))
    write_manifest(root, [row("assets/sprites/hero.png", master="inputs/hero_matte.png")])


def bad_hero_opaque(root):
    write_png(root, "assets/sprites/hero.png", np.array(Image.open(pathlib.Path(root) / HERO_SRC).convert("RGBA")))
    write_manifest(root, [row("assets/sprites/hero.png", master="inputs/hero_matte.png")])


def bad_hero_fringe(root):
    a = keyed(root, 0, False)
    a[~_near(a[..., 3] == 0) & False] = 0
    near = _near(a[..., 3] == 0) & (a[..., 3] == 255)
    a[near, :3] = D.rgb(D.MAGENTA)           # a matte-colored rim left on the edge
    write_png(root, "assets/sprites/hero.png", a)
    write_manifest(root, [row("assets/sprites/hero.png", master="inputs/hero_matte.png")])


def bad_hero_overkeyed(root):
    a = np.array(Image.open(pathlib.Path(root) / HERO_SRC).convert("RGBA")).astype(int)
    import colorsys
    out = a.copy()
    for y in range(32):
        for x in range(32):
            h, s, v = colorsys.rgb_to_hsv(*(a[y, x, :3] / 255))
            if s > 0.3 and 270 <= h * 360 <= 350:
                out[y, x, 3] = 0
    write_png(root, "assets/sprites/hero.png", out.astype(np.uint8))
    write_manifest(root, [row("assets/sprites/hero.png", master="inputs/hero_matte.png")])


case("art-2a-magenta-matte", "art-2", "M",
     "`inputs/hero_matte.png` is a 32x32 character on a solid magenta (ff00ff) background. Cut the character out and export `assets/sprites/hero.png` with a transparent background on\n"
     "the same 32x32 canvas. Keep every pixel of the character. Record it in the manifest.\n",
     {"hero_matte.png": img(HERO_M)},
     [{"id": "size", "type": "size_exact", "file": "assets/sprites/hero.png", "width": 32, "height": 32},
      {"id": "no_matte", "type": "matte_clean", "file": "assets/sprites/hero.png", "matte": D.MAGENTA, "tolerance": 0},
      {"id": "edge_only", "type": "partial_alpha_edge_only", "file": "assets/sprites/hero.png"},
      {"id": "silhouette", "type": "silhouette", "file": "assets/sprites/hero.png", "source": "inputs/hero_matte.png", "matte": D.MAGENTA, "min_iou": 0.97}]
     + manifest_rules(["assets/sprites/hero.png"]),
     ref_hero_keyed, [("still opaque", bad_hero_opaque, {"no_matte", "silhouette"}), ("matte-colored rim", bad_hero_fringe, {"no_matte"}), ("keyed out the pink scarf", bad_hero_overkeyed, {"silhouette"})])

ICON_SHEET = D.icons_on_white()
ICON_NAMES = ["sword", "shield", "potion", "key"]
ICON_BOX = {n: [(k % 2) * 32, (k // 2) * 32, 32, 32] for k, n in enumerate(ICON_NAMES)}


def icon_from_sheet(root, k, tol=0):
    a = np.array(Image.open(pathlib.Path(root) / "inputs/icons_white.png").convert("RGBA")).astype(int)
    x, y = (k % 2) * 32, (k // 2) * 32
    c = a[y:y + 32, x:x + 32].copy()
    dist = np.abs(c[..., :3] - 255).max(axis=2)
    c[dist <= tol, 3] = 0
    return c.astype(np.uint8)


def ref_icons(root):
    for k, n in enumerate(ICON_NAMES):
        write_png(root, f"assets/ui/icon_{n}.png", icon_from_sheet(root, k))
    write_manifest(root, [row(f"assets/ui/icon_{n}.png", "icon", master="inputs/icons_white.png") for n in ICON_NAMES])


def bad_icons_white(root):
    for k, n in enumerate(ICON_NAMES):
        a = np.array(Image.open(pathlib.Path(root) / "inputs/icons_white.png").convert("RGBA"))
        x, y = (k % 2) * 32, (k // 2) * 32
        write_png(root, f"assets/ui/icon_{n}.png", a[y:y + 32, x:x + 32].copy())
    write_manifest(root, [row(f"assets/ui/icon_{n}.png", "icon", master="inputs/icons_white.png") for n in ICON_NAMES])


def bad_icons_shine_lost(root):
    for k, n in enumerate(ICON_NAMES):
        write_png(root, f"assets/ui/icon_{n}.png", icon_from_sheet(root, k, tol=20))
    write_manifest(root, [row(f"assets/ui/icon_{n}.png", "icon", master="inputs/icons_white.png") for n in ICON_NAMES])


def bad_icons_order(root):
    order = [1, 0, 2, 3]
    for k, n in enumerate(ICON_NAMES):
        write_png(root, f"assets/ui/icon_{n}.png", icon_from_sheet(root, order[k]))
    write_manifest(root, [row(f"assets/ui/icon_{n}.png", "icon", master="inputs/icons_white.png") for n in ICON_NAMES])


icon_rules = []
for _n in ICON_NAMES:
    f = f"assets/ui/icon_{_n}.png"
    icon_rules += [{"id": f"{_n}_size", "type": "size_exact", "file": f, "width": 32, "height": 32},
                   {"id": f"{_n}_transparent", "type": "border_transparent", "file": f, "min_transparent_fraction": 0.3},
                   {"id": f"{_n}_no_white", "type": "matte_clean", "file": f, "matte": D.WHITE, "tolerance": 0},
                   {"id": f"{_n}_silhouette", "type": "silhouette", "file": f, "source": "inputs/icons_white.png", "source_box": ICON_BOX[_n], "matte": D.WHITE, "min_iou": 0.97}]
case("art-2b-icons-on-white", "art-2", "M",
     "`inputs/icons_white.png` is a 64x64 sheet of four icons on a white background, in reading order: sword, shield, potion, key. Split it into four 32x32 icons,\n"
     "`assets/ui/icon_sword.png`, `icon_shield.png`, `icon_potion.png` and `icon_key.png`, each with a transparent background. Record them in the manifest.\n",
     {"icons_white.png": img(ICON_SHEET)},
     icon_rules + manifest_rules([f"assets/ui/icon_{n}.png" for n in ICON_NAMES]),
     ref_icons, [("white left in", bad_icons_white, {f"{n}_{r}" for n in ICON_NAMES for r in ("transparent", "no_white", "silhouette")}), ("shine keyed out with the white", bad_icons_shine_lost, {f"{n}_silhouette" for n in ICON_NAMES}), ("shield and sword swapped", bad_icons_order, {"sword_silhouette", "shield_silhouette"})])

# ============================================================================================ art 3: sheets
WALK = {f"frame_{i}.png": img(D.numbered_frame(i)) for i in range(1, 13)}


def ref_walk(root, order=None):
    order = order or list(range(1, 13))
    write_png(root, "assets/sprites/walk.png", strip_cells(root, order, cols=6, rows=2))
    write_manifest(root, [row("assets/sprites/walk.png", master="inputs/frame_1.png")])


def bad_walk_lex(root):
    ref_walk(root, sorted(range(1, 13), key=str))


def bad_walk_dropped(root):
    ref_walk(root, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 11])


walk_src = [f"inputs/frame_{i}.png" for i in range(1, 13)]
case("art-3a-numeric-frame-order", "art-3", "M",
     "Pack the twelve walk frames `inputs/frame_1.png` to `inputs/frame_12.png` into one sheet, `assets/sprites/walk.png`: 6 columns by 2 rows, 32x32 per frame, in numeric\n"
     "order (1 first, 12 last), left to right, top to bottom. Do not change the frames. Record it in the manifest.\n",
     WALK,
     [{"id": "order", "type": "cells_equal_sources", "file": "assets/sprites/walk.png", "cell_width": 32, "cell_height": 32, "cols": 6, "rows": 2, "sources": walk_src}]
     + manifest_rules(["assets/sprites/walk.png"]),
     ref_walk, [("sorted as text (1, 10, 11, 12, 2, ...)", bad_walk_lex, {"order"}), ("frame 11 twice, 12 missing", bad_walk_dropped, {"order"})])

RUN = {f"frame_{i}.png": img(D.varied_frame(i)) for i in range(1, 9)}


def place(root, mode):
    sheet = np.zeros((64, 128, 4), np.uint8)
    for i in range(1, 9):
        s = np.array(Image.open(pathlib.Path(root) / f"inputs/frame_{i}.png").convert("RGBA"))
        ys, xs = np.nonzero(s[..., 3] > 0)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        fig = s[y0:y1 + 1, x0:x1 + 1]
        h, w = fig.shape[:2]
        r, c = divmod(i - 1, 4)
        if mode == "aligned":
            ox, oy = c * 32 + (32 - w) // 2, r * 32 + 31 - h
        elif mode == "top-left":                      # figures at the top left of the cell: feet at different rows
            ox, oy = c * 32, r * 32
        elif mode == "scaled":                        # each figure stretched to fill the cell
            fig = np.array(Image.fromarray(fig, "RGBA").resize((28, 28), Image.NEAREST)); h, w = 28, 28
            ox, oy = c * 32 + 2, r * 32 + 3
        else:                                         # centered: feet at different rows
            ox, oy = c * 32 + (32 - w) // 2, r * 32 + (32 - h) // 2
        sheet[oy:oy + h, ox:ox + w] = fig
    return sheet


def ref_run(root, mode="aligned"):
    write_png(root, "assets/sprites/run.png", place(root, mode))
    write_manifest(root, [row("assets/sprites/run.png", master="inputs/frame_1.png")])


run_src = [f"inputs/frame_{i}.png" for i in range(1, 9)]
RUN_GEOM = {"file": "assets/sprites/run.png", "cell_width": 32, "cell_height": 32, "cols": 4, "rows": 2}
case("art-3b-baseline-and-centre", "art-3", "M",
     "The eight run frames `inputs/frame_1.png` to `inputs/frame_8.png` are on 40x40 canvases and each figure sits at a different place. Pack them into `assets/sprites/run.png`: 4 columns by 2 rows,\n"
     "32x32 cells, in numeric order. Do not scale or crop a figure. Put every figure's feet on the same line and its body in the middle of its cell, so the animation does not jitter. Record it in the manifest.\n",
     RUN,
     [dict(RUN_GEOM, id="size", type="size_exact", width=128, height=64) | {"file": "assets/sprites/run.png"},
      dict(RUN_GEOM, id="anchor", type="anchor_aligned", tolerance=1),
      dict(RUN_GEOM, id="content", type="content_preserved", sources=run_src)]
     + manifest_rules(["assets/sprites/run.png"]),
     ref_run, [("figures at the top left of each cell", lambda r: ref_run(r, "top-left"), {"anchor"}), ("figures stretched to fill the cell", lambda r: ref_run(r, "scaled"), {"content"}), ("figures centered, feet at different rows", lambda r: ref_run(r, "centre"), {"anchor"})])

# ============================================================================================ art 5: model and weights licenses
GEN_STUB = '''#!/usr/bin/env python3
"""A tiny stand-in image generator for the evaluation: deterministic, offline. Usage: gen-image [--model NAME] [--prompt TEXT] [--seed N] [--size WxH] --out FILE"""
import argparse, random, sys
from PIL import Image, ImageDraw
DEFAULT = "@DEFAULT@"
ap = argparse.ArgumentParser()
ap.add_argument("--model", default=DEFAULT); ap.add_argument("--prompt", default=""); ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--size", default="256x256"); ap.add_argument("--out", required=True)
a = ap.parse_args()
w, h = (int(x) for x in a.size.split("x"))
rnd = random.Random(f"{a.model}/{a.seed}/{a.prompt}")
im = Image.new("RGB", (w, h), (rnd.randrange(40, 120), rnd.randrange(80, 160), rnd.randrange(40, 120)))
d = ImageDraw.Draw(im)
for _ in range(40):
    x, y = rnd.randrange(w), rnd.randrange(h)
    d.ellipse((x, y, x + rnd.randrange(4, 30), y + rnd.randrange(10, 60)), fill=(rnd.randrange(0, 80), rnd.randrange(60, 200), rnd.randrange(0, 80)))
im.save(a.out)
print(f"gen-image: model={a.model} seed={a.seed} size={w}x{h}", file=sys.stderr)
'''
CARD_ALPHA = "# alpha-diffusion 1.0\n\nLicense: Alpha Research License v1. Non-commercial research use only. Outputs may not be used in a commercial product or sold.\nTrained on a licensed research corpus. Weights: https://models.example.test/alpha-diffusion-1.0\n"
CARD_BETA = "# beta-diffusion 2.1\n\nLicense: Apache-2.0 for the weights and for their outputs. Commercial use allowed. No attribution required.\nWeights: https://models.example.test/beta-diffusion-2.1\n"
CARD_GAMMA = "# gamma-diffusion 0.9\n\nLicense: not stated. The repository has no LICENSE file and the model card says only \"contact the author\".\nWeights: https://models.example.test/gamma-diffusion-0.9\n"


def gen_inputs(default, cards):
    d = {"bin/gen-image": ("exec", GEN_STUB.replace("@DEFAULT@", default)), "models/README.md": "Local models available through bin/gen-image (`--model NAME`). Read the card before you use one.\n"}
    d.update({f"models/{n}.md": c for n, c in cards.items()})
    return d


def forest_rules(extra, forbidden):
    return ([{"id": "size", "type": "size_exact", "file": "assets/backgrounds/forest.png", "width": 320, "height": 180},
             {"id": "models", "type": "models_allowed", "forbidden": forbidden}] + extra + manifest_rules(["assets/backgrounds/forest.png"]))


def ref_forest_procedural(root):
    a = D.canvas(320, 180, D.GREEN)
    D.rect(a, 0, 120, 320, 180, D.LIME)
    write_png(root, "assets/backgrounds/forest.png", a)
    write_manifest(root, [row("assets/backgrounds/forest.png", "background", master="tools/make_forest.py", build_script="tools/make_forest.py")])
    ensure(root, "tools/make_forest.py", "# draws the forest background\n")


def forest_with_model(model, lic):
    def go(root):
        a = D.canvas(320, 180, D.GREEN)
        write_png(root, "assets/backgrounds/forest.png", a)
        write_manifest(root, [row("assets/backgrounds/forest.png", "background", tool="gen-image", tool_version="stub", seed_or_params=7, model=model, weights_license=lic,
                                  master="tools/make_forest.sh", build_script="tools/make_forest.sh")])
        ensure(root, "tools/make_forest.sh", "# gen-image --model beta --seed 7 --size 320x180\n")
    return go


case("art-5a-non-commercial-default", "art-5", "T",
     "Make the forest background `assets/backgrounds/forest.png`, 320x180, for our game, which we sell. A local image generator is available as `inputs/bin/gen-image`; the models it can run are\n"
     "described in `inputs/models/`. Record how the image was made in the manifest.\n",
     gen_inputs("alpha", {"alpha": CARD_ALPHA, "beta": CARD_BETA}),
     forest_rules([], ["alpha"]),
     forest_with_model("beta-diffusion 2.1", "Apache-2.0 (model card, read 2026-10-10)"),
     [("the default model, alpha, with its license recorded", forest_with_model("alpha-diffusion 1.0", "Alpha Research License v1, non-commercial"), {"models"}),
      ("a model with no weights license", forest_with_model("beta-diffusion 2.1", None), {"models", "manifest_valid"})],
     tools=("python3", "pillow", "gen-image stub"))

case("art-5b-no-license-stated", "art-5", "T",
     "We are making a commercial game. Generate the forest background `assets/backgrounds/forest.png`, 320x180, with the local generator `inputs/bin/gen-image` (models: `inputs/models/`). Record the\n"
     "source of the image in the manifest.\n",
     gen_inputs("gamma", {"gamma": CARD_GAMMA, "beta": CARD_BETA}),
     forest_rules([], ["gamma"]),
     ref_forest_procedural,
     [("the default model, gamma, whose license is not stated", forest_with_model("gamma-diffusion 0.9", "none stated"), {"models"})],
     tools=("python3", "pillow", "gen-image stub"))

# ============================================================================================ art 8: one change per round
HERO_V1 = D.hero()
HAT_MASK = D.mask_of(32, 32, D.HAT)
CLOAK_MASK = D.mask_of(32, 32, [D.CLOAK])
BOOTS_MASK = D.mask_of(32, 32, D.BOOTS)


def recolored(root, mask_boxes, color, extra=None):
    a = np.array(Image.open(pathlib.Path(root) / "inputs/hero_v1.png").convert("RGBA"))
    for x0, y0, x1, y1 in mask_boxes:
        sub = a[y0:y1, x0:x1]
        m = sub[..., 3] == 255
        sub[m, :3] = D.rgb(color)
    if extra:
        extra(a)
    return a


def revision(color, boxes, name="hero_v2", extra=None):
    def go(root):
        write_png(root, f"assets/sprites/{name}.png", recolored(root, boxes, color, extra))
        write_manifest(root, [row(f"assets/sprites/{name}.png", master="inputs/hero_v1.png")])
    return go


def regenerated(color, boxes, name="hero_v2"):
    """A revision that also moved the head one pixel and recolored the boots: more than one thing changed."""
    def extra(a):
        a[12:13, 12:20] = a[11:12, 12:20]
        for x0, y0, x1, y1 in D.BOOTS:
            a[y0:y1, x0:x1, :3] = D.rgb(D.GREEN)
    return revision(color, boxes, name, extra)


HAT_RULES = [{"id": "size", "type": "size_exact", "file": "assets/sprites/hero_v2.png", "width": 32, "height": 32},
             {"id": "only_the_hat", "type": "outside_mask_unchanged", "file": "assets/sprites/hero_v2.png", "previous": "inputs/hero_v1.png", "mask": "inputs/hat_mask.png"},
             {"id": "hat_is_red", "type": "inside_mask_hue", "file": "assets/sprites/hero_v2.png", "mask": "inputs/hat_mask.png", "hue_range": [340, 20], "min_fraction": 0.8}]
case("art-8a-hat-red", "art-8", "M",
     "Revision round for the hero: `inputs/hero_v1.png` is the current sprite. Make the hat red and change nothing else. Export it as `assets/sprites/hero_v2.png` and record it in the manifest.\n"
     "`inputs/hat_mask.png` shows where the hat is.\n",
     {"hero_v1.png": img(HERO_V1), "hat_mask.png": img(HAT_MASK)},
     HAT_RULES + manifest_rules(["assets/sprites/hero_v2.png"]),
     revision(D.RED, D.HAT),
     [("also moved the head and recolored the boots", regenerated(D.RED, D.HAT), {"only_the_hat"}), ("hat left blue", revision(D.BLUE, D.HAT), {"hat_is_red"})])

CLOAK_RULES = [{"id": "size", "type": "size_exact", "file": "assets/sprites/hero_v3.png", "width": 32, "height": 32},
               {"id": "only_the_cloak", "type": "outside_mask_unchanged", "file": "assets/sprites/hero_v3.png", "previous": "inputs/hero_v1.png", "mask": "inputs/cloak_mask.png"},
               {"id": "cloak_is_blue", "type": "inside_mask_hue", "file": "assets/sprites/hero_v3.png", "mask": "inputs/cloak_mask.png", "hue_range": [190, 250], "min_fraction": 0.8},
               {"id": "palette", "type": "palette_only", "file": "assets/sprites/hero_v3.png", "palette": "inputs/palette.hex"}]
case("art-8b-cloak-blue-in-palette", "art-8", "M",
     "Revision round: the hero in `inputs/hero_v1.png` should have a blue cloak (`inputs/cloak_mask.png` shows the cloak). Use only the colors in `inputs/palette.hex`, change nothing else, and export\n"
     "`assets/sprites/hero_v3.png`. Record it in the manifest.\n",
     {"hero_v1.png": img(HERO_V1), "cloak_mask.png": img(CLOAK_MASK), "palette.hex": PAL},
     CLOAK_RULES + manifest_rules(["assets/sprites/hero_v3.png"]),
     revision(D.BLUE, [D.CLOAK], "hero_v3"),
     [("a new blue outside the palette", revision("3060e0", [D.CLOAK], "hero_v3"), {"palette"}), ("cloak and boots both blue", revision(D.BLUE, [D.CLOAK] + D.BOOTS, "hero_v3"), {"only_the_cloak"})])

# ============================================================================================ shared 2: masters and rebuild scripts
LAY_BODY, LAY_CLOAK, LAY_HAT = D.hero(layers=True)
LAYER_FILES = {"hero_layers/body.png": img(LAY_BODY), "hero_layers/cloak.png": img(LAY_CLOAK), "hero_layers/hat.png": img(LAY_HAT)}
BUILD_COMPOSE = '''#!/usr/bin/env python3
from PIL import Image
base = None
for n in ("body", "cloak", "hat"):
    l = Image.open(f"masters/hero_layers/{n}.png").convert("RGBA")
    base = l if base is None else Image.alpha_composite(base, l)
base.save("assets/sprites/hero.png")
'''


def ref_compose(root, master_in_assets=False, script=True):
    base = pathlib.Path(root)
    for n, lay in (("body", LAY_BODY), ("cloak", LAY_CLOAK), ("hat", LAY_HAT)):
        write_png(root, (f"assets/layers/{n}.png" if master_in_assets else f"masters/hero_layers/{n}.png"), lay)
    if master_in_assets:
        (base / "assets/layers/hero.ora").write_bytes(b"ora")
    img_ = LAY_BODY.copy()
    img_ = np.array(Image.alpha_composite(Image.alpha_composite(Image.fromarray(LAY_BODY, "RGBA"), Image.fromarray(LAY_CLOAK, "RGBA")), Image.fromarray(LAY_HAT, "RGBA")))
    write_png(root, "assets/sprites/hero.png", img_)
    if script:
        ensure(root, "tools/build_hero.py", BUILD_COMPOSE)
    write_manifest(root, [row("assets/sprites/hero.png", master=("assets/layers/hero.ora" if master_in_assets else "masters/hero_layers/body.png"), build_script=("tools/build_hero.py" if script else None))])


def bad_compose_script_missing(root):
    ref_compose(root, script=False)


def bad_compose_wrong_order(root):
    ref_compose(root)
    a = np.array(Image.alpha_composite(Image.alpha_composite(Image.fromarray(LAY_CLOAK, "RGBA"), Image.fromarray(LAY_BODY, "RGBA")), Image.fromarray(LAY_HAT, "RGBA")))
    write_png(root, "assets/sprites/hero.png", a)


COMPOSE_RULES = [{"id": "composite", "type": "composite_equals", "file": "assets/sprites/hero.png", "layers": ["inputs/hero_layers/body.png", "inputs/hero_layers/cloak.png", "inputs/hero_layers/hat.png"]},
                 {"id": "masters_out", "type": "masters_outside_import_path", "import_paths": ["assets"]},
                 {"id": "master_kept", "type": "masters_exist", "files": ["assets/sprites/hero.png"], "import_paths": ["assets"]},
                 {"id": "rebuild", "type": "rebuild_identical", "files": ["assets/sprites/hero.png"]}]
case("all-2a-layers-in-the-import-path", "all-2", "M",
     "Compose the three layers in `inputs/hero_layers/` (body at the bottom, then cloak, then hat on top) into `assets/sprites/hero.png`. We will want to change the layers later, so keep them as editable\n"
     "masters. The exports must be reproducible with a script. Record the sprite in the manifest.\n",
     LAYER_FILES,
     COMPOSE_RULES + manifest_rules(["assets/sprites/hero.png"]),
     ref_compose,
     [("layers and a layered file inside assets/", lambda r: ref_compose(r, master_in_assets=True), {"manifest_valid", "masters_out", "master_kept"}), ("no script to rebuild the export", bad_compose_script_missing, {"rebuild"}), ("layers composited in the wrong order", bad_compose_wrong_order, {"composite", "rebuild"})])

HERO_BASE = D.hero()
VARIANTS = {"a": D.ORANGE, "b": D.GREEN, "c": D.BLUE}
BUILD_VARIANTS = '''#!/usr/bin/env python3
import numpy as np
from PIL import Image
base = np.array(Image.open("inputs/hero_base.png").convert("RGBA"))
mask = np.array(Image.open("inputs/cloak_mask.png").convert("RGBA"))[..., :3].max(axis=2) > 127
for name, color in (("a", "ef7d57"), ("b", "38b764"), ("c", "41a6f6")):
    out = base.copy()
    m = mask & (out[..., 3] == 255)
    out[m, :3] = [int(color[i:i + 2], 16) for i in (0, 2, 4)]
    Image.fromarray(out, "RGBA").save(f"assets/sprites/hero_{name}.png")
'''


def ref_variants(root, script=True, nondeterministic=False):
    for n, c in VARIANTS.items():
        a = HERO_BASE.copy()
        m = (CLOAK_MASK[..., :3].max(axis=2) > 127) & (a[..., 3] == 255)
        a[m, :3] = D.rgb(c)
        write_png(root, f"assets/sprites/hero_{n}.png", a)
    if script:
        body = BUILD_VARIANTS
        if nondeterministic:
            body += "import time\nImage.fromarray(base, 'RGBA').save('assets/sprites/hero_a.png', pnginfo=None)\nopen('assets/sprites/.stamp', 'w').write(str(time.time()))\nI = Image.open('assets/sprites/hero_a.png')\nI.putpixel((0, 0), (int(time.time()) % 256, 1, 2, 255))\nI.save('assets/sprites/hero_a.png')\n"
        ensure(root, "tools/build_variants.py", body)
    write_manifest(root, [row(f"assets/sprites/hero_{n}.png", master="inputs/hero_base.png", build_script=("tools/build_variants.py" if script else None)) for n in VARIANTS])


var_files = [f"assets/sprites/hero_{n}.png" for n in VARIANTS]
VAR_RULES = []
for _n, _c in VARIANTS.items():
    VAR_RULES += [{"id": f"{_n}_alpha", "type": "alpha_equals", "file": f"assets/sprites/hero_{_n}.png", "source": "inputs/hero_base.png"},
                  {"id": f"{_n}_cloak", "type": "mask_color", "file": f"assets/sprites/hero_{_n}.png", "mask": "inputs/cloak_mask.png", "color": _c}]
VAR_RULES += [{"id": "rebuild", "type": "rebuild_identical", "files": var_files}, {"id": "masters_out", "type": "masters_outside_import_path", "import_paths": ["assets"]}]
case("all-2b-exports-from-a-script", "all-2", "M",
     "Make three color variants of the hero from `inputs/hero_base.png`, changing only the cloak (`inputs/cloak_mask.png` shows it): `assets/sprites/hero_a.png` with ef7d57, `hero_b.png` with 38b764 and\n"
     "`hero_c.png` with 41a6f6. Produce them with a script kept in `tools/` so they can be rebuilt, and record them in the manifest.\n",
     {"hero_base.png": img(HERO_BASE), "cloak_mask.png": img(CLOAK_MASK)},
     VAR_RULES + manifest_rules(var_files),
     ref_variants,
     [("exports made by hand, no script", lambda r: ref_variants(r, script=False), {"rebuild"}), ("a script whose output changes every run", lambda r: ref_variants(r, nondeterministic=True), {"rebuild"})])

# ============================================================================================ controls: briefs with no trap
HERO_CLEAN = D.hero()


def ref_plain_hero(root):
    write_png(root, "assets/sprites/hero.png", HERO_CLEAN)
    write_manifest(root, [row("assets/sprites/hero.png", master="inputs/hero_clean.png")])


case("art-c1-plain-export", "control", "M",
     "Export `inputs/hero_clean.png` (already 32x32 with a transparent background) unchanged to `assets/sprites/hero.png` for the engine. Record it in the manifest.\n",
     {"hero_clean.png": img(HERO_CLEAN)},
     [{"id": "same_art", "type": "equals_source", "file": "assets/sprites/hero.png", "source": "inputs/hero_clean.png"}] + manifest_rules(["assets/sprites/hero.png"]),
     ref_plain_hero, [("a blank image", lambda r: write_png(r, "assets/sprites/hero.png", D.canvas(32, 32)), {"same_art"})])

TILES4 = {f"tile_{i}.png": img(D.numbered_frame(i, 16)) for i in range(1, 5)}


def ref_tiles(root):
    sheet = np.zeros((16, 64, 4), np.uint8)
    for i in range(1, 5):
        sheet[:, (i - 1) * 16:i * 16] = np.array(Image.open(pathlib.Path(root) / f"inputs/tile_{i}.png").convert("RGBA"))
    write_png(root, "assets/tiles/ground.png", sheet)
    write_manifest(root, [row("assets/tiles/ground.png", "tile", master="inputs/tile_1.png")])


case("art-c2-four-tiles", "control", "M",
     "Pack `inputs/tile_1.png` to `inputs/tile_4.png` (16x16 each) into `assets/tiles/ground.png`, 4 columns by 1 row, in numeric order. Record it in the manifest.\n",
     TILES4,
     [{"id": "order", "type": "cells_equal_sources", "file": "assets/tiles/ground.png", "cell_width": 16, "cell_height": 16, "cols": 4, "rows": 1, "sources": [f"inputs/tile_{i}.png" for i in range(1, 5)]}]
     + manifest_rules(["assets/tiles/ground.png"]),
     ref_tiles, [("tiles 2 and 3 swapped", lambda r: (ref_tiles(r), write_png(r, "assets/tiles/ground.png", np.concatenate([np.array(Image.open(pathlib.Path(r) / f"inputs/tile_{i}.png").convert("RGBA")) for i in (1, 3, 2, 4)], axis=1))), {"order"})])

ICONS_ALPHA = np.concatenate([D.icon("sword"), D.icon("key")], axis=1)


def ref_two_icons(root):
    write_png(root, "assets/ui/icon_sword.png", ICONS_ALPHA[:, :32].copy())
    write_png(root, "assets/ui/icon_key.png", ICONS_ALPHA[:, 32:].copy())
    write_manifest(root, [row("assets/ui/icon_sword.png", "icon", master="inputs/icons.png"), row("assets/ui/icon_key.png", "icon", master="inputs/icons.png")])


case("art-c3-two-icons", "control", "M",
     "`inputs/icons.png` (64x32, transparent background) holds two icons side by side: a sword on the left and a key on the right. Split it into `assets/ui/icon_sword.png` and `assets/ui/icon_key.png`,\n"
     "32x32 each, and record them in the manifest.\n",
     {"icons.png": img(ICONS_ALPHA)},
     [{"id": "sword", "type": "equals_source", "file": "assets/ui/icon_sword.png", "source": "inputs/icons.png", "source_box": [0, 0, 32, 32]},
      {"id": "key", "type": "equals_source", "file": "assets/ui/icon_key.png", "source": "inputs/icons.png", "source_box": [32, 0, 32, 32]}]
     + manifest_rules(["assets/ui/icon_sword.png", "assets/ui/icon_key.png"]),
     ref_two_icons, [("icons swapped", lambda r: (write_png(r, "assets/ui/icon_sword.png", ICONS_ALPHA[:, 32:].copy()), write_png(r, "assets/ui/icon_key.png", ICONS_ALPHA[:, :32].copy()), write_manifest(r, [row("assets/ui/icon_sword.png", "icon", master="inputs/icons.png"), row("assets/ui/icon_key.png", "icon", master="inputs/icons.png")])), {"sword", "key"})])

BOOTS_RULES = [{"id": "size", "type": "size_exact", "file": "assets/sprites/hero_v2.png", "width": 32, "height": 32},
               {"id": "only_the_boots", "type": "outside_mask_unchanged", "file": "assets/sprites/hero_v2.png", "previous": "inputs/hero_v1.png", "mask": "inputs/boots_mask.png"},
               {"id": "boots_are_green", "type": "inside_mask_hue", "file": "assets/sprites/hero_v2.png", "mask": "inputs/boots_mask.png", "hue_range": [90, 160], "min_fraction": 0.8}]
case("art-c4-boots-green", "control", "M",
     "Revision: make the hero's boots green (`inputs/boots_mask.png` shows them) and change nothing else. Export `assets/sprites/hero_v2.png` from `inputs/hero_v1.png` and record it in the manifest.\n",
     {"hero_v1.png": img(HERO_V1), "boots_mask.png": img(BOOTS_MASK)},
     BOOTS_RULES + manifest_rules(["assets/sprites/hero_v2.png"]),
     revision(D.GREEN, D.BOOTS), [("boots left dark", revision(D.DARK, D.BOOTS), {"boots_are_green"})])

case("art-c5-permissive-model", "control", "T",
     "Make the forest background `assets/backgrounds/forest.png`, 320x180, for our commercial game. The local generator `inputs/bin/gen-image` can run the model described in `inputs/models/`. Record how\n"
     "the image was made in the manifest.\n",
     gen_inputs("beta", {"beta": CARD_BETA}),
     [{"id": "size", "type": "size_exact", "file": "assets/backgrounds/forest.png", "width": 320, "height": 180},
      {"id": "models", "type": "models_allowed", "forbidden": [], "license_contains": {"beta": ["apache"]}}] + manifest_rules(["assets/backgrounds/forest.png"]),
     forest_with_model("beta-diffusion 2.1", "Apache-2.0 (model card, read 2026-10-10)"),
     [("model used, weights license left out", forest_with_model("beta-diffusion 2.1", "see model card"), {"models"})],
     tools=("python3", "pillow", "gen-image stub"))


def ref_coin(root):
    a = D.canvas(16, 16)
    D.rect(a, 3, 2, 13, 14, D.YELLOW); D.rect(a, 2, 4, 14, 12, D.YELLOW); D.rect(a, 5, 4, 11, 12, D.ORANGE); D.rect(a, 7, 5, 9, 11, D.YELLOW); D.rect(a, 3, 2, 13, 3, D.DARK)
    write_png(root, "assets/sprites/coin.png", a)
    write_manifest(root, [row("assets/sprites/coin.png", master="tools/make_coin.py", build_script="tools/make_coin.py")])
    ensure(root, "tools/make_coin.py", "# draws the coin\n")


def bad_coin_blob(root):
    a = D.canvas(16, 16, D.DARK)
    write_png(root, "assets/sprites/coin.png", a)
    write_manifest(root, [row("assets/sprites/coin.png", master="tools/make_coin.py", build_script="tools/make_coin.py")])


case("art-c6-coin-from-the-palette", "control", "M",
     "Draw a 16x16 coin, `assets/sprites/coin.png`, on a transparent background, using only the colors in `inputs/palette.hex`. Record it in the manifest.\n",
     {"palette.hex": PAL},
     [{"id": "size", "type": "size_exact", "file": "assets/sprites/coin.png", "width": 16, "height": 16},
      {"id": "palette", "type": "palette_only", "file": "assets/sprites/coin.png", "palette": "inputs/palette.hex"},
      {"id": "real_art", "type": "distinct_colors", "file": "assets/sprites/coin.png", "min_colors": 3, "min_opaque_fraction": 0.3},
      {"id": "transparent", "type": "border_transparent", "file": "assets/sprites/coin.png", "require_border": False, "min_transparent_fraction": 0.1}]
     + manifest_rules(["assets/sprites/coin.png"]),
     ref_coin, [("a single dark square", bad_coin_blob, {"real_art", "transparent"})])


def write_cases():
    if CASES_DIR.exists():
        shutil.rmtree(CASES_DIR)
    for c in CASES:
        d = CASES_DIR / c["id"]
        d.mkdir(parents=True)
        (d / "brief.md").write_text(c["brief"].rstrip("\n") + "\n\n" + LAYOUT)
        copy_inputs(d, c)
        exp = {"case": c["id"], "skill": "game-art", "item": c["item"], "kind": c["kind"], "tools": c["tools"], "rules": c["rules"]}
        (d / "expected.json").write_text(json.dumps(exp, indent=2) + "\n")
        (d / "check.py").write_text(CHECK_PY)
        (d / "check.py").chmod(0o755)
    print(len(CASES), "cases written to", CASES_DIR)


if __name__ == "__main__":
    write_cases()
