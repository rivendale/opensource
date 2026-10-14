#!/usr/bin/env python3
"""Scores a model reviewer's answers on the calibration set. Usage: score.py RECORDS.json  (exit 0 all floors met, 1 a floor missed, 2 unreadable).

RECORDS.json is a list of {"image": "images/<hex>.png", "repeat": 0.., "name": "one line", "features": [6 booleans, in the order of answers.json "questions"]}: the reviewer's
blind name, then its answers to the six subject-free questions, for each image and each of at least three repeats. Output: {"case", "rules": [{"id","pass","measured","threshold"}]}.
Every floor is absolute; a reviewer that answers nothing right cannot pass by being compared with a weak baseline."""
import json, math, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
NEGATION = {"not", "no", "isnt", "isn", "without", "nor", "never"}
MIN_REPEATS = 3
FLOORS = {"names_drawn": 5, "packet_agree": 4, "packet_false_yes": 1, "wrong_named": 0, "feature_all": 0.85, "feature_each": 0.70, "stable": 0.90}


def stem(w):
    return w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w


def tokens(name):
    return [stem(t) for t in re.findall(r"[a-z]+", name.lower().replace("'", ""))]


def classify(name, intended, yes_words, near_words, all_yes):
    """'yes' = the name uses an accepted word for the intended subject; 'near' = a near-miss word; 'object' = it names some other known subject (for an image that has none); else 'no'.
    Whole words only, so 'coincidence', 'monkey' and 'keyboard' do not match; a negation anywhere in the name ('not a key') makes it a non-match."""
    t = tokens(name)
    if set(t) & {stem(n) for n in NEGATION}:
        return "no"
    if intended:
        if set(t) & {stem(w) for w in yes_words}:
            return "yes"
        if set(t) & {stem(w) for w in near_words}:
            return "near"
        return "no"
    return "object" if set(t) & all_yes else "no"


def majority(values):
    """The value held by MORE than half of the repeats; with no strict majority the answer is 'unstable', which no floor treats as a correct name."""
    best = max(set(values), key=lambda v: (values.count(v), v))
    return best if values.count(best) * 2 > len(values) else "unstable"


def score(records, key):
    images = key["images"]
    all_yes = {stem(w) for words in key["words"].values() for w in words[0]}
    rules = []

    def rule(i, ok, measured, threshold):
        rules.append({"id": i, "pass": bool(ok), "measured": measured, "threshold": threshold})

    # completeness first: input count against output count, and the same number of distinct repeats everywhere
    by = {}
    problems = []
    for r in records if isinstance(records, list) else []:
        if (not isinstance(r, dict) or set(r) != {"image", "repeat", "name", "features"} or not isinstance(r["name"], str) or not r["name"].strip()
                or not isinstance(r["features"], list) or len(r["features"]) != len(key["questions"]) or any(type(v) is not bool for v in r["features"])
                or type(r["repeat"]) is not int):
            problems.append("malformed record"); continue
        by.setdefault(r["image"], {})
        if r["repeat"] in by[r["image"]]:
            problems.append("duplicate repeat for " + r["image"])
        by[r["image"]][r["repeat"]] = r
    expected = [im["file"] for im in images]
    if set(by) != set(expected):
        problems.append("images answered %d of %d (missing %d, unknown %d)" % (len(set(by) & set(expected)), len(expected), len(set(expected) - set(by)), len(set(by) - set(expected))))
    counts = {len(v) for v in by.values()}
    reps = min(counts) if counts else 0
    if len(counts) > 1 or reps < MIN_REPEATS or any(sorted(v) != list(range(len(v))) for v in by.values()):
        problems.append("every image needs the same number (>= %d) of repeats numbered from 0" % MIN_REPEATS)
    rule("records", not problems, problems or "%d images x %d repeats" % (len(expected), reps), "all images, equal repeats >= %d, well-formed" % MIN_REPEATS)
    if problems:
        for i, t in (("names_drawn", ">= 5 of 6"), ("packet_agree", ">= 4 of 5"), ("packet_false_yes", "<= 1 of 3"), ("wrong_named", "0 of 3"), ("feature_all", ">= 0.85"), ("feature_each", ">= 0.70 each"), ("stable", ">= 0.90")):
            rule(i, False, "not measured: the records are incomplete", t)
        return {"case": "review-calibration", "rules": rules}

    cls, feat, cells = {}, {}, []
    for im in images:
        rs = [by[im["file"]][k] for k in range(reps)]
        classes = [classify(r["name"], im["intended"], im.get("yes_words", []), im.get("near_words", []), all_yes) for r in rs]
        cls[im["file"]] = majority(classes)
        feat[im["file"]] = [sum(r["features"][q] for r in rs) * 2 > reps for q in range(len(key["questions"]))]
        cells.append(len(set(classes)) == 1)
        cells += [len({r["features"][q] for r in rs}) == 1 for q in range(len(key["questions"]))]
    drawn = [im for im in images if im["kind"] in ("reference", "non-subject")]
    ok = sum(cls[im["file"]] == "yes" for im in drawn)
    rule("names_drawn", ok >= FLOORS["names_drawn"], "%d of %d named correctly" % (ok, len(drawn)), ">= %d of %d" % (FLOORS["names_drawn"], len(drawn)))
    packet = [im for im in images if im["kind"] == "packet"]
    agree = sum((cls[im["file"]] == "yes") == (im["human"] == "yes") for im in packet)
    humno = [im for im in packet if im["human"] == "no"]
    fyes = sum(cls[im["file"]] == "yes" for im in humno)
    rule("packet_agree", agree >= FLOORS["packet_agree"], "%d of %d agree with the human yes/no" % (agree, len(packet)), ">= %d of %d" % (FLOORS["packet_agree"], len(packet)))
    rule("packet_false_yes", fyes <= FLOORS["packet_false_yes"], "%d of %d human-no images named as the subject" % (fyes, len(humno)), "<= %d of %d" % (FLOORS["packet_false_yes"], len(humno)))
    wrong = [im for im in images if im["kind"] == "wrong"]
    named = sum(cls[im["file"]] == "object" for im in wrong)
    rule("wrong_named", named <= FLOORS["wrong_named"], "%d of %d wrong images named as a known object" % (named, len(wrong)), "%d of %d" % (FLOORS["wrong_named"], len(wrong)))
    total = sum(feat[im["file"]][q] == im["truth"][q] for im in images for q in range(len(key["questions"])))
    n = len(images) * len(key["questions"])
    per_q = [sum(feat[im["file"]][q] == im["truth"][q] for im in images) / len(images) for q in range(len(key["questions"]))]
    rule("feature_all", total / n >= FLOORS["feature_all"], round(total / n, 3), ">= %.2f" % FLOORS["feature_all"])
    rule("feature_each", min(per_q) >= FLOORS["feature_each"], [round(x, 2) for x in per_q], ">= %.2f for each question" % FLOORS["feature_each"])
    stable = sum(cells) / len(cells)
    rule("stable", stable >= FLOORS["stable"], round(stable, 3), ">= %.2f of (image, field) cells identical across repeats" % FLOORS["stable"])
    return {"case": "review-calibration", "rules": rules}


def main(argv):
    try:
        key = json.loads((HERE / "answers.json").read_text())
        records = json.loads(pathlib.Path(argv[1]).read_text())
    except (OSError, ValueError, IndexError) as e:
        print("score.py: " + str(e), file=sys.stderr); return 2
    out = score(records, key)
    print(json.dumps(out))
    return 0 if all(r["pass"] for r in out["rules"]) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
