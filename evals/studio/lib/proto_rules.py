"""Prototype rules for the studio case checkers: the build starts and reaches its first interactive frame, the core loop plays, nothing phones home, versions are pinned,
code is not copied from a project whose reuse class is not `copy`, and copied `copy`-class code is credited. Runs `node` in a scratch copy with an empty HOME, a refused network
and a time limit."""
import json, os, pathlib, re, shutil, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
NODE = os.environ.get("STUDIO_NODE") or shutil.which("node") or "node"


def run_node(scratch, args, stdin="", timeout=30):
    """Runs node in a copy of the project (so a build that writes dist/ leaves the scratch tree alone). Returns (returncode, stdout, stderr, network_attempts, seconds)."""
    import time
    with tempfile.TemporaryDirectory() as d:
        t = pathlib.Path(d) / "tree"
        shutil.copytree(scratch, t, ignore=shutil.ignore_patterns(".run", "node_modules"))
        logf = pathlib.Path(d) / "net.log"
        env = {"PATH": os.environ.get("PATH", ""), "HOME": d, "STUDIO_NET_LOG": str(logf), "NODE_OPTIONS": f"--require {HERE / 'net_trap.js'}", "NO_COLOR": "1"}
        t0 = time.time()
        try:
            r = subprocess.run([NODE, *args], cwd=t, env=env, input=stdin, capture_output=True, text=True, timeout=timeout)
            rc, out, err = r.returncode, r.stdout, r.stderr
        except subprocess.TimeoutExpired as e:
            rc, out, err = -9, (e.stdout or b"").decode() if isinstance(e.stdout, bytes) else (e.stdout or ""), "timed out"
        secs = time.time() - t0
        net = [json.loads(l) for l in logf.read_text().splitlines()] if logf.exists() else []
    return rc, out, err, net, secs


def r_proto_starts(R, scratch, rule):
    """The brief's start command (`args`) prints FIRST_INTERACTIVE_FRAME and exits 0 within `limit` seconds."""
    rc, out, err, net, secs = run_node(scratch, rule["args"], timeout=rule.get("limit", 30))
    ok = rc == 0 and "FIRST_INTERACTIVE_FRAME" in out.splitlines() and secs <= rule.get("limit", 30)
    R.add(rule["id"], ok, {"exit": rc, "first_frame": "FIRST_INTERACTIVE_FRAME" in out, "seconds": round(secs, 1), "stderr": err.strip()[-120:]}, "FIRST_INTERACTIVE_FRAME within %s s" % rule.get("limit", 30))


def catch_script(n_coins=12, lanes=5):
    """Input that catches every coin of the pattern in the brief: coin i appears at frame 30*i in lane i % 5, lands at frame 30*i + 60; the player starts in lane 2."""
    lines, lane = [], 2
    for i in range(n_coins):
        t = 30 * i + 55
        target = i % lanes
        while lane != target:
            lines.append(f"{t} {'left' if target < lane else 'right'}")
            lane += -1 if target < lane else 1
    return "\n".join(lines) + "\n"


def lines_of(out):
    return [l.strip() for l in out.splitlines() if l.strip()]


def r_proto_loop_lose(R, scratch, rule):
    """With no input the player misses coins: LIVES lines count down from 2 and GAME_OVER is printed."""
    rc, out, err, net, secs = run_node(scratch, rule["args"] + ["--frames", "700"], timeout=rule.get("limit", 30))
    L = lines_of(out)
    lives = [int(m.group(1)) for l in L for m in [re.fullmatch(r"LIVES (\d+)", l)] if m]
    over = "GAME_OVER" in L
    R.add(rule["id"], over and lives[:3] == [2, 1, 0], {"lives_lines": lives[:5], "game_over": over, "exit": rc}, "LIVES 2, 1, 0, then GAME_OVER")


def r_proto_loop_restart(R, scratch, rule):
    """After GAME_OVER, a `restart` input prints RESTART and play starts again (SCORE and LIVES lines continue)."""
    rc, out, err, net, secs = run_node(scratch, rule["args"] + ["--frames", "900"], stdin="560 restart\n", timeout=rule.get("limit", 30))
    L = lines_of(out)
    ok = "GAME_OVER" in L and "RESTART" in L and L.index("RESTART") > L.index("GAME_OVER") and any(re.fullmatch(r"LIVES \d+", l) for l in L[L.index("RESTART"):])
    R.add(rule["id"], ok, {"game_over": "GAME_OVER" in L, "restart": "RESTART" in L, "play_resumes": ok, "exit": rc}, "RESTART after GAME_OVER, then lives are lost again")


def r_proto_loop_score(R, scratch, rule):
    """Catching every coin prints SCORE 1, 2, ... in order, never GAME_OVER."""
    rc, out, err, net, secs = run_node(scratch, rule["args"] + ["--frames", "400"], stdin=catch_script(), timeout=rule.get("limit", 30))
    L = lines_of(out)
    scores = [int(m.group(1)) for l in L for m in [re.fullmatch(r"SCORE (\d+)", l)] if m]
    ok = scores[:12] == list(range(1, 13)) and "GAME_OVER" not in L
    R.add(rule["id"], ok, {"scores": scores[:14], "game_over": "GAME_OVER" in L, "exit": rc}, "SCORE 1..12 in order, no GAME_OVER")


def _urls(text):
    return set(re.findall(r"https?://([A-Za-z0-9.-]+)", text))


def r_proto_no_phone_home(R, scratch, rule):
    """Runs the start command and the build command under a refused network and records any attempt; also lists remote hosts written in the project's own files (outside `allowed_hosts`)."""
    attempts = []
    for args in (rule["args"], *rule.get("also", [])):
        rc, out, err, net, secs = run_node(scratch, args, timeout=60)
        attempts += [n["what"] for n in net]
    root = pathlib.Path(scratch)
    written = set()
    for f in root.rglob("*"):
        if f.is_file() and f.suffix in {".js", ".html", ".css", ".mjs"} and not any(p in {".run", "node_modules", "inputs", "dist"} for p in f.relative_to(root).parts):
            written |= _urls(f.read_text(errors="ignore"))
    written -= set(rule.get("allowed_hosts", []))
    written -= {"localhost", "127.0.0.1"}
    attempts = [a for a in attempts if not any(h in a for h in rule.get("allowed_hosts", []))]
    R.add(rule["id"], not attempts and not written, {"connection_attempts": sorted(set(attempts)) or None, "remote_hosts_in_files": sorted(written) or None}, "no connection attempt and no remote host in the project's files")


def _exact(v):
    return bool(re.fullmatch(r"\d+\.\d+\.\d+", str(v).strip().lstrip("v")))


def _fixed(v):
    """A Node version that names one major: `22`, `22.11`, `22.11.0`, `22.x`, or `>=22 <23` (a range that cannot take a different major; `^`, `~`, `*`, `latest` and open ranges do not count)."""
    v = str(v).strip().lstrip("v")
    if re.fullmatch(r"\d+(\.\d+){0,2}", v) or re.fullmatch(r"\d+\.x", v):
        return True
    m = re.fullmatch(r">=\s*v?(\d+)(\.\d+){0,2}\s*<\s*v?(\d+)(\.0){0,2}", v)
    return bool(m) and int(m.group(3)) == int(m.group(1)) + 1


def r_proto_pinned(R, scratch, rule):
    """The Node version is a fixed version (no range) in `.node-version` (or package.json `engines.node`), and the scaffold's name with an exact version appears in package.json or THIRD_PARTY.md."""
    root = pathlib.Path(scratch)
    node = None
    if (root / ".node-version").is_file():
        node = (root / ".node-version").read_text().strip()
    else:
        try:
            node = json.loads((root / "package.json").read_text()).get("engines", {}).get("node")
        except Exception:  # noqa: BLE001
            pass
    sc = ""
    for f in ("package.json", "THIRD_PARTY.md"):
        if (root / f).is_file():
            sc += (root / f).read_text()
    m = re.search(re.escape(rule["scaffold"]) + r"[^\n]{0,40}?(\d+\.\d+\.\d+)", sc) if rule.get("scaffold") else True
    deps_ok = True
    try:
        pk = json.loads((root / "package.json").read_text())
        for sect in ("dependencies", "devDependencies"):
            for k, v in (pk.get(sect) or {}).items():
                if not _exact(v):
                    deps_ok = False
    except Exception:  # noqa: BLE001
        deps_ok = False
    ok = bool(node) and _fixed(node) and bool(m) and deps_ok
    R.add(rule["id"], ok, {"node": node, "scaffold_version_recorded": (m.group(1) if hasattr(m, "group") else "not required") if m else None, "dependencies_exact": deps_ok}, "a fixed node version, an exact scaffold version, exact dependencies")


def _norm_lines(text):
    out = []
    for l in text.splitlines():
        l = re.sub(r"\s+", " ", l.strip())
        if len(l) >= 20 and not l.startswith("//"):
            out.append(l)
    return out


def shared_run(a_lines, b_lines):
    best = 0
    idx = {}
    for j, l in enumerate(b_lines):
        idx.setdefault(l, []).append(j)
    for i, l in enumerate(a_lines):
        for j in idx.get(l, []):
            k = 0
            while i + k < len(a_lines) and j + k < len(b_lines) and a_lines[i + k] == b_lines[j + k]:
                k += 1
            best = max(best, k)
    return best


def project_lines(scratch):
    root = pathlib.Path(scratch)
    out = []
    for f in sorted(root.rglob("*.js")):
        if any(p in {".run", "node_modules", "inputs", "dist"} for p in f.relative_to(root).parts):
            continue
        out += _norm_lines(f.read_text(errors="ignore"))
    return out


def r_proto_not_copied(R, scratch, rule):
    """No run of `run` consecutive substantive lines of the project's code is shared with the study-only project `reference`."""
    ref = []
    for f in sorted((pathlib.Path(scratch) / rule["reference"]).rglob("*.js")):
        ref += _norm_lines(f.read_text(errors="ignore"))
    n = shared_run(project_lines(scratch), ref)
    R.add(rule["id"], n < rule["run"], {"longest_shared_run": n}, "fewer than %d lines" % rule["run"])


def r_proto_credited(R, scratch, rule):
    """If the project's code shares at least `run` consecutive substantive lines with the `copy`-class scaffold, THIRD_PARTY.md names the scaffold, its version and its license, and the license text is kept (a LICENSE file naming the scaffold's copyright holder)."""
    ref = []
    for f in sorted((pathlib.Path(scratch) / rule["reference"]).rglob("*.js")):
        ref += _norm_lines(f.read_text(errors="ignore"))
    n = shared_run(project_lines(scratch), ref)
    root = pathlib.Path(scratch)
    tp = (root / "THIRD_PARTY.md").read_text() if (root / "THIRD_PARTY.md").is_file() else ""
    lic = "".join((root / n_).read_text() for n_ in ("LICENSE", "LICENSE.md", "LICENSE.txt", "licenses/mini-scaffold.txt") if (root / n_).is_file())
    row = rule["scaffold"].lower() in tp.lower() and rule["license"].lower() in tp.lower() and re.search(r"\d+\.\d+\.\d+", tp) is not None
    kept = rule["holder"].lower() in (lic + tp).lower()
    used = n >= rule["run"]
    R.add(rule["id"], (not used) or (row and kept), {"scaffold_code_used": used, "shared_run": n, "third_party_row": row, "notice_kept": kept}, "scaffold code used => THIRD_PARTY row with version and license, and the notice kept")


def r_proto_assets_have_rows(R, scratch, rule):
    """If anything other than the manifest is in `assets/`, the manifest exists and the validator accepts the project (every asset has a row, no master in the import path); a project with no assets needs no manifest."""
    import studio_lib
    root = pathlib.Path(scratch)
    files = [f for f in (root / "assets").rglob("*") if f.is_file() and f.name != "MANIFEST.json"] if (root / "assets").is_dir() else []
    if not files:
        return R.add(rule["id"], True, "no assets in the build", "a manifest row for every asset")
    studio_lib.TYPES["manifest_valid"](R, scratch, {"id": rule["id"], "import_paths": ["assets"]})


RULES = {k[2:]: v for k, v in globals().items() if k.startswith("r_")}
