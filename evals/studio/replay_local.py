#!/usr/bin/env python3
"""A local stand-in for the runner's replay test: for every tree in a bundle written by `selfcheck.py --emit DIR`, stage a scratch directory the way the lane does
(the case's inputs, the output tree, `.run/` in the runner's format), run the case's `check.py` the way the lane does (from the answers directory, a clean environment,
`STUDIO_LIB` pointing at the packed library) and require the verdict to equal the one the host checker gave. It does not test isolation, only that the bundle, the
environment and the file formats are enough for the checkers.

    python3 evals/studio/replay_local.py REPLAY_DIR LIB_BUNDLE_DIR CASES_DIR [CASE_ID_PREFIX]
"""
import json, os, pathlib, shutil, subprocess, sys, tarfile, tempfile, time


def stage(case_dir, tree, tar_path, scratch):
    shutil.copytree(case_dir / "inputs", scratch / "inputs") if (case_dir / "inputs").is_dir() else (scratch / "inputs").mkdir(parents=True)
    with tarfile.open(tar_path) as tar:
        tar.extractall(scratch, filter="data")
    run = scratch / ".run"
    run.mkdir()
    body = []
    for role, text in tree["transcript"]:
        body.append(f"## {role}\n\n" + "\n".join("> " + l for l in text.splitlines()) + "\n")
    (run / "transcript.md").write_text("\n".join(body))
    (run / "proxy.log").write_text("".join(json.dumps({"host": r["host"], "method": "POST", "status": r["status"], "bytes": 0, "time": time.time()}, sort_keys=True) + "\n" for r in tree["proxy"]))
    (run / "usage.json").write_text("{}")
    (run / "run.json").write_text("{}")


def main(argv):
    if len(argv) < 4:
        print(__doc__)
        return 2
    replay, lib, cases = map(pathlib.Path, argv[1:4])
    prefix = argv[4] if len(argv) > 4 else ""
    bad = total = 0
    for cdir in sorted(replay.iterdir()):
        if not cdir.name.startswith(prefix) or not (cdir / "replay.json").is_file():
            continue
        spec = json.loads((cdir / "replay.json").read_text())
        for tree in spec["trees"]:
            total += 1
            with tempfile.TemporaryDirectory(prefix="replay-") as tmp:
                tmp = pathlib.Path(tmp)
                scratch = tmp / "scratch"
                scratch.mkdir()
                answers = tmp / "answers"
                answers.mkdir()
                for f in ("check.py", "expected.json"):
                    shutil.copyfile(cases / spec["case"] / f, answers / f)
                stage(cases / spec["case"], tree, cdir / tree["tar"], scratch)
                home = tmp / "home"
                (home / "tmp").mkdir(parents=True)
                if os.environ.get("REPLAY_TMP_INSIDE"):      # the runner's first draft put the checker's TMPDIR in the scratch tree
                    (scratch / "tmp").mkdir(exist_ok=True)
                env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home), "LANG": "C.UTF-8", "TMPDIR": str(scratch / "tmp") if os.environ.get("REPLAY_TMP_INSIDE") else str(home / "tmp"), "STUDIO_LIB": str(lib)}
                for k in ("LD_LIBRARY_PATH", "TESSDATA_PREFIX", "STUDIO_NODE_MODULES", "STUDIO_CHROME", "STUDIO_FFMPEG", "STUDIO_NODE"):
                    if k in os.environ:
                        env[k] = os.environ[k]
                r = subprocess.run([sys.executable, str(answers / "check.py"), str(scratch), str(answers / "expected.json")], cwd=scratch, env=env, capture_output=True, text=True, timeout=300)
                try:
                    out = json.loads(r.stdout)
                    for rule in out["rules"]:
                        assert set(rule) == {"id", "pass", "measured", "threshold"}, "rule keys " + str(sorted(rule))
                    got = {rule["id"]: rule["pass"] for rule in out["rules"]}
                    assert out["case"] == spec["case"]
                except Exception as e:  # noqa: BLE001
                    got, err = None, f"{type(e).__name__}: {e} | {r.stderr.strip()[-200:]}"
                good = got == tree["expect"]
                bad += not good
                print(f"{'ok  ' if good else 'FAIL'} {spec['case']} / {tree['name']}" + ("" if good else f"  got {got if got is not None else err}  wanted {tree['expect']}"))
    print(f"replay: {total - bad} of {total} trees give the host verdict in a lane-like run")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
