#!/usr/bin/env python3
"""Shows that every game-art checker can fail: for each case, the reference solution must pass every rule, and each defective output must fail
exactly the rules it was made to break (and no others).

    python3 evals/studio/game-art/build/selfcheck.py [CASE_ID_PREFIX]
"""
import json, pathlib, shutil, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "lib"))
import make_cases as M
import studio_lib


def tree(case):
    d = pathlib.Path(tempfile.mkdtemp(prefix="studio-"))
    shutil.copytree(M.CASES_DIR / case["id"] / "inputs", d / "inputs") if (M.CASES_DIR / case["id"] / "inputs").is_dir() else (d / "inputs").mkdir()
    return d


def run(case, d):
    out = studio_lib.run_case(d, M.CASES_DIR / case["id"] / "expected.json")
    return {r["id"]: r for r in out["rules"]}


def main(argv):
    prefix = argv[0] if argv else ""
    bad = 0
    for case in M.CASES:
        if not case["id"].startswith(prefix):
            continue
        # the checker script itself, as the runner will call it
        d = tree(case)
        case["reference"](d)
        res = run(case, d)
        failed = sorted(k for k, v in res.items() if not v["pass"])
        ok = not failed
        proc = subprocess.run([sys.executable, str(M.CASES_DIR / case["id"] / "check.py"), str(d), str(M.CASES_DIR / case["id"] / "expected.json")], capture_output=True, text=True)
        ok2 = (proc.returncode == 0) == ok and json.loads(proc.stdout)["case"] == case["id"]
        print(f"{'ok  ' if ok and ok2 else 'FAIL'} {case['id']}: reference passes all {len(res)} rules" + ("" if ok else f"  -> failed {failed}: {[res[k]['measured'] for k in failed]}"))
        bad += not (ok and ok2)
        shutil.rmtree(d)
        for name, fn, expect in case["defects"]:
            d = tree(case)
            case["reference"](d)      # start from the correct output, then break only what this defect breaks
            fn(d)
            res = run(case, d)
            failed = {k for k, v in res.items() if not v["pass"]}
            good = failed == set(expect)
            print(f"  {'ok  ' if good else 'FAIL'} {name}: fails {sorted(failed)}" + ("" if good else f"  (wanted {sorted(expect)})"))
            bad += not good
            shutil.rmtree(d)
    print("selfcheck:", "FAILED" if bad else "all checkers pass the reference and fail each defect for the right reason", f"({bad})" if bad else "")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
