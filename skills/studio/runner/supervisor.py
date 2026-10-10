"""Trusted PID 1: keep tmpfs alive, remove all agent processes, then admit answers."""
import base64
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tarfile
import tempfile
import time

from common import VERSION, encode, read_frame


def send(kind, **values):
    sys.stdout.buffer.write(encode({"type": kind, **values}))
    sys.stdout.buffer.flush()


def unprivileged(uid):
    def drop():
        os.setgroups([])
        os.setgid(uid)
        os.setuid(uid)
        os.umask(0o022)
    return drop


def remaining():
    return [int(p.name) for p in Path("/proc").iterdir() if p.name.isdigit() and int(p.name) != os.getpid()]


def drain():
    """PID namespace is private. Kill every process, not only a process group."""
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        for pid in remaining():
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        while True:
            try:
                pid, _ = os.waitpid(-1, os.WNOHANG)
                if pid == 0:
                    break
            except ChildProcessError:
                break
        if not remaining():
            send("drained", processes=0)
            return
        time.sleep(0.02)
    raise RuntimeError("agent descendants remain")


def clean_env(home):
    return {"PATH": "/usr/local/bin:/usr/bin:/bin:/opt/tools/bin", "HOME": home,
            "LANG": "C.UTF-8", "STUDIO_FFMPEG": "/opt/tools/bin/ffmpeg", "TMPDIR": "/scratch/tmp"}


def tools():
    versions = {"python": sys.version.split()[0], "agent": VERSION}
    for name, command in {
        "ffmpeg": ["/opt/tools/bin/ffmpeg", "-version"],
        "tesseract": ["tesseract", "--version"],
        "strace": ["strace", "--version"],
        "numpy": ["python3", "-I", "-c", "import numpy; print(numpy.__version__)"]
    }.items():
        result = subprocess.run(command, env=clean_env("/home/studio"), capture_output=True, timeout=10)
        if result.returncode:
            raise RuntimeError("required image tool unavailable")
        versions[name] = result.stdout.decode("utf-8").splitlines()[0]
    if not versions["ffmpeg"].startswith("ffmpeg version 7.0.2 "):
        raise RuntimeError("ffmpeg 7.0.2 required")
    # Reap tool inventory children before the agent phase.
    return versions


def verify_limits(limits):
    root = Path("/sys/fs/cgroup")
    if int((root / "memory.max").read_text()) != limits["memory"]:
        raise RuntimeError("memory cgroup limit missing")
    if int((root / "pids.max").read_text()) != limits["processes"]:
        raise RuntimeError("process cgroup limit missing")
    quota, period = (root / "cpu.max").read_text().split()
    if quota == "max" or int(quota) / int(period) != limits["cpus"]:
        raise RuntimeError("CPU cgroup limit missing")
    if (root / "memory.swap.max").read_text().strip() != "0":
        raise RuntimeError("swap must be disabled")
    scratch = os.statvfs("/scratch")
    if scratch.f_blocks * scratch.f_frsize > limits["scratch"]:
        raise RuntimeError("scratch tmpfs exceeds limit")


def audit_records():
    # strace data arguments are raw pointer addresses; headers/bodies are never read.
    # Keep only refused network calls and IP addresses, never arbitrary input strings.
    import re
    result = []
    trace = Path("/audit/network.trace")
    if not trace.is_file():
        raise RuntimeError("network audit missing")
    with trace.open(errors="replace") as stream:
        for line in stream:
            if "= -1 " not in line or not any(x in line for x in ("connect(", "sendto(", "sendmsg(")):
                continue
            address = re.search(r'inet_addr\("([0-9.]+)"\)', line)
            result.append({"host": address.group(1) if address else "network",
                           "method": "CONNECT", "status": "DENIED", "bytes": 0, "time": time.time()})
            if len(result) > 5000:
                raise RuntimeError("network audit size limit")
    return result


def limits_hit():
    root = Path("/sys/fs/cgroup")
    hits = []
    for file, keys, name in [("pids.events", {"max"}, "process count"),
                              ("memory.events", {"max", "oom", "oom_kill"}, "memory")]:
        values = dict(line.split() for line in (root / file).read_text().splitlines())
        if any(int(values.get(key, "0")) > 0 for key in keys):
            hits.append(name)
    with Path("/audit/network.trace").open(errors="replace") as stream:
        if any("ENOSPC" in line for line in stream):
            hits.append("scratch or temporary disk")
    return hits


def snapshot():
    # Reject links and special files before tar; never follow attacker-created links.
    for folder, dirs, files in os.walk("/scratch", followlinks=False):
        for name in dirs + files:
            path = Path(folder) / name
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise RuntimeError("scratch contains a link or special file")
    with tempfile.TemporaryFile(dir="/audit") as archive:
        with tarfile.open(fileobj=archive, mode="w|") as tar:
            tar.add("/scratch", arcname="scratch", recursive=True)
        archive.seek(0)
        send("archive-start")
        while True:
            block = archive.read(65536)
            if not block:
                break
            send("archive-chunk", data=base64.b64encode(block).decode())
        send("archive-end")


def main():
    if os.getpid() != 1 or os.getuid() != 0:
        raise RuntimeError("supervisor must be PID 1 as container root")
    for path, uid, mode in [("/scratch", 1000, 0o755), ("/home/studio", 1000, 0o700),
                            ("/scratch/tmp", 1000, 0o700),
                            ("/scratch/.run", 0, 0o700), ("/audit", 0, 0o700)]:
        Path(path).mkdir(exist_ok=True)
        os.chown(path, uid, uid)
        os.chmod(path, mode)
    versions = tools()
    start = read_frame(sys.stdin.buffer)
    if start["type"] != "start" or start["mode"] not in {"run", "probe"}:
        raise ValueError("expected start frame")
    verify_limits(start["limits"])
    command = (["python3", "-I", "/opt/studio/probe.py"] if start["mode"] == "probe" else
               ["python3", "/opt/studio/agent.py", "--model", start["model"],
                "--host", start["host"], "--path", start["path"], "--turns", str(start["turns"])])
    send("ready", versions=versions)
    # Root tracer owns the audit file; -u launches the program with no root caps.
    process = subprocess.Popen(["strace", "-D", "-f", "-e", "trace=connect,sendto,sendmsg,write,writev,pwrite64,truncate,ftruncate",
                                "-e", "raw=sendto,sendmsg,write,writev,pwrite64", "-o", "/audit/network.trace",
                                "-u", "studio", *command], cwd="/scratch", env=clean_env("/home/studio"),
                               stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.DEVNULL)
    while True:
        line = process.stdout.readline(2 * 1024 * 1024 + 1)
        if not line:
            break
        if len(line) > 2 * 1024 * 1024 or not line.endswith(b"\n"):
            raise RuntimeError("agent event exceeds protocol limit")
        event = json.loads(line)
        if event.get("pid") != process.pid:
            raise RuntimeError("agent process identity mismatch")
        send("event", event=event)
        if event["type"] in {"finished", "failed", "probe"}:
            break
    code = process.wait(timeout=5)
    drain()
    send("agent-exit", code=code, audit=audit_records(), limits_hit=limits_hit())
    capture = read_frame(sys.stdin.buffer)
    if capture["type"] != "capture":
        raise ValueError("expected capture frame")
    # Protected mount: agent cannot plant symlinks or write runner claims here.
    os.chmod("/scratch/.run", 0o755)
    allowed = {"transcript.md", "proxy.log", "usage.json", "run.json"}
    total = 0
    seen = set()
    while True:
        frame = read_frame(sys.stdin.buffer)
        if frame["type"] == "capture-end":
            break
        name = frame["name"]
        if frame["type"] != "capture-chunk" or name not in allowed:
            raise ValueError("invalid capture name or frame")
        data = base64.b64decode(frame["data"], validate=True)
        total += len(data)
        if total > 24 * 1024 * 1024:
            raise ValueError("capture size limit")
        with Path("/scratch/.run", name).open("ab") as stream:
            stream.write(data)
        seen.add(name)
    if seen != allowed:
        raise ValueError("missing capture file")
    snapshot()
    send("answers-ready", processes=0)
    answer = read_frame(sys.stdin.buffer)
    if answer["type"] == "abort":
        return 1
    if answer["type"] != "check" or remaining():
        raise ValueError("answers arrived in wrong phase")
    Path("/audit/answers").mkdir(mode=0o755)
    for name in ["check.py", "expected.json"]:
        Path("/audit/answers", name).write_bytes(base64.b64decode(answer[name], validate=True))
    # Checker is a different unprivileged UID. It cannot alter .run/ claims.
    os.chmod("/audit", 0o755)
    for folder, dirs, files in os.walk("/scratch", followlinks=False):
        if Path(folder) == Path("/scratch/.run") or Path("/scratch/inputs") in Path(folder).parents or folder == "/scratch/inputs":
            continue
        os.chown(folder, 1001, 1001)
        for name in files:
            path = Path(folder) / name
            if not str(path).startswith("/scratch/.run/") and path.name != "brief.md":
                os.chown(path, 1001, 1001)
    with Path("/audit/checker.out").open("wb") as output:
        process = subprocess.Popen(["python3", "/audit/answers/check.py", "/scratch", "/audit/answers/expected.json"],
                                   cwd="/scratch", env=clean_env("/home/checker"), preexec_fn=unprivileged(1001),
                                   stdout=output, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
        deadline = time.monotonic() + 120
        while process.poll() is None:
            if time.monotonic() > deadline or output.tell() > 1024 * 1024:
                raise RuntimeError("checker time or output limit")
            time.sleep(0.05)
    code = process.returncode
    drain()
    content = Path("/audit/checker.out").read_bytes()
    if len(content) > 1024 * 1024:
        raise RuntimeError("checker output too large")
    send("checker", code=code, output=content.decode("utf-8"), limits_hit=limits_hit())
    snapshot()
    send("done")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Host marks generic failure and destroys the container; never spill payloads.
        send("failed", reason="supervisor isolation or protocol failure")
        sys.exit(1)
