"""Synthetic denying-direction probes, unrelated to studio acceptance cases."""
import json
import os
from pathlib import Path
import socket
import subprocess
import time


def refused(function):
    try:
        function()
        return False
    except (OSError, PermissionError):
        return True


def network():
    with socket.socket() as connection:
        connection.settimeout(1)
        connection.connect(("198.51.100.1", 443))


def main():
    rules = {"network": refused(network),
             "root-write": refused(lambda: Path("/forbidden").write_text("probe")),
             "credential-file": refused(lambda: Path("/root/.aws/credentials").read_bytes()),
             "early-answer-mount": all(not Path(p).exists() for p in
                                       ["/audit/answers", "/answers", "/scratch/check.py", "/scratch/expected.json"]),
             "empty-home": not list(Path(os.environ["HOME"]).iterdir()),
             "clean-env": set(os.environ) == {"PATH", "HOME", "LANG", "STUDIO_FFMPEG", "TMPDIR"},
             "executable-input": subprocess.run(["/scratch/inputs/tool"], check=False).returncode == 0,
             "unprivileged": os.getuid() == 1000,
             "no-agent-capabilities": "CapEff:\t0000000000000000" in Path("/proc/self/status").read_text(),
             "credential-sentinel": refused(lambda: Path("/credential-sentinel").read_bytes()),
             "capture-protected": refused(lambda: Path("/scratch/.run/injected").write_text("probe")),
             "inputs-read-only": refused(lambda: Path("/scratch/inputs/injected").write_text("probe"))}
    # Detached descendant survives the agent itself; PID 1 must kill/reap it.
    pid = os.fork()
    if pid == 0:
        os.setsid()
        os.close(1)
        os.close(2)
        time.sleep(60)
        os._exit(0)
    print(json.dumps({"type": "probe", "pid": os.getpid(), "rules": rules}), flush=True)
    return 0 if all(rules.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
