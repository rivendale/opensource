#!/usr/bin/env python3
"""Builds the review-calibration control set: images/, answers.json and plan.json. Reproducible: python3 build_set.py (needs numpy and Pillow).

The set tests the model reviewer (blind name, then subject-free yes/no questions) against ground truth that does not come from a model: the feature answers are COMPUTED
from the pixels, the name answers for drawn icons are the drawer's, and the name answers for the pilot images are two human readers' verdicts."""
import hashlib, json, pathlib, random, sys
import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "build"))
import drawing as D                       # noqa: E402
import make_cases as M                    # noqa: E402  (the leg-1 reference drawings)

DARK = D.rgb(D.DARK)
QUESTIONS = [   # subject-free, answerable from the rendered pixels; truth() is the ground truth for each
    "Is the whole shape surrounded by a dark outline?",
    "Does any part of the shape touch the edge of the picture?",
    "Does the shape use at least three colours other than its dark outline colour?",
    "Is the lower-right half of the shape darker than its upper-left half?",
    "Is the picture a single flat colour?",
    "Is the shape a left-to-right mirror image of itself?",
]


def opaque(a):
    return a[..., 3] == 255


def luma(a):
    return 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]


def truth(a):
    op = opaque(a); h, w = op.shape
    pad = np.pad(op, 1, constant_values=False)
    edge = op & ~(pad[:-2, 1:-1] & pad[2:, 1:-1] & pad[1:-1, :-2] & pad[1:-1, 2:])
    dark = (a[..., :3] == np.array(DARK)).all(axis=2)
    q1 = bool(edge.any()) and float((edge & dark).sum()) / float(edge.sum()) >= 0.9
    ring = np.zeros_like(op); ring[0, :] = ring[-1, :] = ring[:, 0] = ring[:, -1] = True
    q2 = bool((op & ring).any())
    cols = {tuple(p) for p in a[op & ~dark][:, :3]}
    q3 = len(cols) >= 3
    ys, xs = np.nonzero(op)
    if len(xs):
        s = xs + ys; c = s.mean(); L = luma(a)[ys, xs]
        ul, lr = L[s < c], L[s > c]
        q4 = bool(len(ul) and len(lr) and lr.mean() < ul.mean() - 8)
    else:
        q4 = False
    q5 = len({tuple(p) for p in a.reshape(-1, 4)}) == 1
    if len(xs):
        mism = int((op ^ op[:, ::-1]).sum())
        q6 = mism <= 0.10 * int(op.sum())
    else:
        q6 = False
    return [q1, q2, q3, q4, q5, q6]


def icon(rows, key):
    a = D.canvas(16, 16)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                D.rect(a, x, y, x + 1, y + 1, key[ch])
    return a


def draw_heart():
    rows = ["................", "................", "...RRR....RRR...", "..RRRRR..RRRRR..", ".RRRRRRRRRRRRRR.", ".RRRRRRRRRRRRRR.", ".RRRRRRRRRRRRRR.",
            "..RRRRRRRRRRRR..", "...RRRRRRRRRR...", "....RRRRRRRR....", ".....RRRRRR.....", "......RRRR......", ".......RR.......", "................", "................", "................"]
    a = D.outlined(icon(rows, {"R": D.RED}))
    for x, y in ((3, 4), (4, 4), (3, 5)):
        D.rect(a, x, y, x + 1, y + 1, D.ORANGE)
    return a


def draw_mushroom():
    a = D.canvas(16, 16)
    cap = np.zeros((16, 16), bool)
    yy, xx = np.mgrid[0:16, 0:16]
    cap = (np.hypot(xx - 7.5, (yy - 8.0) * 1.25) <= 6.2) & (yy <= 8)
    a[cap, :3] = D.rgb(D.RED); a[cap, 3] = 255
    D.rect(a, 6, 8, 10, 13, D.YELLOW); D.rect(a, 9, 9, 10, 13, D.ORANGE)
    for x, y in ((4, 5), (5, 5), (9, 4), (10, 4), (11, 6), (7, 7)):
        D.rect(a, x, y, x + 1, y + 1, D.YELLOW)
    return D.outlined(a)


def draw_boot():
    a = D.canvas(16, 16)
    D.rect(a, 4, 2, 9, 11, D.BLUE); D.rect(a, 4, 9, 14, 13, D.BLUE); D.rect(a, 3, 13, 14, 15, D.PURPLE)
    D.rect(a, 5, 3, 6, 9, D.LIME); D.rect(a, 8, 5, 9, 11, D.PURPLE)
    return D.outlined(a)


def flat():
    return D.canvas(16, 16, D.PALETTE[7])


def blank():
    return D.canvas(16, 16)


def noise():
    r = random.Random(7); a = D.canvas(16, 16)
    for y in range(16):
        for x in range(16):
            D.rect(a, x, y, x + 1, y + 1, D.PALETTE[r.randrange(8)])
    return a


WORDS = {  # yes words (whole words, lower case) and near-miss words, per intended subject
    "coin": (["coin", "coins"], ["medal", "token", "disc", "disk"]),
    "key": (["key", "keys"], ["wand", "skeleton"]),
    "potion": (["potion", "bottle", "flask", "vial"], ["jar", "vase"]),
    "heart": (["heart"], ["valentine"]),
    "mushroom": (["mushroom", "toadstool"], ["umbrella"]),
    "boot": (["boot", "shoe"], ["sock", "slipper"]),
}
# the pilot images and the two readers' verdicts (the first reader's names reached the second before the second opened the packet, so the agreement is not independent)
PACKET = {"packet1-08bc7065.png": ("key", "yes", "a key"), "packet1-27256dfd.png": ("coin", "no", "an orange ball"), "packet1-4a9ddb2c.png": ("potion", "yes", "a potion bottle"),
          "packet1-b6128d49.png": ("key", "no", "a stick or a wand, not a key"), "packet1-d33c8f6f.png": ("coin", "no", "a large orange disc cropped by the picture, an orange or a sun")}


def build():
    out = HERE / "images"
    if out.exists():
        for p in out.glob("*.png"):
            p.unlink()
    out.mkdir(exist_ok=True)
    items = [("reference", "coin", M.draw_coin(), None, "a coin"), ("reference", "key", M.draw_key(), None, "a key"), ("reference", "potion", M.draw_potion(), None, "a potion bottle"),
             ("non-subject", "heart", draw_heart(), None, "a heart"), ("non-subject", "mushroom", draw_mushroom(), None, "a mushroom"), ("non-subject", "boot", draw_boot(), None, "a boot"),
             ("wrong", None, flat(), None, "a flat blue square"), ("wrong", None, blank(), None, "an empty picture"), ("wrong", None, noise(), None, "random coloured noise")]
    for name, (subject, human, said) in PACKET.items():
        raw = (HERE / "source" / name).read_bytes()
        a = np.array(Image.open(HERE / "source" / name).convert("RGBA"))
        items.append(("packet", subject, a, {"human": human, "human_name": said, "source_sha256": hashlib.sha256(raw).hexdigest()}, said))
    answers = []
    for kind, subject, a, extra, canonical in items:
        px = hashlib.sha256(a.tobytes()).hexdigest()[:8]
        Image.fromarray(a, "RGBA").save(out / f"{px}.png", optimize=False)   # pixel-exact, no ancillary chunks
        rec = {"file": f"images/{px}.png", "kind": kind, "intended": subject, "canonical_name": canonical, "truth": truth(a)}
        if subject:
            rec["yes_words"], rec["near_words"] = WORDS[subject]
        if kind in ("reference", "non-subject"):
            rec["human"] = "yes"
        if kind == "wrong":
            rec["human"] = "no"
        if extra:
            rec.update(extra)
        answers.append(rec)
    assert len({r["file"] for r in answers}) == len(answers), "duplicate image"
    (HERE / "answers.json").write_text(json.dumps({"questions": QUESTIONS, "words": WORDS, "images": answers}, indent=2) + "\n")
    print(len(answers), "images;", "truth balance per question (true count):", [sum(r["truth"][i] for r in answers) for i in range(len(QUESTIONS))])


if __name__ == "__main__":
    build()
