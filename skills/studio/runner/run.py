#!/usr/bin/env python3
"""Fail-closed Podman studio runner. Requires an already-loaded pinned image."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import uuid

from common import VERSION, MAX_FRAME, checker_result, encode, leak_reason, plain_tree, sha256
from proxy import Relay

CAPTURE_RESERVE = 32 * 1024 * 1024


class Frames:
    def __init__(self, process, deadline):
        self.process, self.deadline = process, deadline
        self.pending = bytearray()
        self.selector = selectors.DefaultSelector()
        self.selector.register(process.stdout, selectors.EVENT_READ)

    def next(self):
        while True:
            newline = self.pending.find(b"\n")
            if newline >= 0:
                if newline >= MAX_FRAME:
                    raise ValueError("protocol size limit")
                line = bytes(self.pending[:newline])
                del self.pending[:newline + 1]
                return json.loads(line)
            if len(self.pending) > MAX_FRAME:
                raise ValueError("protocol size limit")
            if time.monotonic() >= self.deadline:
                raise TimeoutError("wall time limit")
            if self.selector.select(min(0.2, self.deadline - time.monotonic())):
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    raise RuntimeError("supervisor ended early")
                self.pending.extend(chunk)


def command(base, arguments, timeout=30):
    process = subprocess.run(base + arguments, env=base.env, capture_output=True, timeout=timeout)
    if process.returncode:
        # Runtime diagnostics might contain private host paths; do not publish them.
        raise RuntimeError("runtime command refused or unavailable")
    return process.stdout


class Runtime(list):
    def __init__(self, store, root):
        executable = shutil.which("podman")
        if not executable:
            raise RuntimeError("Podman missing")
        # Podman persists its runroot/temporary-directory choices in the store DB.
        # Keep those stable across runs; only the runtime HOME is disposable.
        token = hashlib.sha256(str(store.resolve()).encode()).hexdigest()[:12]
        # Podman 4 has a 50-character runroot limit. Keep socket paths short too.
        state = Path(tempfile.gettempdir()) / ("studio-rt-" + token)
        state.mkdir(exist_ok=True, mode=0o700)
        if state.is_symlink() or state.stat().st_uid != os.getuid() or state.stat().st_mode & 0o077:
            raise RuntimeError("unsafe runtime-state directory")
        marker = state / "store-path"
        if marker.exists() and marker.read_text() != str(store.resolve()):
            raise RuntimeError("runtime-state store mismatch")
        marker.write_text(str(store.resolve()))
        # The caller delegates its scope; no user bus or session configuration is inherited.
        super().__init__([executable, "--cgroup-manager=cgroupfs", "--root", str(store), "--runroot", str(state / "run")])
        home = root / "runtime-home"
        home.mkdir()
        xdg = state / "xdg"
        xdg.mkdir(mode=0o700, exist_ok=True)
        self.env = {"PATH": "/usr/bin:/bin", "HOME": str(home), "XDG_RUNTIME_DIR": str(xdg)}


def image_identity(runtime, image):
    if not re.fullmatch(r"[a-zA-Z0-9./:_-]+@sha256:[a-f0-9]{64}", image):
        raise ValueError("image must be a fully qualified immutable digest reference")
    value = json.loads(command(runtime, ["image", "inspect", image]))[0]
    if image not in value.get("RepoDigests", []) and value.get("Digest") != image.split("@", 1)[1]:
        raise ValueError("selected image digest is not loaded in the explicit store")
    labels = value.get("Config", {}).get("Labels", {}) or {}
    if labels.get("studio.runner") != VERSION:
        raise ValueError("image lacks the pinned studio runner label")
    sources = {p.name: sha256(p) for p in Path(__file__).parent.glob("*.py") if p.name != "run.py"}
    if labels.get("studio.sources") != json.dumps(sources, sort_keys=True, separators=(",", ":")):
        raise ValueError("image sources differ from this runner")
    return {"reference": image, "id": value["Id"], "sources": sources}


def runtime_identity(runtime):
    value = json.loads(command(runtime, ["info", "--format=json"]))
    host = value["host"]
    return {"podman": value["version"]["Version"], "oci_runtime": host["ociRuntime"]["version"].splitlines()[0],
            "cgroup_version": host["cgroupVersion"], "controllers": host["cgroupControllers"],
            "rootless": host["security"]["rootless"], "seccomp": host["security"]["seccompEnabled"]}


def sandbox_args(image, name, seed, skill, egress, limits, input_bytes):
    size = limits["scratch"] - CAPTURE_RESERVE - input_bytes
    if size < 64 * 1024 * 1024:
        raise ValueError("scratch limit too small for captures and inputs")
    args = ["run", "--name", name, "--pull=never", "--interactive", "--network=none",
            "--read-only", "--read-only-tmpfs=false", "--unsetenv-all", "--image-volume=ignore",
            "--user=0:0", "--cap-drop=all", "--cap-add=SETUID", "--cap-add=SETGID",
            "--cap-add=CHOWN", "--cap-add=FOWNER", "--cap-add=DAC_OVERRIDE",
            "--cap-add=KILL", "--cap-add=SYS_PTRACE", "--security-opt=no-new-privileges",
            "--pid=private", "--ipc=private", "--cgroupns=private", "--hostname=studio",
            "--pids-limit=" + str(limits["processes"]), "--cpus=" + str(limits["cpus"]),
            "--memory=" + str(limits["memory"]), "--memory-swap=" + str(limits["memory"]),
            "--ulimit=nofile=1024:1024",
            "--tmpfs=/scratch:rw,nosuid,nodev,size=" + str(size) + ",mode=0755",
            "--tmpfs=/scratch/.run:rw,nosuid,nodev,noexec,size=" + str(CAPTURE_RESERVE) + ",mode=0700",
            "--tmpfs=/home/studio:rw,nosuid,nodev,size=33554432,mode=0700",
            "--tmpfs=/home/checker:rw,nosuid,nodev,size=33554432,mode=0700",
            "--tmpfs=/audit:rw,nosuid,nodev,noexec,size=" + str(limits["scratch"] + 128 * 1024 * 1024) + ",mode=0700",
            "--mount=type=bind,src=" + str(seed / "inputs") + ",dst=/scratch/inputs,ro=true",
            "--mount=type=bind,src=" + str(seed / "brief.md") + ",dst=/scratch/brief.md,ro=true",
            "--mount=type=bind,src=" + str(skill) + ",dst=/skill/SKILL.md,ro=true",
            "--mount=type=bind,src=" + str(egress) + ",dst=/egress,ro=true",
            "--entrypoint=/usr/bin/python3", image, "/opt/studio/supervisor.py"]
    return args


def mount_receipt(runtime, name, allowed):
    value = json.loads(command(runtime, ["inspect", name]))[0]
    binds = [m for m in value["Mounts"] if m["Type"] == "bind"]
    if {m["Source"] for m in binds} != {str(p) for p in allowed} or any(m.get("RW") for m in binds):
        raise RuntimeError("unexpected or writable bind mount")
    return [{"destination": m["Destination"], "read_only": True} for m in binds]


def archive(frames, destination, size_limit):
    # Host extraction never trusts tar paths or link targets.
    raw = destination.with_suffix(".tar")
    size = 0
    with raw.open("xb") as stream:
        while True:
            frame = frames.next()
            if frame["type"] == "archive-end":
                break
            if frame["type"] != "archive-chunk":
                raise ValueError("bad archive protocol")
            data = base64.b64decode(frame["data"], validate=True)
            size += len(data)
            if size > size_limit + 64 * 1024 * 1024:
                raise ValueError("archive size limit")
            stream.write(data)
    destination.mkdir()
    total = 0
    with tarfile.open(raw) as tar:
        for member in tar:
            parts = Path(member.name).parts
            if not parts or parts[0] != "scratch" or ".." in parts or Path(member.name).is_absolute():
                raise ValueError("unsafe archive path")
            if not (member.isfile() or member.isdir()) or member.size < 0:
                raise ValueError("links and special files are refused")
            total += member.size
            if total > size_limit:
                raise ValueError("scratch size limit")
            target = destination.joinpath(*parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("xb") as output, tar.extractfile(member) as source:
                    shutil.copyfileobj(source, output, 65536)
                target.chmod(0o755 if member.mode & 0o111 else 0o644)
    raw.unlink()
    return destination / "scratch"


def capture(process, files):
    process.stdin.write(encode({"type": "capture"}))
    for name, content in files.items():
        data = content.encode("utf-8")
        for offset in range(0, max(1, len(data)), 65536):
            process.stdin.write(encode({"type": "capture-chunk", "name": name,
                                      "data": base64.b64encode(data[offset:offset + 65536]).decode()}))
    process.stdin.write(encode({"type": "capture-end"}))
    process.stdin.flush()


def run(args):
    result = {"runner": VERSION, "status": "failed", "reason": "runner preflight or isolation failure",
              "runner_sha256": sha256(__file__),
              "case": args.case_id, "agent": VERSION, "model": args.model, "limits": args.limits}
    # No overwritten results and no mixed case runs.
    args.output.mkdir(parents=True, exist_ok=False)
    os.chmod(args.output, 0o700)
    started = time.monotonic()
    process = None
    relay = None
    thread = None
    runtime = None
    name = "studio-" + uuid.uuid4().hex
    key_values = []
    root = Path(tempfile.mkdtemp(prefix="studio-private-"))
    try:
        runtime = Runtime(args.store, root)
        try:
            result["runtime"] = runtime_identity(runtime)
            host = result["runtime"]
            if (host["cgroup_version"] != "v2" or not {"cpu", "memory", "pids"} <= set(host["controllers"])
                    or not host["rootless"] or not host["seccomp"]):
                raise RuntimeError("runtime controls unavailable")
        except RuntimeError:
            result["reason"] = "runtime unavailable or missing delegated cgroup v2 cpu, memory, pids or seccomp"
            raise
        result["image"] = image_identity(runtime, args.image)
        if args.mode == "run":
            receipt = json.loads(args.selftest.read_text())
            if (receipt.get("status") != "passed" or receipt.get("image") != result["image"]
                    or receipt.get("runner") != VERSION or receipt.get("runner_sha256") != result["runner_sha256"]):
                raise ValueError("passing selftest for this exact image and runner required")
        seed = root / "seed"
        seed.mkdir()
        brief = args.case / "brief.md"
        if not brief.is_file() or brief.is_symlink() or brief.stat().st_size > 256 * 1024:
            raise ValueError("unsafe or oversized brief")
        (seed / "brief.md").write_bytes(brief.read_bytes())
        (seed / "brief.md").chmod(0o644)
        input_bytes = plain_tree(args.case / "inputs", seed / "inputs") + brief.stat().st_size
        private_answers = root / "private-answers"
        private_answers.mkdir(mode=0o700)
        for file in ["check.py", "expected.json"]:
            source = args.case / file
            if source.is_symlink() or not source.is_file() or source.stat().st_size > 512 * 1024:
                raise ValueError("unsafe or oversized checker answers")
            (private_answers / file).write_bytes(source.read_bytes())
            result[file + "_sha256"] = sha256(private_answers / file)
        skill = root / "SKILL.md"
        if args.skill.is_symlink() or not args.skill.is_file() or args.skill.stat().st_size > 256 * 1024:
            raise ValueError("unsafe or oversized skill")
        skill.write_bytes(args.skill.read_bytes())
        skill.chmod(0o644)
        result["skill_sha256"] = sha256(skill)
        result["brief_sha256"] = sha256(seed / "brief.md")
        egress = root / "egress"
        egress.mkdir(mode=0o755)
        if args.mode == "run":
            keys = {}
            routes = [{"name": "model", "host": args.host, "path": args.api_path}]
            # FD mappings are operator input, never environment credentials.
            for host, fd in args.key_fds.items():
                data = os.read(fd, 4097).strip()
                if not data or len(data) > 4096 or any(c < 33 or c > 126 for c in data):
                    raise ValueError("invalid key input")
                keys[host] = data
            for route in args.paid_routes:
                if (not isinstance(route.get("name"), str) or not route["name"] or route["name"] == "model"
                        or route["name"].lower() not in (seed / "brief.md").read_text().lower()):
                    raise ValueError("paid service must be named in brief")
                routes.append(route)
            key_values = list(keys.values())
            if args.ca_file:
                if args.ca_file.stat().st_size > 1024 * 1024 or b"PRIVATE KEY" in args.ca_file.read_bytes():
                    raise ValueError("CA file must contain public certificates only")
                result["ca_sha256"] = sha256(args.ca_file)
            relay = Relay(egress / "api.sock", routes, keys, args.model, args.turns, args.ca_file)
            thread = threading.Thread(target=relay.serve_forever, daemon=True)
            thread.start()
        # Sentinel is outside all mounts; probe must be unable to read it.
        (root / "credential-sentinel").write_text("synthetic isolation sentinel")
        launched = time.monotonic()
        process = subprocess.Popen(list(runtime) + sandbox_args(args.image, name, seed, skill, egress,
                                    args.limits, input_bytes), env=runtime.env, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        frames = Frames(process, launched + args.wall)
        process.stdin.write(encode({"type": "start", "mode": args.mode, "model": args.model,
                                   "host": args.host, "path": args.api_path, "turns": args.turns,
                                   "limits": args.limits}))
        process.stdin.flush()
        frame = frames.next()
        if frame["type"] != "ready":
            raise RuntimeError("image preflight failed")
        result["tools"] = frame["versions"]
        result["mounts"] = mount_receipt(runtime, name, [seed / "inputs", seed / "brief.md", skill, egress])
        transcript, events, usage = [], [], {}
        drained = False
        while True:
            frame = frames.next()
            if frame["type"] == "event":
                event = frame["event"]
                events.append(event)
                if event["type"] in {"assistant", "tool"}:
                    text = str(event.get("text", ""))
                    if event.get("calls"):
                        text += "\nTool calls:\n" + json.dumps(event["calls"], ensure_ascii=True)
                    # Quoting prevents tool output from forging structural headings.
                    body = "\n".join("> " + line for line in text.splitlines())
                    transcript.append("## " + event["type"] + "\n\n" + body + "\n")
                elif event["type"] == "probe":
                    result["probes"] = event["rules"]
                    transcript.append("## tool\n\nSynthetic isolation probe completed.\n")
                if event["type"] == "finished":
                    usage = event["usage"]
                if len(encode({"events": events})) > MAX_FRAME - 65536:
                    raise ValueError("event capture size limit")
            elif frame["type"] == "drained":
                drained = frame["processes"] == 0
            elif frame["type"] == "agent-exit":
                break
            else:
                raise RuntimeError("unexpected agent protocol frame")
        if not drained:
            raise RuntimeError("agent drain not proved")
        result["agent_exit"] = frame["code"]
        result["limits_hit"] = frame["limits_hit"]
        result["agent_wall_seconds"] = time.monotonic() - launched
        if relay:
            relay.shutdown()
            relay.server_close()
            thread.join(timeout=5)
            cutoff = min(frames.deadline, time.monotonic() + 65)
            while relay.active_requests:
                if time.monotonic() > cutoff:
                    raise TimeoutError("proxy drain time limit")
                time.sleep(0.05)
        log = list(relay.log) if relay else []
        log += frame["audit"]
        result["usage"] = usage
        capture(process, {"transcript.md": "\n".join(transcript),
                          "proxy.log": "".join(json.dumps(v, sort_keys=True) + "\n" for v in log),
                          "usage.json": json.dumps(usage),
                          "run.json": json.dumps({**result, "events": events}, sort_keys=True)})
        if frames.next()["type"] != "archive-start":
            raise RuntimeError("missing capture archive")
        before = archive(frames, root / "before", args.limits["scratch"])
        reason = leak_reason(before)
        if relay and relay.incident:
            reason = "proxy blocked a key-bearing response"
        for key in key_values:
            reason = reason or leak_reason(before, key)
        if reason:
            result["reason"] = "API key incident in .run; tree excluded; operator must rotate key"
            result["incident"] = True
            raise RuntimeError("key incident")
        if frames.next() != {"type": "answers-ready", "processes": 0}:
            raise RuntimeError("answer phase not proved")
        if result["limits_hit"] or result["agent_exit"] != 0 or (args.mode == "run" and not usage):
            failed = next((e.get("reason") for e in events if e.get("type") == "failed"), None)
            result["reason"] = ("limit hit: " + ", ".join(result["limits_hit"]) if result["limits_hit"] else
                                failed if failed in {"turn limit", "tool wall time limit", "tool output limit"} else
                                "agent failed or omitted usage")
            shutil.copytree(before, args.output / "scratch")
            raise RuntimeError("agent failure")
        if args.mode == "probe" and (not all(result.get("probes", {}).values()) or not result.get("probes")
                                      or not any(v["status"] == "DENIED" for v in log)):
            raise RuntimeError("denying-direction probes not proved")
        answers = {"type": "check"}
        for file in ["check.py", "expected.json"]:
            source = private_answers / file
            answers[file] = base64.b64encode(source.read_bytes()).decode()
            result[file + "_sha256"] = sha256(source)
        # First transmission of either answer occurs after a clean snapshot scan.
        process.stdin.write(encode(answers))
        process.stdin.flush()
        frame = frames.next()
        if frame["type"] == "drained":
            frame = frames.next()
        if frame["type"] != "checker":
            raise RuntimeError("checker failed")
        if frame["limits_hit"]:
            result["limits_hit"] = frame["limits_hit"]
            result["reason"] = "limit hit: " + ", ".join(frame["limits_hit"])
            raise RuntimeError("checker resource limit")
        if frame["code"] != 0:
            raise RuntimeError("checker failed")
        result["checker"] = checker_result(json.loads(frame["output"]), args.case_id)
        if frames.next()["type"] != "archive-start":
            raise RuntimeError("missing final archive")
        after = archive(frames, root / "after", args.limits["scratch"])
        reason = leak_reason(after)
        for key in key_values:
            reason = reason or leak_reason(after, key)
        if reason:
            result["reason"] = "API key incident in .run; tree excluded; operator must rotate key"
            result["incident"] = True
            raise RuntimeError("key incident")
        if frames.next()["type"] != "done" or process.wait(timeout=5) != 0:
            raise RuntimeError("supervisor did not finish")
        shutil.copytree(after, args.output / "scratch")
        result["status"] = "passed" if all(r["pass"] for r in result["checker"]["rules"]) else "failed"
        result["reason"] = None if result["status"] == "passed" else "checker rules failed"
    except TimeoutError:
        result["reason"] = "wall time limit"
    except Exception:
        # Keep the generic/specific safe reason. Never serialize exceptions or keys.
        if runtime and process:
            try:
                state = json.loads(command(runtime, ["inspect", name]))[0]["State"]
                if state.get("OOMKilled"):
                    result["reason"] = "memory limit"
            except Exception:
                pass
    finally:
        if process and process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        if runtime and process:
            try:
                command(runtime, ["rm", "--force", name], timeout=10)
            except Exception:
                result["cleanup_unverified"] = True
                result["status"] = "failed"
        if relay:
            relay.shutdown()
            relay.server_close()
        if thread:
            thread.join(timeout=5)
        shutil.rmtree(root, ignore_errors=True)
        result["wall_seconds"] = time.monotonic() - started
        if result.get("incident"):
            shutil.rmtree(args.output / "scratch", ignore_errors=True)
            # Avoid returning token usage or checker measurements from a tainted run.
            result.pop("checker", None)
            result.pop("usage", None)
        (args.output / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "reason": result["reason"], "result": str(args.output / "result.json")}))
    return 0 if result["status"] == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["run", "probe"])
    parser.add_argument("--image", required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--skill", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="synthetic-probe")
    parser.add_argument("--host", default="api.example.test")
    parser.add_argument("--api-path", default="/v1/chat/completions")
    parser.add_argument("--key-fds", default="{}", help='JSON mapping exact host to inherited key FD; no key values')
    parser.add_argument("--paid-routes", default="[]", help='JSON routes: name, host, path; explicit keys per host')
    parser.add_argument("--ca-file", type=Path, help="Explicit public CA bundle for a test HTTPS host")
    parser.add_argument("--selftest", type=Path)
    parser.add_argument("--turns", type=int, default=60)
    parser.add_argument("--wall", type=int, default=1200)
    parser.add_argument("--cpus", type=int, default=4)
    parser.add_argument("--memory", type=int, default=8 * 1024**3)
    parser.add_argument("--scratch", type=int, default=2 * 1024**3)
    parser.add_argument("--processes", type=int, default=256)
    args = parser.parse_args()
    args.limits = {k: getattr(args, k) for k in ["cpus", "memory", "scratch", "processes"]}
    if any(v <= 0 for v in [*args.limits.values(), args.turns, args.wall]):
        parser.error("limits must be positive")
    args.key_fds, args.paid_routes = json.loads(args.key_fds), json.loads(args.paid_routes)
    if not isinstance(args.key_fds, dict) or any(type(fd) is not int or fd < 3 for fd in args.key_fds.values()):
        parser.error("key-fds must map hosts to FDs >= 3")
    if args.mode == "run" and (not args.selftest or not args.key_fds or args.model == "synthetic-probe"):
        parser.error("run requires a pinned model, explicit key FD and selftest receipt")
    if args.mode == "run" and args.model.lower() in {"latest", "auto", "default"}:
        parser.error("mutable model aliases are not pins")
    for name in ["store", "case", "skill", "output"]:
        setattr(args, name, getattr(args, name).absolute())
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
