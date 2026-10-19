#!/usr/bin/env python3
"""Fail-closed Podman studio runner. Requires an already-loaded pinned image."""
import argparse
import base64
import hashlib
import http.client
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
import traceback
import uuid

from common import KEY_PATTERN, VERSION, MAX_FRAME, checker_result, encode, leak_reason, plain_tree, sha256, read_key_fds
from proxy import Relay
from agent import system_text
from cache_api import FIELDS, usage as checked_usage, receipt as usage_receipt

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
            "--mount=type=bind,src=" + str(seed / "studio-resources") + ",dst=/scratch/skills/studio,ro=true",
            "--mount=type=bind,src=" + str(skill) + ",dst=/skill,ro=true",
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


def exception_receipt(error, keys, limit=2048):
    try:
        # Redact before truncating: a prefix of an exact key must not escape.
        message = str(error).encode('utf-8', 'replace')
        for key in keys:
            if key:
                message = message.replace(key, b'[REDACTED]')
        message = KEY_PATTERN.sub(b'[REDACTED]', message)
        return {'type': type(error).__name__, 'message': (message if limit is None else message[:limit]).decode('utf-8', 'replace'),
                'frames': [{'file': Path(f.filename).name, 'line': f.lineno,
                            'function': f.name} for f in traceback.extract_tb(error.__traceback__)[-12:]]}
    except Exception:
        return {'type': type(error).__name__, 'message': 'unavailable'}


def failed_capture(root, output, result, events, transcript, log, keys, snapshot=None):
    """Retain scanned received evidence even when the container protocol fails.

    A host-only receipt is not a proof of drain, a complete scratch snapshot,
    or permission to send checker answers. Those gates remain unchanged.
    """
    candidate = root / 'failure-capture'
    if snapshot is not None:
        shutil.copytree(snapshot, candidate)
    else:
        candidate.mkdir()
    capture_root = candidate / '.run'
    capture_root.mkdir(exist_ok=True)
    result['capture_scope'] = 'drained-scratch-snapshot' if snapshot is not None else 'host-received-events-only'
    result['key_scan'] = 'pending'
    files = {'transcript.md': '\n'.join(transcript),
             'proxy.log': ''.join(json.dumps(row, sort_keys=True) + '\n' for row in log),
             'usage.json': json.dumps(result.get('usage', {})),
             'run.json': json.dumps({**result, 'events': events}, sort_keys=True)}
    for name, content in files.items():
        (capture_root / name).write_text(content)
    reason = leak_reason(candidate)
    for key in keys:
        reason = reason or leak_reason(candidate, key)
    if reason or result.get('incident'):
        result['key_scan'] = 'incident'
        result['incident'] = True
        result['reason'] = 'API key incident in .run; tree excluded; operator must rotate key'
        return
    result['key_scan'] = 'passed'
    # Persist the final scan disposition; replacing pending with passed adds no input data.
    (capture_root / 'run.json').write_text(json.dumps({**result, 'events': events}, sort_keys=True))
    if (output / 'scratch').exists():
        shutil.rmtree(output / 'scratch')
    shutil.copytree(candidate, output / 'scratch')


from reviewer import validate_plan, review, png_dimensions, MAX_DIMENSION, VIEW_SCALE, ReviewError


def event_usage(value, prompt_cache):
    """Keep compatibility validation unchanged; native categories are strict."""
    if prompt_cache:
        return checked_usage(value)
    fields = FIELDS[:3]
    if not isinstance(value, dict) or any(type(value.get(k)) is not int or value[k] < 0 for k in fields):
        raise ValueError("invalid assistant token usage")
    return {k: value[k] for k in fields}


def result_usage(value, model, prompt_cache):
    return usage_receipt(value, model) if prompt_cache else dict(value)


def run(args):
    result = {"runner": VERSION, "status": "failed", "reason": "runner preflight or isolation failure",
              "runner_sha256": sha256(__file__),
              "case": args.case_id, "agent": VERSION, "model": args.model, "limits": args.limits,
              "usage": {}}
    if args.prompt_cache:
        result["prompt_cache"] = {"enabled": True,
            "policy": "operator-system-and-brief-only", "sampling": "provider-default",
            "thinking": "provider-default-lossless-roundtrip"}
    usage_result = lambda value: result_usage(value, args.model, args.prompt_cache)
    # No overwritten results and no mixed case runs.
    args.output.mkdir(parents=True, exist_ok=False)
    os.chmod(args.output, 0o700)
    started = time.monotonic()
    process = None
    relay = None
    thread = None
    transfer = None
    transfer_errors = []
    runtime = None
    name = "studio-" + uuid.uuid4().hex
    key_values = []
    events, transcript, log, usage = [], [], [], {}
    scanned_snapshot = None
    root = Path(tempfile.mkdtemp(prefix="studio-private-"))
    try:
        review_plan = []
        if args.review_plan:
            if args.mode != 'run' or args.review_plan.stat().st_size > 65536:
                raise ValueError('review plan requires live-run mode and a small trusted plan')
            review_plan = validate_plan(json.loads(args.review_plan.read_text()))
        reserve = 2 * len(review_plan) * args.review_rounds
        if reserve >= args.turns:
            raise ValueError('turn budget cannot reserve requested reviewer rounds')
        review_round = 0
        review_records = []
        review_ok = not review_plan
        result['review_gate'] = False  # Uncalibrated model review is a separate observation.
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
        if args.mode in {"run", "replay"}:
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
        if (args.case / "inputs").exists() or (args.case / "inputs").is_symlink():
            input_bytes = plain_tree(args.case / "inputs", seed / "inputs")
        else:
            # Cases with no reference files still get the same empty read-only
            # inputs mount, with no visible change to the neutral case layout.
            (seed / "inputs").mkdir(mode=0o755)
            input_bytes = 0
        input_bytes += brief.stat().st_size
        resources = seed / "studio-resources"
        resources.mkdir()
        result["studio_resources"] = {}
        for filename in ["manifest.schema.json", "validate_manifest.py"]:
            source = Path(__file__).resolve().parent.parent / filename
            if source.is_symlink() or not source.is_file() or source.stat().st_size > 512 * 1024:
                raise ValueError("unsafe or missing shared studio resource")
            target = resources / filename
            target.write_bytes(source.read_bytes())
            target.chmod(0o644)
            input_bytes += target.stat().st_size
            result["studio_resources"][filename] = sha256(target)
        private_answers = root / "private-answers"
        private_answers.mkdir(mode=0o700)
        for file in ["check.py", "expected.json"]:
            source = args.case / file
            if source.is_symlink() or not source.is_file() or source.stat().st_size > 512 * 1024:
                raise ValueError("unsafe or oversized checker answers")
            (private_answers / file).write_bytes(source.read_bytes())
            result[file + "_sha256"] = sha256(private_answers / file)
        library = private_answers / "lib"
        if args.checker_lib:
            if plain_tree(args.checker_lib, library) > 16 * 1024 * 1024:
                raise ValueError("checker library exceeds 16 MiB")
        else:
            library.mkdir()
        result["checker_lib_files"] = {str(p.relative_to(library)): sha256(p)
                                       for p in sorted(library.rglob("*")) if p.is_file()}
        skill = root / "skill"
        entry = args.skill / "SKILL.md" if args.skill.is_dir() else args.skill
        if args.skill.is_symlink() or entry.is_symlink() or not entry.is_file() or entry.stat().st_size > 256 * 1024:
            raise ValueError("unsafe or oversized skill")
        if args.skill.is_dir():
            plain_tree(args.skill, skill)
        else:
            # Legacy single-file callers receive only that file, never its siblings.
            skill.mkdir()
            (skill / "SKILL.md").write_bytes(entry.read_bytes())
            (skill / "SKILL.md").chmod(0o644)
        result["skill_sha256"] = sha256(skill / "SKILL.md")
        result["skill_files"] = {str(p.relative_to(skill)): sha256(p)
                                for p in sorted(skill.rglob("*")) if p.is_file()}
        result["brief_sha256"] = sha256(seed / "brief.md")
        replay_tree = None
        if args.mode == "replay":
            if args.replay.is_symlink() or args.replay.stat().st_size > MAX_FRAME:
                raise ValueError("unsafe replay metadata")
            metadata = json.loads(args.replay.read_text())
            if metadata["case"] != args.case_id or args.tree < 0:
                raise ValueError("replay case mismatch")
            replay_tree = metadata["trees"][args.tree]
            tar_name = replay_tree["tar"]
            if not isinstance(tar_name, str) or Path(tar_name).name != tar_name:
                raise ValueError("unsafe replay archive name")
            source = args.replay.parent / tar_name
            if source.is_symlink() or not source.is_file() or source.stat().st_size > args.scratch + 64 * 1024 * 1024:
                raise ValueError("unsafe or oversized replay archive")
            frozen_tar = root / "replay.tar"
            total = 0
            with source.open("rb") as input_stream, frozen_tar.open("xb") as output_stream:
                while block := input_stream.read(65536):
                    total += len(block)
                    if total > args.scratch + 64 * 1024 * 1024:
                        raise ValueError("replay archive exceeds staging limit")
                    output_stream.write(block)
            expected = replay_tree["expect"]
            if not isinstance(expected, dict) or not expected or any(not isinstance(k, str) or type(v) is not bool for k, v in expected.items()):
                raise ValueError("invalid replay expected verdict")
            with frozen_tar.open("rb") as stream:
                tar_sha256 = hashlib.file_digest(stream, "sha256").hexdigest()
            result["replay"] = {"tree": args.tree, "tar_sha256": tar_sha256,
                                "metadata_sha256": sha256(args.replay), "expected": expected,
                                "model_called": False}
        egress = root / "egress"
        egress.mkdir(mode=0o755)
        if args.mode == "run":
            routes = [{"name": "model", "host": args.host, "path": args.api_path}]
            keys = read_key_fds(args.key_fds)
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
            prefix = {'system': system_text((skill/'SKILL.md').read_text()), 'brief': (seed/'brief.md').read_text()} if args.prompt_cache else None
            relay = Relay(egress / "api.sock", routes, keys, args.model, args.turns, args.ca_file, cache_prefix=prefix)
            thread = threading.Thread(target=relay.serve_forever, daemon=True)
            thread.start()
        launched = time.monotonic()
        process = subprocess.Popen(list(runtime) + sandbox_args(args.image, name, seed, skill, egress,
                                    args.limits, input_bytes), env=runtime.env, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        frames = Frames(process, launched + args.wall)
        process.stdin.write(encode({"type": "start", "mode": args.mode, "model": args.model,
                                   "host": args.host, "path": args.api_path, "turns": args.turns - reserve,
                                   "review_files": [item["file"] for item in review_plan],
                                   "limits": args.limits,
                                   "replay_limit": args.scratch - CAPTURE_RESERVE - input_bytes}))
        process.stdin.flush()
        frame = frames.next()
        if frame["type"] != "ready":
            raise RuntimeError("image preflight failed")
        result["tools"] = frame["versions"]
        result["mounts"] = mount_receipt(runtime, name, [seed / "inputs", seed / "brief.md", resources, skill, egress])
        if replay_tree is not None:
            def transfer_replay():
                try:
                    with frozen_tar.open("rb") as stream:
                        while block := stream.read(65536):
                            process.stdin.write(encode({"type": "replay-chunk", "data": base64.b64encode(block).decode()}))
                    process.stdin.write(encode({"type": "replay-end"}))
                    process.stdin.flush()
                except Exception:
                    transfer_errors.append(True)
            # Frame reception keeps enforcing the wall deadline if extraction
            # stalls while the writer is blocked on the container's pipe.
            transfer = threading.Thread(target=transfer_replay, daemon=True)
            transfer.start()
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
                if event["type"] == "assistant":
                    reported = event.get("usage")
                    fields = FIELDS if args.prompt_cache else FIELDS[:3]
                    reported = event_usage(reported, args.prompt_cache)
                    usage = {k: usage.get(k, 0) + reported[k] for k in fields}
                    # Retain paid usage even if a later event, tool or drain fails.
                    result["usage"] = usage_result(usage)
                if len(encode({"events": events})) > MAX_FRAME - 65536:
                    raise ValueError("event capture size limit")
            elif frame["type"] == 'review-snapshots':
                review_round += 1
                snapshots = frame.get('snapshots')
                accepted = False
                stop = False
                feedback = []
                try:
                    if (not review_plan or review_round > args.review_rounds or
                            not isinstance(snapshots, list) or
                            [s.get('file') for s in snapshots] != [item['file'] for item in review_plan]):
                        raise ReviewError('invalid review phase or asset set')
                    for item, snapshot in zip(review_plan, snapshots):
                        if snapshot.get('error'):
                            raise ReviewError(snapshot['error'])
                        if not re.fullmatch(r'[a-f0-9]{64}', snapshot.get('sha256', '')):
                            raise ReviewError('invalid supervisor snapshot hash')
                        if not isinstance(snapshot.get('views'), list) or len(snapshot['views']) != 2:
                            raise ReviewError('invalid supervisor neutral views')
                        views = [base64.b64decode(v, validate=True) for v in snapshot['views']]
                        source_dimensions = snapshot.get('source_dimensions')
                        scale = snapshot.get('scale')
                        dimensions = snapshot.get('dimensions')
                        if (not isinstance(source_dimensions, list) or len(source_dimensions) != 2 or
                                any(type(d) is not int or not 1 <= d <= MAX_DIMENSION for d in source_dimensions) or
                                type(scale) is not int or not isinstance(dimensions, list) or
                                len(dimensions) != 2 or any(type(d) is not int for d in dimensions) or
                                scale != max(1, min(VIEW_SCALE, MAX_DIMENSION // max(source_dimensions))) or
                                dimensions != [d * scale for d in source_dimensions] or
                                any(list(png_dimensions(v)) != dimensions for v in views)):
                            raise ReviewError('invalid supervisor view scale or dimensions')
                        def record(phase, text, reported):
                            nonlocal usage
                            for key, value in reported.items():
                                usage[key] = usage.get(key, 0) + value
                            result['usage'] = usage_result(usage)
                            review_records.append({'round': review_round, 'file': item['file'],
                                'sha256': snapshot['sha256'], 'scale': scale, 'dimensions': dimensions,
                                'source_dimensions': source_dimensions, 'phase': phase, 'text': text,
                                'usage': reported})
                            result['review_records'] = list(review_records)
                        def transport(messages, max_tokens):
                            remaining = frames.deadline - time.monotonic()
                            if remaining <= 0:
                                raise TimeoutError('shared review wall time limit')
                            return relay.review_request(messages, max_tokens, min(60, remaining))
                        verdict = review(views, item, args.model, transport, record)
                        feedback.append({'file': item['file'], **verdict})
                    accepted = all(item['accepted'] for item in feedback)
                    stop = not accepted and review_round >= args.review_rounds
                except (ReviewError, ValueError, OSError, TimeoutError, http.client.HTTPException) as error:
                    stop = True
                    result['review_error'] = exception_receipt(error, key_values)
                    feedback = [{'error': 'fresh-context model review failed; no acceptance'}]
                review_ok = accepted
                process.stdin.write(encode({'type': 'review-feedback', 'accepted': accepted,
                    'stop': stop, 'feedback': json.dumps(feedback)}))
                process.stdin.flush()
            elif frame["type"] == "drained":
                drained = frame["processes"] == 0
            elif frame["type"] == "agent-exit":
                break
            else:
                raise RuntimeError("unexpected agent protocol frame")
        if not drained:
            raise RuntimeError("agent drain not proved")
        if transfer:
            transfer.join(timeout=5)
            if transfer.is_alive() or transfer_errors:
                raise RuntimeError("replay transfer failed")
        result['review_accepted'] = review_ok and frame.get('review_integrity', not review_plan)
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
        if replay_tree is not None:
            transcript = []
            for role, content in replay_tree["transcript"]:
                if role not in {"assistant", "tool"} or not isinstance(content, str):
                    raise ValueError("invalid replay transcript")
                transcript.append("## " + role + "\n\n" + "\n".join("> " + line for line in content.splitlines()) + "\n")
            for row in replay_tree["proxy"]:
                if (not isinstance(row["host"], str) or not re.fullmatch(r"[a-zA-Z0-9.-]{1,253}", row["host"])
                        or type(row["status"]) is not int or not 100 <= row["status"] <= 599):
                    raise ValueError("invalid replay proxy observation")
                log.append({"host": row["host"], "method": "POST", "status": row["status"], "bytes": 0, "time": time.time()})
        if relay:
            result["paid_routes"] = [{"host": host, "path": path, **budget}
                                     for (host, path), budget in sorted(relay.budgets.items())]
            if relay.limit_hit:
                result["limits_hit"].append("paid route calls or bytes")
        result["usage"] = usage_result(usage)
        capture(process, {"transcript.md": "\n".join(transcript),
                          "proxy.log": "".join(json.dumps(v, sort_keys=True) + "\n" for v in log),
                          "usage.json": json.dumps(usage_result(usage)),
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
        scanned_snapshot = before
        result["key_scan"] = "passed"
        if frames.next() != {"type": "answers-ready", "processes": 0}:
            raise RuntimeError("answer phase not proved")
        if (result["limits_hit"] or result["agent_exit"] != 0 or
                (args.mode == "run" and not usage)):
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
        for source in sorted(library.rglob("*")):
            if source.is_file():
                relative = str(source.relative_to(library))
                process.stdin.write(encode({"type": "library-file", "name": relative,
                                           "executable": bool(source.stat().st_mode & 0o111)}))
                with source.open("rb") as stream:
                    while block := stream.read(65536):
                        process.stdin.write(encode({"type": "library-chunk", "data": base64.b64encode(block).decode()}))
                process.stdin.write(encode({"type": "library-file-end"}))
        process.stdin.write(encode({"type": "library-end"}))
        process.stdin.flush()
        frame = frames.next()
        if frame["type"] == "drained":
            frame = frames.next()
        if frame["type"] != "checker":
            raise RuntimeError("checker failed")
        result["checker_exit"] = frame["code"]
        stderr = frame.get("stderr", "")
        if not isinstance(stderr, str):
            raise ValueError("invalid checker stderr")
        redacted = exception_receipt(ValueError(stderr), key_values, limit=None)["message"].encode('utf-8')
        result["checker_stderr"] = redacted[:2048].decode('utf-8', 'ignore')
        result["checker_stderr_truncated"] = len(redacted) > 2048
        if frame["limits_hit"]:
            result["limits_hit"] = frame["limits_hit"]
            result["reason"] = "limit hit: " + ", ".join(frame["limits_hit"])
            raise RuntimeError("checker resource limit")
        if type(frame["code"]) is not int or frame["code"] not in (0, 1):
            raise RuntimeError("checker error")
        result["checker"] = checker_result(json.loads(frame["output"]), args.case_id)
        if (frame['code'] == 0) != all(rule['pass'] for rule in result['checker']['rules']):
            raise RuntimeError('checker exit code disagrees with its rules')
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
        scanned_snapshot = after
        result["key_scan"] = "passed"
        if frames.next()["type"] != "done" or process.wait(timeout=5) != 0:
            raise RuntimeError("supervisor did not finish")
        shutil.copytree(after, args.output / "scratch")
        result["verdict"] = "passed" if all(r["pass"] for r in result["checker"]["rules"]) else "failed"
        result["status"] = "completed" if args.mode == "run" else result["verdict"]
        result["reason"] = None if result["verdict"] == "passed" else "checker rules failed"
        if replay_tree is not None:
            got = {r["id"]: r["pass"] for r in result["checker"]["rules"]}
            matched = got == result["replay"]["expected"]
            result["replay"]["matched"] = matched
            result["status"] = "passed" if matched else "failed"
            result["reason"] = None if matched else "replay verdict differs from host"
    except TimeoutError as error:
        result["exception"] = exception_receipt(error, key_values)
        result["reason"] = "wall time limit"
    except Exception as error:
        result["exception"] = exception_receipt(error, key_values)
        if result["reason"] == "runner preflight or isolation failure":
            result["reason"] = "runner exception: " + type(error).__name__
        # Keep specific reasons and redacted diagnostics; never serialize raw exceptions or keys.
        if runtime and process:
            try:
                state = json.loads(command(runtime, ["inspect", name]))[0]["State"]
                if state.get("OOMKilled"):
                    result["reason"] = "memory limit"
            except Exception:
                pass
    finally:
        if process and process.poll() is None:
            try:
                process.kill()
                process.wait(timeout=5)
            except Exception as error:
                result['process_cleanup_exception'] = exception_receipt(error, key_values)
                result['cleanup_unverified'] = True
                result['status'] = 'failed'
                result['reason'] = result['reason'] or 'process cleanup unverified'
        if transfer:
            transfer.join(timeout=5)
        if runtime and process:
            try:
                command(runtime, ["rm", "--force", name], timeout=10)
            except Exception as error:
                result["cleanup_exception"] = exception_receipt(error, key_values)
                result["cleanup_unverified"] = True
                result["status"] = "failed"
                result["reason"] = result["reason"] or "container cleanup unverified"
        if relay:
            try:
                relay.shutdown()
                relay.server_close()
            except Exception as error:
                result['relay_cleanup_exception'] = exception_receipt(error, key_values)
                result['status'] = 'failed'
                result['reason'] = result['reason'] or 'relay cleanup unverified'
        if thread:
            thread.join(timeout=5)
        if result['status'] not in ('passed', 'completed'):
            try:
                failed_capture(root, args.output, result, events, transcript,
                               log or (list(relay.log) if relay else []), key_values,
                               scanned_snapshot)
            except Exception as error:
                result['capture_exception'] = exception_receipt(error, key_values)
                result['key_scan'] = 'not_completed'
                # A missing scan never becomes a retained unverified tree.
                shutil.rmtree(args.output / 'scratch', ignore_errors=True)
        shutil.rmtree(root, ignore_errors=True)
        result["wall_seconds"] = time.monotonic() - started
        if result.get("incident"):
            shutil.rmtree(args.output / "scratch", ignore_errors=True)
            # Avoid returning token usage or checker measurements from a tainted run.
            result.pop("checker", None)
            result.pop("checker_stderr", None)
            result.pop("checker_exit", None)
            result.pop("checker_stderr_truncated", None)
            result.pop("verdict", None)
            result.pop("usage", None)
            result.pop("exception", None)
            result.pop("capture_exception", None)
            for field in ['cleanup_exception', 'process_cleanup_exception', 'relay_cleanup_exception',
                          'review_records', 'review_error', 'review_accepted']:
                result.pop(field, None)
        (args.output / "result.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "reason": result["reason"], "result": str(args.output / "result.json")}))
    return 0 if result["status"] in {"passed", "completed"} else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["run", "probe", "replay"])
    parser.add_argument("--replay", type=Path, help="Emitted replay.json; replay mode only, never calls a model")
    parser.add_argument("--tree", type=int, default=0, help="Zero-based tree index in replay.json")
    parser.add_argument("--image", required=True)
    parser.add_argument("--store", type=Path, required=True)
    parser.add_argument("--case", type=Path, required=True)
    parser.add_argument("--case-id", required=True)
    parser.add_argument("--skill", type=Path, required=True, help="Read-only skill directory containing SKILL.md (or legacy single file)")
    parser.add_argument("--checker-lib", type=Path, help="Trusted checker library bundle, transferred only after agent drain")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="synthetic-probe")
    parser.add_argument("--host", default="api.example.test")
    parser.add_argument("--prompt-cache", action="store_true", help="Native Messages caching of the fixed operator prefix only")
    parser.add_argument("--api-path", default="/v1/chat/completions")
    parser.add_argument("--key-fds", default="{}", help='JSON mapping exact host to inherited key FD; no key values')
    parser.add_argument("--paid-routes", default="[]", help='JSON routes: name, host, path, max_calls, max_bytes; bytes count requests plus responses')
    parser.add_argument("--ca-file", type=Path, help="Explicit public CA bundle for a test HTTPS host")
    parser.add_argument("--selftest", type=Path)
    parser.add_argument("--turns", type=int, default=60)
    parser.add_argument("--wall", type=int, default=1200)
    parser.add_argument("--cpus", type=int, default=4)
    parser.add_argument("--memory", type=int, default=8 * 1024**3)
    parser.add_argument("--scratch", type=int, default=2 * 1024**3)
    parser.add_argument("--processes", type=int, default=256)
    parser.add_argument('--review-plan', type=Path, help='Trusted operator plan: file, subject_words, feature questions; never checker answers')
    parser.add_argument('--review-rounds', type=int, default=2, help='Maximum blind review/redraw rounds, shared run budget')
    args = parser.parse_args()
    if args.prompt_cache:
        if args.mode != 'run' or args.host != 'api.anthropic.com' or args.api_path not in ('/v1/chat/completions','/v1/messages'):
            parser.error('prompt cache requires native Anthropic run mode')
        args.api_path = '/v1/messages'
    if not 1 <= args.review_rounds <= 4:
        parser.error('review-rounds must be 1-4')
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
    if args.mode == "replay" and (not args.replay or not args.selftest or args.key_fds or args.paid_routes):
        parser.error("replay requires metadata and selftest, and refuses credential FDs or paid routes")
    for name in ["store", "case", "skill", "output"]:
        setattr(args, name, getattr(args, name).absolute())
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
