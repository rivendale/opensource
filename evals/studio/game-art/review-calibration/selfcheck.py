#!/usr/bin/env python3
"""Checks the calibration set and its scorer, with no model call: (1) the set's hygiene, (2) that the scorer passes a reviewer that answers from the ground truth, (3) that it FAILS each
reviewer that is wrong in a known way (every floor must be failed by at least one of them: a floor nothing can fail may be unable to). Exit 0 when all hold."""
import copy, json, pathlib, re, struct, sys
import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_set as B   # noqa: E402
import score as S       # noqa: E402

KEY = json.loads((HERE / "answers.json").read_text())
IM = KEY["images"]
Q = len(KEY["questions"])
bad = 0


def check(ok, text):
    global bad
    print(("ok   " if ok else "FAIL ") + text)
    bad += not ok


# ---- 1. the set itself
check(len(IM) == 14 and len({r["file"] for r in IM}) == 14, "14 distinct images")
kinds = {k: sum(r["kind"] == k for r in IM) for k in ("reference", "non-subject", "packet", "wrong")}
check(kinds == {"reference": 3, "non-subject": 3, "packet": 5, "wrong": 3}, "kinds %s" % kinds)
hexnames = all(re.fullmatch(r"images/[0-9a-f]{8}\.png", r["file"]) and (HERE / r["file"]).is_file() for r in IM)
check(hexnames, "every file is a neutral 8-hex name that exists")
def chunks(p):
    d = p.read_bytes(); i, out = 8, []
    while i < len(d):
        n = struct.unpack(">I", d[i:i + 4])[0]; out.append(d[i + 4:i + 8].decode()); i += n + 12
    return out
check(all(set(chunks(HERE / r["file"])) <= {"IHDR", "PLTE", "IDAT", "IEND"} for r in IM), "no ancillary chunks (no text that could name a subject)")
check(all(Image.open(HERE / r["file"]).size == (16, 16) for r in IM), "all 16x16")
recomputed = [B.truth(np.array(Image.open(HERE / r["file"]).convert("RGBA"))) for r in IM]
check(recomputed == [r["truth"] for r in IM], "stored feature truth equals the truth recomputed from the pixels")
for q in range(Q):
    t = sum(r["truth"][q] for r in IM)
    check(2 <= t <= len(IM) - 2, "question %d is balanced (%d true of %d), so answering all one way cannot score" % (q + 1, t, len(IM)))
words = {w for v in KEY["words"].values() for w in v[0] + v[1]}
leak = [q for q in KEY["questions"] if set(S.tokens(q)) & {S.stem(w) for w in words}]
check(not leak, "no question contains a subject word %s" % leak)
check([r["human"] for r in IM if r["kind"] == "packet"].count("yes") == 2, "packet has 2 human yes and 3 human no")

# ---- 2. the name matcher on its own
POS = ["a coin", "Coins", "a gold coin", "potion bottle", "A flask", "a key", "a heart", "toadstool", "boot"]
NEG = ["coincidence", "a monkey", "keyboard", "not a key", "no coin here", "an orange ball", "a stick or a wand, not a key", "a bottle opener? no"]
allyes = {S.stem(w) for v in KEY["words"].values() for w in v[0]}
def which(name):
    for subj, (y, n) in KEY["words"].items():
        if S.classify(name, subj, y, n, allyes) == "yes":
            return subj
check(all(which(n) for n in POS), "matcher accepts: %s" % POS)
check(not any(which(n) for n in NEG), "matcher refuses (substrings, negations, other objects): %s" % NEG)

# ---- 3. reviewers with known behaviour; each yields records for 3 repeats
REPS = 3
def records(fn):
    return [{"image": r["file"], "repeat": k, "name": fn(r, k)[0], "features": fn(r, k)[1]} for r in IM for k in range(REPS)]
def perfect(r, k): return r["canonical_name"], list(r["truth"])
def human_like(r, k): return (r.get("human_name") or r["canonical_name"]), list(r["truth"])
def all_true(r, k): return r["canonical_name"], [True] * Q
def all_false(r, k): return r["canonical_name"], [False] * Q
def echo_intended(r, k): return (r["intended"] or "coin"), list(r["truth"])
def generic_names(r, k): return "an image", list(r["truth"])
nxt = {IM[i]["file"]: IM[(i + 1) % len(IM)]["canonical_name"] for i in range(len(IM))}
def shifted(r, k): return nxt[r["file"]], list(r["truth"])
def blind_on_q4(r, k): t = list(r["truth"]); t[3] = not t[3]; return r["canonical_name"], t
def unstable(r, k):
    t = list(r["truth"]); n = r["canonical_name"]
    if k == 1:
        t = [not x for x in t]; n = "an image"
    return n, t
def lenient_packet(r, k): return ((r["intended"] or r["canonical_name"]) if r["kind"] == "packet" else r["canonical_name"]), list(r["truth"])
def names_everything(r, k): return ("a coin" if r["kind"] == "wrong" else r["canonical_name"]), list(r["truth"])

ALL = {"records", "names_drawn", "packet_agree", "packet_false_yes", "wrong_named", "feature_all", "feature_each", "stable"}
seen = set()


def run(label, recs, expect_fail):
    out = S.score(recs, KEY)
    failed = {x["id"] for x in out["rules"] if not x["pass"]}
    check(failed == set(expect_fail), "%-44s fails %s%s" % (label, sorted(failed) or "nothing", "" if failed == set(expect_fail) else "   (wanted %s)" % sorted(expect_fail)))
    seen.update(failed)


run("answers from the ground truth", records(perfect), [])
run("answers as the human readers did", records(human_like), [])
run("every question answered yes", records(all_true), {"feature_all", "feature_each"})
run("every question answered no", records(all_false), {"feature_all", "feature_each"})
run("names the intended subject, always", records(echo_intended), {"packet_agree", "packet_false_yes", "wrong_named"})
run("names every image 'an image'", records(generic_names), {"names_drawn", "packet_agree"})
# (one human-no image happens to receive a matching name, which the "<= 1 false yes" floor allows; the wrong images receive object names, which the floor on those catches)
run("names shifted by one image", records(shifted), {"names_drawn", "packet_agree", "wrong_named"})
run("one question answered backwards", records(blind_on_q4), {"feature_all", "feature_each"})
run("flips every answer on repeat 2 of 3", records(unstable), {"stable"})
run("calls the three human-no images yes", records(lenient_packet), {"packet_agree", "packet_false_yes"})
run("names the wrong images as objects", records(names_everything), {"wrong_named"})
full = records(perfect)
run("one image missing", [r for r in full if r["image"] != IM[0]["file"]], ALL)
run("a repeat duplicated (same index twice)", full + [copy.deepcopy(full[0])], ALL)
run("only two repeats", [r for r in full if r["repeat"] < 2], ALL)
bad_rec = copy.deepcopy(full); bad_rec[0]["features"] = [1, 0, 1, 0, 1, 0]
run("features as 0/1, not booleans", bad_rec, ALL)
unfailed = ALL - {"records"} - seen
check(not unfailed, "every floor is failed by at least one known-bad reviewer (unfailed: %s)" % sorted(unfailed))
print("selfcheck:", "all hold" if not bad else "FAILED (%d)" % bad)
sys.exit(1 if bad else 0)
