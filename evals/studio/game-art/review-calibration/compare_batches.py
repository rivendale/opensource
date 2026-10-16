#!/usr/bin/env python3
"""Compares two calibration batches over the same 14 images: per image, the name class (yes / near / no / object / unstable) in each batch and the question answers that changed.
Usage: compare_batches.py OLD_RECORDS.json NEW_RECORDS.json [--json OUT]. Reported, never scored: the floors are score.py's. Exit 0 always unless a file cannot be read (2) or the two
batches do not cover the same images and repeats (1)."""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import score as S  # noqa: E402


def per_image(records, key):
    all_yes = {S.stem(w) for words in key["words"].values() for w in words[0]}
    by = {}
    for r in records:
        by.setdefault(r["image"], []).append(r)
    out = {}
    for im in key["images"]:
        rs = sorted(by.get(im["file"], []), key=lambda r: r["repeat"])
        classes = [S.classify(r["name"], im["intended"], im.get("yes_words", []), im.get("near_words", []), all_yes) for r in rs]
        feats = [sum(r["features"][q] for r in rs) * 2 > len(rs) for q in range(len(key["questions"]))] if rs else []
        out[im["file"]] = {"repeats": len(rs), "class": S.majority(classes) if classes else "missing", "classes": classes, "features": feats,
                           "names": sorted({r["name"] for r in rs}), "truth": im["truth"], "kind": im["kind"], "canonical": im["canonical_name"]}
    return out


def compare(old, new, key):
    a, b = per_image(old, key), per_image(new, key)
    problems = [f for f in a if a[f]["repeats"] != b[f]["repeats"] or a[f]["repeats"] == 0]
    rows = []
    for im in key["images"]:
        f = im["file"]
        changed = [q + 1 for q in range(len(key["questions"])) if a[f]["features"] and b[f]["features"] and a[f]["features"][q] != b[f]["features"][q]]
        right_a = [q + 1 for q in range(len(key["questions"])) if a[f]["features"] and a[f]["features"][q] == im["truth"][q]]
        right_b = [q + 1 for q in range(len(key["questions"])) if b[f]["features"] and b[f]["features"][q] == im["truth"][q]]
        rows.append({"image": f, "kind": im["kind"], "is": im["canonical_name"], "old_class": a[f]["class"], "new_class": b[f]["class"],
                     "old_names": a[f]["names"], "new_names": b[f]["names"], "answers_changed": changed,
                     "correct_old": len(right_a), "correct_new": len(right_b)})
    def n(rows_, pred): return sum(1 for r in rows_ if pred(r))
    drawn_or_packet_yes = [r for r in rows if r["kind"] in ("reference", "non-subject")]
    summary = {"images": len(rows), "same_class": n(rows, lambda r: r["old_class"] == r["new_class"]),
               "drawn_icons_named_correctly_old": n(drawn_or_packet_yes, lambda r: r["old_class"] == "yes"),
               "drawn_icons_named_correctly_new": n(drawn_or_packet_yes, lambda r: r["new_class"] == "yes"),
               "feature_answers_correct_old": sum(r["correct_old"] for r in rows), "feature_answers_correct_new": sum(r["correct_new"] for r in rows),
               "feature_answers_total": len(rows) * len(key["questions"]), "gained_yes": [r["image"] for r in rows if r["old_class"] != "yes" and r["new_class"] == "yes"],
               "lost_yes": [r["image"] for r in rows if r["old_class"] == "yes" and r["new_class"] != "yes"]}
    return rows, summary, problems


def main(argv):
    try:
        key = json.loads((HERE / "answers.json").read_text())
        old = json.loads(pathlib.Path(argv[1]).read_text())
        new = json.loads(pathlib.Path(argv[2]).read_text())
    except (OSError, ValueError, IndexError) as e:
        print("compare_batches.py: " + str(e), file=sys.stderr)
        return 2
    rows, summary, problems = compare(old, new, key)
    for r in rows:
        print(f"{r['image'][7:15]} {r['kind'][:6]:6} {r['is'][:26]:26} {r['old_class']:>8} -> {r['new_class']:<8} answers changed {r['answers_changed']} correct {r['correct_old']}->{r['correct_new']}")
    print(json.dumps(summary))
    if "--json" in argv:
        pathlib.Path(argv[argv.index("--json") + 1]).write_text(json.dumps({"rows": rows, "summary": summary, "problems": problems}, indent=2) + "\n")
    if problems:
        print("the batches do not cover the same images and repeats: " + ", ".join(problems), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
