#!/usr/bin/env python3
"""Run synthetic isolation probes against the actual selected image and runtime."""
import argparse
from pathlib import Path
import subprocess
import sys
import tempfile


CHECKER = '''import json, pathlib, sys
scratch = pathlib.Path(sys.argv[1])
expected = json.loads(pathlib.Path(sys.argv[2]).read_text())
log = [json.loads(line) for line in (scratch / '.run/proxy.log').read_text().splitlines()]
rules = [
 {'id': 'network-denial-audited', 'pass': any(row['status'] == 'DENIED' for row in log),
  'measured': len(log), 'threshold': 'at least one denied connection'},
 {'id': 'captures-before-checker', 'pass': all((scratch / '.run' / name).is_file() for name in
  ['transcript.md', 'proxy.log', 'usage.json', 'run.json']), 'measured': 'capture files', 'threshold': 'all four'},
 {'id': 'answers-after-drain', 'pass': expected['phase'] == 'after-drain',
  'measured': expected['phase'], 'threshold': 'after-drain'}]
print(json.dumps({'case': 'runner-selftest', 'rules': rules}))
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="studio-probe-case-") as temp:
        case = Path(temp)
        (case / "inputs").mkdir()
        executable = case / "inputs/tool"
        executable.write_text("#!/bin/sh\nexit 0\n")
        executable.chmod(0o755)
        (case / "brief.md").write_text("Synthetic runtime isolation probe. No model or credentials.\n")
        (case / "SKILL.md").write_text("Synthetic runtime isolation probe.\n")
        (case / "check.py").write_text(CHECKER)
        (case / "expected.json").write_text('{"phase":"after-drain"}\n')
        return subprocess.run([sys.executable, str(here / "run.py"), "probe", "--image", args.image,
                               "--store", str(args.store), "--case", str(case), "--case-id", "runner-selftest",
                               "--skill", str(case / "SKILL.md"), "--output", str(args.output)],
                              env={"PATH": "/usr/bin:/bin"}, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
