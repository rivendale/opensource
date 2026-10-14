#!/usr/bin/env python3
"""Checks the operator review plans without a model call: each plan is well formed, no question holds a subject word (casefolded, NFKC, common Greek and Cyrillic lookalikes, prefix match), the
plan is accepted by the runner's own validate_plan (a missing or unimportable reviewer is a failure, never a skip, and the check fails if validate_plan was applied to fewer plans than exist), a primed question is refused (a negative control), and every expectation names a real calibration image."""
import json, pathlib, re, sys, unicodedata

HERE = pathlib.Path(__file__).resolve().parent
LOOK = str.maketrans({'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'х': 'x', 'у': 'y', 'і': 'i', 'ј': 'j', 'к': 'k', 'ν': 'v', 'α': 'a', 'ο': 'o', 'ρ': 'p', 'ι': 'i', 'κ': 'k', 'ε': 'e'})
bad = 0


def norm(t):
    return unicodedata.normalize("NFKC", t).casefold().translate(LOOK)


def holds(question, words):
    return any(re.search(r"(?<!\w)" + re.escape(norm(w)), norm(question)) for w in words)


def check(ok, text):
    global bad
    print(("ok   " if ok else "FAIL ") + text)
    bad += not ok


RUNNER = HERE.parents[3] / "skills/studio/runner"      # HERE is <repo>/evals/studio/game-art/review-plans
sys.path.insert(0, str(RUNNER))
reviewer, applied = None, 0
check((RUNNER / "reviewer.py").is_file(), "the runner's reviewer.py exists at %s" % RUNNER.relative_to(HERE.parents[3]))
try:
    import reviewer
    check(pathlib.Path(reviewer.__file__).resolve() == (RUNNER / "reviewer.py").resolve(), "the module imported is that file")
except ImportError as e:
    check(False, "the runner's reviewer cannot be imported (%s): validate_plan would not be applied" % e)
images = {r["file"] for r in json.loads((HERE.parent / "review-calibration/answers.json").read_text())["images"]}
exp = json.loads((HERE / "expectations.json").read_text())["plans"]
for path in sorted(HERE.glob("leg-1-*.json")):
    if path.name == "expectations.json":
        continue
    plan = json.loads(path.read_text())
    item = plan[0]
    check(len(plan) == 1 and set(item) == {"file", "subject_words", "features"}, "%s: one asset with file, subject_words, features" % path.name)
    check(1 <= len(item["features"]) <= 12 and len(set(item["features"])) == len(item["features"]), "%s: %d distinct questions" % (path.name, len(item["features"])))
    check(not [q for q in item["features"] if holds(q, item["subject_words"])], "%s: no question holds a subject word %s" % (path.name, item["subject_words"]))
    check(all(q.endswith("?") and "\n" not in q for q in item["features"]), "%s: every question is a single-line question" % path.name)
    check(holds("Does it look like a %s?" % item["subject_words"][0], item["subject_words"]), "%s: the local guard refuses a primed question (negative control)" % path.name)
    if reviewer:
        try:
            reviewer.validate_plan(plan)
            applied += 1
            check(True, "%s: accepted by the runner's validate_plan" % path.name)
        except reviewer.ReviewError as e:
            check(False, "%s: refused by validate_plan: %s" % (path.name, e))
        try:
            reviewer.validate_plan([dict(item, features=["Does it look like a %s?" % item["subject_words"][0]])])
            check(False, "%s: validate_plan accepted a primed question" % path.name)
        except reviewer.ReviewError:
            check(True, "%s: validate_plan refuses a primed question" % path.name)
    rows = exp.get(path.name, [])
    check(rows and all(r["image"] in images for r in rows), "%s: %d expectations, each naming a real calibration image" % (path.name, len(rows)))
    check(any(r["accept"] for r in rows) and any(not r["accept"] for r in rows), "%s: the expectations include accepted and rejected images" % path.name)
check(set(exp) == {p.name for p in HERE.glob("leg-1-*.json")}, "expectations exist for exactly the three plans")
check(reviewer is not None and applied == len(exp), "validate_plan was applied to every plan (%d of %d): a check that applied nothing has not run" % (applied, len(exp)))
print("check_plans:", "all hold" if not bad else "FAILED (%d)" % bad)
sys.exit(1 if bad else 0)
