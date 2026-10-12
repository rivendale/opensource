#!/usr/bin/env python3
"""The selfcheck shared by every studio case set: for each case, the reference solution must pass every gated rule, and each defective output must fail
exactly the rules it was made to break (and no others). A set's build/selfcheck.py calls main(make_cases_module, argv)."""
import json, pathlib, re, shutil, subprocess, sys, tarfile, tempfile

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


def emit_tree(M, case, name, d, verdict, out):
    """For the runner's replay test: the output tree (without inputs/ and .run/, which the runner stages and writes itself), the assistant turns and relay requests the
    transcript and proxy log of this tree show, and the verdict the host checker gave it."""
    cdir = pathlib.Path(out) / case["id"]
    cdir.mkdir(parents=True, exist_ok=True)
    tar_path = cdir / f"{name}.tar"
    with tarfile.open(tar_path, "w", format=tarfile.PAX_FORMAT) as tar:
        for f in sorted(pathlib.Path(d).rglob("*")):
            rel = f.relative_to(d)
            if rel.parts[0] in ("inputs", ".run") or f.is_symlink():
                continue
            ti = tar.gettarinfo(str(f), arcname=str(rel))
            ti.uid = ti.gid = 0
            ti.uname = ti.gname = ""
            ti.mtime = 0
            if f.is_file():
                with f.open("rb") as fh:
                    tar.addfile(ti, fh)
            else:
                tar.addfile(ti)
    transcript, proxy = [], []
    if (pathlib.Path(d) / ".run/transcript.md").is_file():
        transcript = [[role, text] for role, text in (studio_lib.turns(d) or [])]
    pl = pathlib.Path(d) / ".run/proxy.log"
    if pl.is_file():
        for line in pl.read_text().splitlines():
            m = re.search(r"CONNECT ([a-z0-9.-]+):\d+ (\d+)", line)
            if m:
                proxy.append({"host": m.group(1), "status": int(m.group(2))})
    return {"name": name, "tar": tar_path.name, "transcript": transcript, "proxy": proxy,
            "expect": {rid: v["pass"] for rid, v in verdict.items()}}


def main(M, argv):
    argv = list(argv)
    emit = None
    if "--emit" in argv:
        i = argv.index("--emit")
        emit, argv = argv[i + 1], argv[:i] + argv[i + 2:]
    explicit, skip = "--coverage" in argv, "--no-coverage" in argv
    argv = [a for a in argv if a not in ("--coverage", "--no-coverage")]
    prefix = argv[0] if argv else ""
    # The gate: a full run (no case prefix) also requires every rule TYPE in use to be failed by at least one defect somewhere in the set; a rule type that nothing makes
    # fail may not be able to. A prefix run sees only part of the set, so it reports coverage only when asked (--coverage).
    coverage = explicit or (not prefix and not skip)
    replay = {}
    try:
        import audio_rules
        print("ffmpeg:", audio_rules._run(["-version"]).stdout.splitlines()[0])
    except Exception:  # noqa: BLE001
        pass
    bad = 0
    all_types, failed_types = {}, set()
    for case in M.CASES:
        if not case["id"].startswith(prefix):
            continue
        failed_by_a_defect = set()
        # the checker script itself, as the runner will call it
        d = tree(M, case)
        case["reference"](d)
        res = run(M, case, d)
        failed = sorted(k for k, v in res.items() if not v["pass"])
        ok = not failed
        proc = subprocess.run([sys.executable, str(M.CASES_DIR / case["id"] / "check.py"), str(d), str(M.CASES_DIR / case["id"] / "expected.json")], capture_output=True, text=True)
        ok2 = (proc.returncode == 0) == ok and json.loads(proc.stdout)["case"] == case["id"]
        if emit:
            replay.setdefault(case["id"], []).append(emit_tree(M, case, "reference", d, res, emit))
        print(f"{'ok  ' if ok and ok2 else 'FAIL'} {case['id']}: reference passes all {len(res)} rules" + ("" if ok else f"  -> failed {failed}: {[res[k]['measured'] for k in failed]}"))
        bad += not (ok and ok2)
        shutil.rmtree(d)
        for name, fn, expect in case["defects"]:
            d = tree(M, case)
            case["reference"](d)      # start from the correct output, then break only what this defect breaks
            fn(d)
            res = run(M, case, d)
            failed = {k for k, v in res.items() if not v["pass"]}
            if emit:
                replay[case["id"]].append(dict(emit_tree(M, case, "defect-%02d" % len(replay[case["id"]]), d, res, emit), description=name))
            failed_by_a_defect |= failed
            good = failed == set(expect)
            print(f"  {'ok  ' if good else 'FAIL'} {name}: fails {sorted(failed)}" + ("" if good else f"  (wanted {sorted(expect)})"))
            bad += not good
            shutil.rmtree(d)
        rules_here = json.loads((M.CASES_DIR / case["id"] / "expected.json").read_text())["rules"]
        for r in rules_here:
            all_types.setdefault(r["type"], []).append(case["id"])
            if r["id"] in failed_by_a_defect:
                failed_types.add(r["type"])
    if coverage:
        never = {ty: cases for ty, cases in all_types.items() if ty not in failed_types}
        print(f"coverage: {len(all_types)} rule types in use, {len(failed_types)} failed by at least one defect somewhere in the set")
        for ty, cases in sorted(never.items()):
            print(f"  NEVER FAILED: {ty} (used in {len(cases)} case(s): {', '.join(cases[:3])}{' ...' if len(cases) > 3 else ''})")
        bad += bool(never)
    if emit:
        for cid, trees in replay.items():
            (pathlib.Path(emit) / cid / "replay.json").write_text(json.dumps({"case": cid, "trees": trees}, indent=2) + "\n")
        print(f"replay bundles for {len(replay)} cases written to {emit}")
    print("selfcheck:", "FAILED" if bad else "all checkers pass the reference and fail each defect for the right reason", f"({bad})" if bad else "")
    return 1 if bad else 0
