#!/usr/bin/env python3
"""Run the independent fixtures for a skill's tools.

    python3 tools/evals/runner.py glean              # every fixture under tools/evals/glean/fixtures
    python3 tools/evals/runner.py harvest --only 04  # fixtures whose id starts with 04
    python3 tools/evals/runner.py glean --list       # id, failure-list item, tag, title
    python3 tools/evals/runner.py glean --tools DIR  # test the tools in another directory

Each fixture is a directory with one case.json: the input files, the tool and its arguments, and what the run
must do. The fixtures were written from the spec's failure list by someone other than the builder, before the
tools existed. They run the tool in a fresh temp directory with HOME empty, a PATH of symlinked system tools
only, and no network except the local stub servers a fixture starts for itself.

Exit 0 when every selected fixture passes, 1 when one fails, 3 when a tool is missing (so "no tool yet" is never
read as "all passed").
"""
import argparse, datetime, http.server, json, os, pathlib, re, shutil, socketserver, subprocess, sys, tempfile, threading, time

HERE = pathlib.Path(__file__).resolve().parent
NOW = datetime.datetime(2026, 10, 6, 12, 0, 0, tzinfo=datetime.timezone.utc)
COMMON_TOOLS = ["sh", "bash", "env", "cat", "python3", "git", "date", "true", "false", "sleep", "mkdir", "rm", "ls"]


PORTS = {}


def fmt(text):
    for name, port in PORTS.items():
        text = text.replace("{{PORT_%s}}" % name, str(port))
    return text.replace("{{NOW}}", NOW.strftime("%Y-%m-%dT%H:%M:%SZ")).replace("{{DATE}}", NOW.strftime("%Y-%m-%d"))


def deep_fmt(v):
    if isinstance(v, str):
        return fmt(v)
    if isinstance(v, list):
        return [deep_fmt(x) for x in v]
    if isinstance(v, dict):
        return {k: deep_fmt(x) for k, x in v.items()}
    return v


def make_toolbin(root):
    tb = root / "toolbin"
    tb.mkdir()
    for name in COMMON_TOOLS:
        p = shutil.which(name)
        if p:
            (tb / name).symlink_to(p)
    return tb


FAKE_GH = r'''#!/usr/bin/env python3
# fake gh for fixtures: logs every call, answers `auth status` and `api PATH` from a canned table
import json, os, sys
cfg = json.loads(os.environ["FAKE_GH_CONFIG"])
with open(os.environ["GH_LOG"], "a") as f:
    f.write(" ".join(sys.argv[1:]) + "\n")
a = sys.argv[1:]
if a[:2] == ["auth", "status"]:
    if cfg.get("auth", True):
        print("Logged in to github.com account fixture-bot")
        sys.exit(0)
    sys.stderr.write("You are not logged into any GitHub hosts. To log in, run: gh auth login\n")
    sys.exit(1)
if a and a[0] == "api":
    path = next((x for x in a[1:] if x.lstrip("/").startswith(("repos/", "projects/", "search/"))), "")
    path = path.split("?")[0].lstrip("/")
    if path in cfg.get("api", {}):
        print(json.dumps(cfg["api"][path]))
        sys.exit(0)
    sys.stderr.write("gh: Not Found (HTTP 404)\n")
    sys.exit(1)
sys.stderr.write("fake gh: unsupported call\n")
sys.exit(1)
'''


def snapshot(path):
    out = {}
    for p in sorted(pathlib.Path(path).rglob("*")):
        try:
            s = p.lstat()
        except OSError:
            continue
        out[str(p.relative_to(path))] = (s.st_size, s.st_mtime_ns, s.st_mode)
    return out


def build(work, case):
    for name, content in case.get("files", {}).items():
        p = work / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(deep_fmt(content) if isinstance(content, str) else json.dumps(deep_fmt(content)))
    for name, spec in case.get("files_gen", {}).items():
        p = work / name
        p.parent.mkdir(parents=True, exist_ok=True)
        line = spec["line"]
        with p.open("w") as f:
            total = 0
            n = 0
            while total < spec.get("min_bytes", 0) or n < spec.get("lines", 0):
                row = deep_fmt(line.replace("{n}", str(n)))
                f.write(row + "\n")
                total += len(row) + 1
                n += 1
    for name, hexdata in case.get("binary_files", {}).items():
        p = work / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(bytes.fromhex(hexdata))
    for d in case.get("mkdirs", []):
        (work / d).mkdir(parents=True, exist_ok=True)
    for name, mode in case.get("chmod", {}).items():
        os.chmod(work / name, int(mode, 8))


class Stub:
    """A local HTTP server for one fixture. Routes: path -> {status, headers, body, body_repeat, stream_forever, drip_seconds, delay, redirect}.
    Every request is logged with a monotonic time, so a fixture can assert what was and was not requested."""

    def __init__(self, routes):
        self.routes, self.log = routes, []
        stub = self

        class H(http.server.BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *a):
                pass

            def do_GET(self):
                path = self.path.split("?")[0]
                stub.log.append(dict(t=time.monotonic(), method="GET", path=path, full=self.path, headers={k.lower(): v for k, v in self.headers.items()}))
                r = stub.routes.get(path) or stub.routes.get("*") or {"status": 404, "body": "not found"}
                if r.get("delay"):
                    time.sleep(r["delay"])
                status = r.get("redirect_status", 302) if r.get("redirect") else r.get("status", 200)
                try:
                    self.send_response(status)
                    for k, v in (r.get("headers") or {}).items():
                        self.send_header(k, fmt(v))
                    if r.get("redirect"):
                        self.send_header("Location", fmt(r["redirect"]))
                    if r.get("stream_forever") or r.get("drip_seconds"):
                        self.send_header("Content-Type", r.get("content_type", "text/html; charset=utf-8"))
                        self.send_header("Connection", "close")
                        self.end_headers()
                        t0 = time.time()
                        while True:
                            self.wfile.write(b"x" if r.get("drip_seconds") else b"x" * 65536)
                            self.wfile.flush()
                            if r.get("drip_seconds"):
                                time.sleep(1)
                                if time.time() - t0 > r["drip_seconds"]:
                                    break
                        return
                    if "body_repeat" in r:
                        body = (r["body_repeat"].get("prefix", "") + r["body_repeat"]["char"] * r["body_repeat"]["count"] + r["body_repeat"].get("suffix", "")).encode()
                    else:
                        body = fmt(r.get("body", "")).encode("utf-8", "surrogateescape") if isinstance(r.get("body", ""), str) else bytes.fromhex(r["body"]["hex"])
                    if "Content-Type" not in (r.get("headers") or {}):
                        self.send_header("Content-Type", r.get("content_type", "text/html; charset=utf-8"))
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("Connection", "close")
                    self.end_headers()
                    if self.command != "HEAD":
                        self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            do_HEAD = do_GET

        class S(socketserver.ThreadingMixIn, http.server.HTTPServer):
            daemon_threads = True
            allow_reuse_address = True

        self.server = S(("127.0.0.1", 0), H)
        self.port = self.server.server_address[1]

    def start(self):
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()


def run_case(case, tools_dir):
    stubs = {}
    PORTS.clear()
    for name, routes in case.get("servers", {}).items():
        stubs[name] = Stub(routes)
        PORTS[name] = stubs[name].port
    try:
        for st in stubs.values():
            st.routes = deep_fmt(st.routes)
            st.start()
        res = _run_case(case, tools_dir)
        res["reqlogs"] = {n: list(st.log) for n, st in stubs.items()}
        return res
    finally:
        for st in stubs.values():
            st.stop()
        PORTS.clear()


def _run_case(case, tools_dir):
    root = pathlib.Path(tempfile.mkdtemp(prefix="evalrun-"))
    try:
        work = root / "work"
        work.mkdir()
        build(work, case)
        tb = make_toolbin(root)
        gh_log = root / "gh.log"
        gh_log.write_text("")
        if "fake_gh" in case:
            (tb / "gh").write_text(FAKE_GH)
            (tb / "gh").chmod(0o755)
        home = root / "home"
        home.mkdir()
        env = {"PATH": str(tb), "HOME": str(home), "TZ": "UTC", "LC_ALL": "C.UTF-8", "LANG": "C.UTF-8",
               "PYTHONDONTWRITEBYTECODE": "1"}
        env["GH_LOG"] = str(gh_log)
        if "fake_gh" in case:
            env["FAKE_GH_CONFIG"] = json.dumps(deep_fmt(case["fake_gh"]))
        env.update({k: fmt(v) for k, v in case.get("env", {}).items()})
        tool = tools_dir / case["tool"]
        if not tool.exists():
            return dict(missing=str(tool))
        args = [fmt(a) for a in case.get("args", [])]
        before = snapshot(work)
        runs = []
        for _ in range(2 if case["expect"].get("deterministic") else 1):
            t0 = time.time()
            try:
                r = subprocess.run([str(tool)] + args, cwd=work, env=env, capture_output=True, timeout=case.get("timeout", 30))
                runs.append((r.returncode, r.stdout, r.stderr, time.time() - t0))
            except subprocess.TimeoutExpired:
                runs.append((124, b"", b"TIMEOUT", time.time() - t0))
            except OSError as e:
                runs.append((127, b"", str(e).encode(), time.time() - t0))
        after = snapshot(work)
        calls = [l.strip() for l in gh_log.read_text().splitlines() if l.strip()]
        return dict(rc=runs[0][0], out=runs[0][1], err=runs[0][2], secs=runs[0][3], runs=runs, before=before, after=after, expect=case["expect"], gh_calls=calls)
    finally:
        for dp, dn, fn in os.walk(root):
            for n in dn + fn:
                try:
                    os.chmod(os.path.join(dp, n), 0o700 if n in dn else 0o600)
                except OSError:
                    pass
        shutil.rmtree(root, ignore_errors=True)


def dig(doc, path):
    cur = doc
    for part in path.split("."):
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return KeyError
        elif isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return KeyError
    return cur


def check(res):
    e = deep_fmt(res["expect"])
    problems = []
    out = res["out"].decode("utf-8", "replace")
    err = res["err"].decode("utf-8", "replace")
    if res["rc"] not in e.get("exit", [0]):
        problems.append(f"exit code {res['rc']}, expected one of {e.get('exit', [0])}")
    doc = None
    if not e.get("no_json"):
        try:
            doc = json.loads(out)
        except ValueError:
            problems.append("stdout is not exactly one JSON document")
    for j in e.get("json", []):
        if doc is None:
            break
        v = dig(doc, j["path"])
        if "equals" in j and v != j["equals"]:
            problems.append(f"json {j['path']} = {v!r}, expected {j['equals']!r}")
        if "in" in j and v not in j["in"]:
            problems.append(f"json {j['path']} = {v!r}, expected one of {j['in']!r}")
        if "regex" in j and (v is KeyError or not re.search(j["regex"], str(v))):
            problems.append(f"json {j['path']} = {v!r} does not match /{j['regex']}/")
        if j.get("absent") and v is not KeyError:
            problems.append(f"json {j['path']} should be absent, is {v!r}")
        if j.get("present") and v is KeyError:
            problems.append(f"json {j['path']} is missing")
        if "length" in j and (v is KeyError or len(v) != j["length"]):
            problems.append(f"json {j['path']} has length {None if v is KeyError else len(v)}, expected {j['length']}")
    if doc is not None:
        fl = doc.get("findings", []) if isinstance(doc.get("findings"), list) else []
        # findings are objects {card_id, code, message} (the checkers) or plain strings (the resolver and fetcher)
        alltext = " | ".join((f if isinstance(f, str) else f"{f.get('card_id')}:{f.get('code')}:{f.get('message')}") for f in fl)
        for rx in e.get("finding_includes", []):
            if not re.search(rx, alltext):
                problems.append(f"no finding matches /{rx}/ (findings: {alltext[:300]!r})")
        for rx in e.get("finding_excludes", []):
            if re.search(rx, alltext):
                problems.append(f"a finding matches forbidden /{rx}/ (findings: {alltext[:300]!r})")
    for rx in e.get("contains", []):
        if not re.search(rx, out, re.M):
            problems.append(f"stdout lacks /{rx}/")
    for rx in e.get("not_contains", []):
        m = re.search(rx, out, re.M)
        if m:
            problems.append(f"stdout must not contain /{rx}/: {m.group(0)[:80]!r}")
    for rx in e.get("stderr_contains", []):
        if not re.search(rx, err, re.M):
            problems.append(f"stderr lacks /{rx}/")
    for rx in e.get("stderr_not_contains", []):
        if re.search(rx, err, re.M):
            problems.append(f"stderr must not contain /{rx}/")
    if e.get("no_control_chars"):
        bad = re.findall(rb"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]|\x1b|\r", res["out"])
        if bad:
            problems.append(f"control characters in stdout: {sorted(set(b.hex() for b in bad))}")
        if re.search("[​-‏‪-‮⁦-⁩﻿]", out):
            problems.append("invisible or bidi format characters in stdout")
    for name, rq in e.get("requests", {}).items():
        log = res.get("reqlogs", {}).get(name, [])
        paths = [x["path"] for x in log]
        for pth in rq.get("paths_include", []):
            if pth not in paths:
                problems.append(f"server {name} never saw a request for {pth} (saw {paths})")
        for pth in rq.get("paths_exclude", []):
            if pth in paths:
                problems.append(f"server {name} was asked for {pth}, which must never be requested (saw {paths})")
        for pth, n in rq.get("path_counts", {}).items():
            if paths.count(pth) != n:
                problems.append(f"server {name} saw {paths.count(pth)} requests for {pth}, expected {n} (saw {paths})")
        if "count" in rq and len(log) != rq["count"]:
            problems.append(f"server {name} saw {len(log)} requests, expected {rq['count']} ({paths})")
        if "max_count" in rq and len(log) > rq["max_count"]:
            problems.append(f"server {name} saw {len(log)} requests, at most {rq['max_count']} expected ({paths})")
        if "first_path" in rq and (not log or log[0]["path"] != rq["first_path"]):
            problems.append(f"first request to {name} was {paths[:1]}, expected {rq['first_path']}")
        if "ua_regex" in rq:
            for x in log:
                if not re.search(rq["ua_regex"], x["headers"].get("user-agent", "")):
                    problems.append(f"request {x['path']} sent User-Agent {x['headers'].get('user-agent')!r}, expected /{rq['ua_regex']}/")
        for h in rq.get("no_headers", []):
            for x in log:
                if h.lower() in x["headers"]:
                    problems.append(f"request {x['path']} carried a {h} header")
        if "min_gap_s" in rq:
            for a_, b_ in zip(log, log[1:]):
                gap = b_["t"] - a_["t"]
                if gap < rq["min_gap_s"]:
                    problems.append(f"requests {a_['path']} and {b_['path']} started {gap:.2f}s apart, minimum {rq['min_gap_s']}s")
    if "gh_calls" in e:
        calls = res.get("gh_calls", [])
        g = e["gh_calls"]
        if "count" in g and len(calls) != g["count"]:
            problems.append(f"gh was called {len(calls)} times, expected {g['count']}: {calls}")
        for call in calls:
            if not re.match(r"^(auth status|api )", call) or re.search(r"(-X|--method)\s+(POST|PUT|PATCH|DELETE)|clone|download|install", call):
                problems.append(f"gh was called with something other than a read: {call!r}")
        for rx in g.get("include", []):
            if not any(re.search(rx, c) for c in calls):
                problems.append(f"no gh call matches /{rx}/ (calls: {calls})")
    if e.get("writes_nothing") and res["before"] != res["after"]:
        problems.append("the run changed files in its working directory")
    if e.get("deterministic") and len(res["runs"]) == 2 and res["runs"][0][1] != res["runs"][1][1]:
        problems.append("two runs printed different stdout")
    if e.get("max_seconds") and res["secs"] > e["max_seconds"]:
        problems.append(f"took {res['secs']:.1f}s, limit {e['max_seconds']}s")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("skill", choices=["glean", "harvest"])
    ap.add_argument("--only", default="")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--tags", default="")
    ap.add_argument("--tools", default=str(HERE.parent))
    a = ap.parse_args()
    fx = HERE / a.skill / "fixtures"
    cases = [json.loads(p.read_text()) for p in sorted(fx.glob("*/case.json"))]
    if a.only:
        pre = tuple(x.strip() for x in a.only.split(","))
        cases = [c for c in cases if c["id"].startswith(pre)]
    if a.tags:
        want = set(a.tags.split(","))
        cases = [c for c in cases if c["tag"] in want]
    if a.list:
        for c in cases:
            print(f"{c['id']:44} item {str(c.get('spec_item')):>4}  [{c['tag']}] {c['title']}")
        return 0
    tools = pathlib.Path(a.tools)
    failed, tags, missing = [], {}, 0
    for c in cases:
        res = run_case(c, tools)
        if "missing" in res:
            print(f"  NOT RUN {c['id']}: {res['missing']} does not exist")
            missing += 1
            continue
        problems = check(res)
        t = tags.setdefault(c["tag"], [0, 0])
        t[1] += 1
        if problems:
            failed.append(c["id"])
            print(f"  FAIL {c['id']:44} [{c['tag']}] {c['title']}")
            for p in problems:
                print(f"         - {p}")
        else:
            t[0] += 1
            print(f"  ok   {c['id']:44} [{c['tag']}] {c['title']}")
    if missing:
        print(f"NOT RUN: {missing} fixture(s) need a tool that does not exist yet")
        return 3
    ok = len(cases) - len(failed)
    print(f"{ok}/{len(cases)} fixtures pass. " + ", ".join(f"{k}: {v[0]}/{v[1]}" for k, v in sorted(tags.items())))
    if failed:
        print("FAILED: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
