#!/usr/bin/env python3
"""The selfcheck shared by every studio case set: for each case, the reference solution must pass every gated rule, and each defective output must fail
exactly the rules it was made to break (and no others). A set's build/selfcheck.py calls main(make_cases_module, argv)."""
import json, pathlib, shutil, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import studio_lib


def tree(M, case):
    d = pathlib.Path(tempfile.mkdtemp(prefix="studio-"))
    shutil.copytree(M.CASES_DIR / case["id"] / "inputs", d / "inputs") if (M.CASES_DIR / case["id"] / "inputs").is_dir() else (d / "inputs").mkdir()
    return d


def run(M, case, d):
    out = studio_lib.run_case(d, M.CASES_DIR / case["id"] / "expected.json")
    return {r["id"]: r for r in out["rules"]}


def main(M, argv):
    prefix = argv[0] if argv else ""
    try:
        import audio_rules
        print("ffmpeg:", audio_rules._run(["-version"]).stdout.splitlines()[0])
    except Exception:  # noqa: BLE001
        pass
    bad = 0
    for case in M.CASES:
        if not case["id"].startswith(prefix):
            continue
        # the checker script itself, as the runner will call it
        d = tree(M, case)
        case["reference"](d)
        res = run(M, case, d)
        failed = sorted(k for k, v in res.items() if not v["pass"] and v.get("gate", True))
        ok = not failed
        proc = subprocess.run([sys.executable, str(M.CASES_DIR / case["id"] / "check.py"), str(d), str(M.CASES_DIR / case["id"] / "expected.json")], capture_output=True, text=True)
        ok2 = (proc.returncode == 0) == ok and json.loads(proc.stdout)["case"] == case["id"]
        print(f"{'ok  ' if ok and ok2 else 'FAIL'} {case['id']}: reference passes all {len(res)} rules" + ("" if ok else f"  -> failed {failed}: {[res[k]['measured'] for k in failed]}"))
        bad += not (ok and ok2)
        shutil.rmtree(d)
        for name, fn, expect in case["defects"]:
            d = tree(M, case)
            case["reference"](d)      # start from the correct output, then break only what this defect breaks
            fn(d)
            res = run(M, case, d)
            failed = {k for k, v in res.items() if not v["pass"] and v.get("gate", True)}
            good = failed == set(expect)
            print(f"  {'ok  ' if good else 'FAIL'} {name}: fails {sorted(failed)}" + ("" if good else f"  (wanted {sorted(expect)})"))
            bad += not good
            shutil.rmtree(d)
    print("selfcheck:", "FAILED" if bad else "all checkers pass the reference and fail each defect for the right reason", f"({bad})" if bad else "")
    return 1 if bad else 0
