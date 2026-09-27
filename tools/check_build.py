#!/usr/bin/env python3
"""End-to-end checks of the catalog build's failure paths, with a fake `gh` and no network.

    python3 tools/check_build.py

Runs the real tools/build_catalog.py and tools/fetch_sources.sh in a temporary directory, with a
fake `gh` (and `git`) first on PATH, and checks what a reader of the outputs would see. Reads
nothing outside the temporary directory except the two tools. Exits 0 only when every check passes.

What the checks guard against, written before the code they check:

  build, one GitHub batch out of five fails on every attempt (a timeout reply, a dropped
  connection, a rate limit, a reply with data but another error, a null nobody explained):
    - the build exits 0, prints a traceback, or writes or touches any output
    - the failed batch, or an empty answer for it, reaches the cache
    - the batches answered before it are not cached, so a rerun queries them again
    - the cache is left unreadable, or a temporary file is left beside it
    - a failed batch is retried at once, with no growing delay and no jitter
  build, rerun after that failure: queries the answered batches again, or its rows differ from
    a build that never failed
  build, a batch that fails twice and then answers: the build gives up instead of retrying
  build, NOT_FOUND for one repository: more than that one row is dropped, or the build stops
  build, gh missing, not signed in, or its token rejected: a traceback, more than one line,
    retries that cannot help, or outputs written
  build, every lookup already cached and no gh installed: the build refuses to run
  tables: a copy row with a note reads plain "copy"; any other row gains "(see note)"; the data
    file's reuse field changes; "Apache-2.0 AND MIT" is not copy; an AND with a non-permissive
    part, or a lowercase "and", becomes copy
  tables: a seed marked listed_in is also listed as a row, is missing from its category page, or
    stays out of the list after its target page stops listing it
  tables: the software index still claims how many projects were pushed in the last 2 years
  fetch_sources.sh: a failed, partial or unreadable topic search, or a failed list download,
    exits 0 or replaces a list that was already there; gh missing gives more than one line
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

TOOLS = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
BASH = shutil.which("bash") or "/bin/bash"
BATCH = 50
SEEDS = 230          # five batches of 50: 50, 50, 50, 50, 29 after the listed_in seed leaves
FAIL_IN = "o/p120"   # a repository in the third batch

FAKE_GH = r'''#!@PY@
# Fake GitHub CLI. Error shapes copied from gh 2.45.0 replies (NOT_FOUND, exit 4 with no token,
# HTTP 401 with a bad token); the timeout and rate-limit bodies follow GitHub's documented replies.
import json, os, re, sys
base = os.environ["FAKE_GH"]
scn = json.load(open(base + ".json"))
state = json.load(open(base + ".state")) if os.path.exists(base + ".state") else {}
args = sys.argv[1:]
open(base + ".log", "a").write(json.dumps(args) + "\n")

def out(stdout="", stderr="", code=0):
    json.dump(state, open(base + ".state", "w"))
    sys.stdout.write(stdout)
    sys.stderr.write(stderr)
    sys.exit(code)

if scn.get("auth") == "none":
    out(stderr="To get started with GitHub CLI, please run:  gh auth login\nAlternatively, populate the GH_TOKEN "
               "environment variable with a GitHub API authentication token.\n", code=4)
if scn.get("auth") == "bad":
    out('{\n  "message": "Bad credentials",\n  "documentation_url": "https://docs.github.com/rest",\n  "status": "401"\n}',
        "gh: Bad credentials (HTTP 401)\n", 1)
fields = dict(args[i + 1].split("=", 1) for i, a in enumerate(args) if a == "-f")

if args[:2] == ["api", "graphql"]:
    aliases = re.findall(r'(r\d+): repository\(owner: "([^"]*)", name: "([^"]*)"\)', fields["query"])
    slugs = [f"{o}/{n}" for _, o, n in aliases]
    fault = scn.get("fault")
    hit = bool(fault) and fault["in"] in slugs
    if hit:
        state["attempts"] = state.get("attempts", 0) + 1
        hit = fault.get("times") is None or state["attempts"] <= fault["times"]
    if hit:
        kind = fault["kind"]
        if kind == "timeout":
            msg = ("Something went wrong while executing your query. This may be the result of a timeout, "
                   "or it could be a GitHub bug.")
            out(json.dumps({"data": None, "errors": [{"message": msg}]}), f"gh: {msg}\n", 1)
        if kind == "network":
            out("", 'Post "https://api.github.com/graphql": read tcp: connection reset by peer\n', 1)
        if kind == "rate_limited":
            out(json.dumps({"errors": [{"type": "RATE_LIMITED", "message": "API rate limit exceeded"}]}),
                "gh: API rate limit exceeded\n", 1)
    data, errors = {}, []
    for (alias, o, n), slug in zip(aliases, slugs):
        if slug in scn.get("not_found", []):
            data[alias] = None
            errors.append({"type": "NOT_FOUND", "path": [alias], "locations": [{"line": 1, "column": 1}],
                           "message": f"Could not resolve to a Repository with the name '{slug}'."})
            continue
        data[alias] = {"nameWithOwner": slug, "licenseInfo": {"spdxId": scn.get("licenses", {}).get(slug, "MIT")},
                       "primaryLanguage": {"name": "Python"}, "stargazerCount": 1000 - int(n[1:]),
                       "pushedAt": "2026-09-01T00:00:00Z", "isArchived": False, "description": "d",
                       "homepageUrl": None}
    if hit and fault["kind"] == "forbidden_alias":
        data["r0"] = None
        errors.append({"type": "FORBIDDEN", "path": ["r0"], "message": "Resource not accessible by integration"})
    if hit and fault["kind"] == "unexplained_null":
        data["r0"] = None
    body = {"data": data}
    if errors:
        body["errors"] = errors
    out(json.dumps(body), "".join(f"gh: {e['message']}\n" for e in errors), 1 if errors else 0)

if len(args) > 1 and args[0] == "api" and args[1].endswith("/contents/README.md"):
    if args[1] in scn.get("contents_fail", []):
        out('{"message":"Not Found","documentation_url":"https://docs.github.com/rest","status":"404"}',
            "gh: Not Found (HTTP 404)\n", 1)
    out(f"## Games\n\n- [Game of {args[1]}](https://github.com/x/y) - a game\n")

if "search/repositories" in args:
    q, page = fields["q"], int(fields.get("page", "1"))
    kind = scn.get("search_fault", {}).get(f"{q}|{page}")
    if kind == "rate_limit":
        out('{"message":"API rate limit exceeded for user ID 1.","documentation_url":"https://docs.github.com/rest"}',
            "gh: API rate limit exceeded for user ID 1. (HTTP 403)\n", 1)
    if kind == "not_json":
        out("<html>502 Bad Gateway</html>")
    if kind == "no_items":
        out('{"total_count": 0}')
    total = scn.get("topics", {}).get(q.split(":", 1)[1], 0)
    start = (page - 1) * 100
    items = [{"name": f"g{k}", "html_url": f"https://github.com/t/{q.split(':', 1)[1]}-{k}", "topics": ["t"],
              "description": "d"} for k in range(start, min(total, start + 100))]
    out(json.dumps({"total_count": total, "incomplete_results": kind == "incomplete", "items": items}))

out(stderr=f"fake gh: unhandled {args}\n", code=2)
'''

FAKE_GIT = """#!/bin/sh
# Fake git: `git clone ... <dest>` makes an empty entries folder.
for last; do :; done
mkdir -p "$last/entries" && printf '# Fake\\n\\n- Code repository: https://github.com/x/z\\n' > "$last/entries/fake.md"
"""

# Run the build with time.sleep recorded instead of slept, so backoff is measured, not waited for.
PRELUDE = ("import json, runpy, sys, time\n"
           "log = open(sys.argv[1], 'a')\n"
           "time.sleep = lambda s: (log.write(json.dumps(s) + '\\n'), log.flush(), None)[-1]\n"
           "script = sys.argv[2]\n"
           "sys.argv = [script] + sys.argv[3:]\n"
           "runpy.run_path(script, run_name='__main__')\n")

results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f": {detail}"))


def read(path):
    try:
        return open(path, encoding="utf-8").read()
    except OSError:
        return None


class World:
    """A temporary copy of the build: tools/, a fake domain, an out/ tree, a fake gh and git."""

    def __init__(self, root):
        self.root = root
        os.makedirs(os.path.join(root, "tools", "domains"))
        shutil.copy(os.path.join(TOOLS, "build_catalog.py"), os.path.join(root, "tools"))
        self.bin = os.path.join(root, "bin")
        self.empty = os.path.join(root, "empty-bin")
        os.makedirs(self.bin)
        os.makedirs(self.empty)
        open(os.path.join(self.bin, "gh"), "w").write(FAKE_GH.replace("@PY@", PY))
        open(os.path.join(self.bin, "git"), "w").write(FAKE_GIT)
        for f in ("gh", "git"):
            os.chmod(os.path.join(self.bin, f), 0o755)
        self.fake = os.path.join(root, "fake-gh")
        self.src = os.path.join(root, "sources")
        self.out = os.path.join(root, "out")
        seeds = [{"name": f"p{k:03d}", "url": f"https://github.com/o/p{k:03d}", "category": "a" if k < 10 else "b",
                  "why": f"why {k}"} for k in range(SEEDS)]
        seeds[6]["listed_in"] = "catalog/engines.md"
        spec = {"title": "Fake", "intro": ["Intro."], "categories": [
            {"slug": "a", "title": "Alpha", "scope": "first things"},
            {"slug": "b", "title": "Beta", "scope": "second things"}],
            "resources": [{"name": "x/list", "url": "https://github.com/x/list", "covers": "c", "license": "MIT",
                           "use": "parse"}], "seeds": seeds}
        json.dump(spec, open(os.path.join(root, "tools", "domains", "fake.json"), "w"))
        overrides = {
            "o/p000": {"license": "Apache-2.0 AND MIT", "why": "w", "reuse_ok": True, "note": "keep both notices"},
            "o/p002": {"why": "w", "note": "sends telemetry by default"},
            "o/p003": {"why": "w", "note": "a note on a GPL row"},
            "o/p004": {"license": "MIT AND BUSL-1.1", "why": "w", "reuse_ok": True},
            "o/p005": {"license": "Apache-2.0 and MIT", "why": "w", "reuse_ok": True},
        }
        json.dump(overrides, open(os.path.join(root, "tools", "overrides.json"), "w"))
        os.makedirs(os.path.join(root, "catalog"))
        open(os.path.join(root, "catalog", "engines.md"), "w").write(
            "| project |\n|---|\n| [p006](https://github.com/o/p006) |\n")
        open(os.path.join(root, "catalog", "other.md"), "w").write("| project |\n|---|\n| [q](https://github.com/o/q) |\n")
        self.scenario({})

    def scenario(self, scn):
        for ext in (".state", ".log"):
            if os.path.exists(self.fake + ext):
                os.remove(self.fake + ext)
        json.dump({"licenses": {"o/p003": "GPL-3.0"}, **scn}, open(self.fake + ".json", "w"))

    def gh_calls(self):
        log = read(self.fake + ".log") or ""
        return [json.loads(line) for line in log.splitlines()]

    def graphql_slugs(self):
        calls = [c for c in self.gh_calls() if c[:2] == ["api", "graphql"]]
        return [re.findall(r'repository\(owner: "([^"]*)", name: "([^"]*)"\)', c[c.index("-f") + 1]) for c in calls]

    def build(self, path=None):
        sleeps = os.path.join(self.root, "sleeps.log")
        if os.path.exists(sleeps):
            os.remove(sleeps)
        env = {"PATH": path or self.bin, "FAKE_GH": self.fake, "HOME": self.root, "LANG": "C.UTF-8"}
        p = subprocess.run([PY, "-c", PRELUDE, sleeps, os.path.join(self.root, "tools", "build_catalog.py"),
                            "--domain", "fake", "--src", self.src, "--out", self.out],
                           capture_output=True, text=True, env=env, cwd=self.root)
        s = [json.loads(x) for x in (read(sleeps) or "").splitlines()]
        return p, s

    def cache(self):
        text = read(os.path.join(self.src, "github_cache_fake.json"))
        return None if text is None else json.loads(text)

    def outputs(self):
        return {rel: read(os.path.join(self.out, rel)) for rel in ("data/fake.json", "fake/README.md")}


def plant_outputs(w):
    os.makedirs(os.path.join(w.out, "data"), exist_ok=True)
    os.makedirs(os.path.join(w.out, "fake"), exist_ok=True)
    for rel in ("data/fake.json", "fake/README.md"):
        open(os.path.join(w.out, rel), "w").write("SENTINEL " + rel)


def one_line(p):
    """The error is one line, it is the last thing printed, and there is no traceback. Progress lines
    the build prints before it ("N seeds, ...", "  enriched ...") are allowed."""
    lines = [x for x in p.stderr.splitlines() if x.strip()]
    progress = re.compile(r"^\d+ seeds, |^  enriched ")
    errors = [x for x in lines if not progress.match(x)]
    return len(errors) == 1 and errors[0] == lines[-1] and "Traceback" not in p.stderr, lines


def build_checks(tmp):
    enriched = sorted(f"o/p{k:03d}" for k in range(SEEDS) if k != 6)
    for kind in ("timeout", "network", "rate_limited", "forbidden_alias", "unexplained_null"):
        w = World(os.path.join(tmp, f"fail-{kind}"))
        plant_outputs(w)
        w.scenario({"fault": {"kind": kind, "in": FAIL_IN}})
        p, sleeps = w.build()
        batches = w.graphql_slugs()
        firsts = [b[0] for b in batches]
        answered = {f"{o}/{n}".lower() for b in batches[:2] for o, n in b}
        cache = w.cache()
        tag = f"build, batch 3 of 5 fails ({kind})"
        check(f"{tag}: exits non-zero without a traceback", p.returncode != 0 and "Traceback" not in p.stderr,
              f"exit {p.returncode}; stderr tail {p.stderr[-300:]!r}")
        check(f"{tag}: outputs untouched", all(v == "SENTINEL " + k for k, v in w.outputs().items())
              and not os.path.exists(os.path.join(w.out, "fake", "catalog")), w.outputs())
        check(f"{tag}: batches 1-2 cached, nothing from batch 3 on",
              cache is not None and set(cache) == answered and len(answered) == 2 * BATCH,
              f"cache has {None if cache is None else len(cache)} entries; answered {len(answered)}")
        check(f"{tag}: no temporary file left beside the cache",
              not [f for f in os.listdir(w.src) if f != "github_cache_fake.json"] if os.path.isdir(w.src) else False,
              os.listdir(w.src) if os.path.isdir(w.src) else "no sources dir")
        tries = sum(1 for f in firsts if f == firsts[2]) if len(firsts) > 2 else 0
        grows = len(sleeps) >= 2 and all(b > a for a, b in zip(sleeps, sleeps[1:]))
        jitter = len(sleeps) >= 2 and any(abs(b / a - 2) > 1e-9 for a, b in zip(sleeps, sleeps[1:]) if a)
        check(f"{tag}: retried {tries - 1} times, waits growing with jitter",
              tries >= 3 and len(sleeps) == tries - 1 and sleeps[0] >= 1 and grows and jitter,
              f"attempts on batch 3: {tries}; sleeps {[round(s, 2) for s in sleeps]}")
        if kind == "timeout":
            w.scenario({})
            p2, _ = w.build()
            again = {f"{o}/{n}".lower() for b in w.graphql_slugs() for o, n in b}
            check("build, rerun after the failure: asks GitHub only for what was not cached",
                  p2.returncode == 0 and again == {s.lower() for s in enriched} - answered,
                  f"exit {p2.returncode}; re-queried {len(again)}; stderr {p2.stderr[-300:]!r}")
            clean = World(os.path.join(tmp, "clean"))
            p3, _ = clean.build()
            a_rows = json.loads(read(os.path.join(w.out, "data", "fake.json")) or "{}").get("entries")
            b_rows = json.loads(read(os.path.join(clean.out, "data", "fake.json")) or "{}").get("entries")
            check("build, rerun after the failure: same rows as a build that never failed",
                  p3.returncode == 0 and a_rows is not None and a_rows == b_rows,
                  f"clean exit {p3.returncode}; rows {None if a_rows is None else len(a_rows)} vs "
                  f"{None if b_rows is None else len(b_rows)}")

    w = World(os.path.join(tmp, "transient"))
    w.scenario({"fault": {"kind": "timeout", "in": FAIL_IN, "times": 2}})
    p, sleeps = w.build()
    cache = w.cache()
    check("build, batch 3 fails twice then answers: build succeeds after two waits",
          p.returncode == 0 and len(sleeps) == 2 and cache is not None and len(cache) == len(enriched),
          f"exit {p.returncode}; sleeps {sleeps}; cached {None if cache is None else len(cache)}; {p.stderr[-300:]!r}")

    w = World(os.path.join(tmp, "not-found"))
    w.scenario({"not_found": ["o/p150"]})
    p, _ = w.build()
    data = json.loads(read(os.path.join(w.out, "data", "fake.json")) or "{}")
    rows = {r["name"] for r in data.get("entries", [])}
    drops = {d["name"]: d["reason"] for d in data.get("dropped", [])}
    check("build, NOT_FOUND on one repository drops that row only",
          p.returncode == 0 and "p150" not in rows and drops.get("p150") == "repository not found on GitHub"
          and len(rows) == SEEDS - 2 and len(rows) + len(drops) == SEEDS,
          f"exit {p.returncode}; rows {len(rows)}; drops {drops}; {p.stderr[-300:]!r}")

    # Tables, read from the successful NOT_FOUND build.
    readme = read(os.path.join(w.out, "fake", "README.md")) or ""
    page_a = read(os.path.join(w.out, "fake", "catalog", "a.md")) or ""
    by = {r["name"]: r for r in data.get("entries", [])}
    rowline = lambda n: next((x for x in page_a.splitlines() if x.startswith(f"| [{n}]")), "")
    cell = lambda n: (rowline(n).split(" | ") + ["", ""])[1]
    check("tables: copy row with a note reads \"copy (see note)\"",
          cell("p000") == "copy (see note)" and cell("p002") == "copy (see note)",
          f"p000 {cell('p000')!r}, p002 {cell('p002')!r}")
    check("tables: copy row without a note, and a study row with a note, are unchanged",
          cell("p001") == "copy" and cell("p003") == "study only", f"p001 {cell('p001')!r}, p003 {cell('p003')!r}")
    check("tables: the data file's reuse field stays \"copy\"",
          by.get("p000", {}).get("reuse") == "copy" and by.get("p002", {}).get("reuse") == "copy",
          {k: by.get(k, {}).get("reuse") for k in ("p000", "p002")})
    check("tables: \"Apache-2.0 AND MIT\" is copy",
          by.get("p000", {}).get("license") == "Apache-2.0 AND MIT" and by["p000"]["reuse"] == "copy",
          by.get("p000"))
    check("tables: \"MIT AND BUSL-1.1\" and a lowercase \"and\" are not copy",
          by.get("p004", {}).get("reuse") == "check" and by.get("p005", {}).get("reuse") == "check",
          {k: by.get(k, {}).get("reuse") for k in ("p004", "p005")})
    check("tables: a listed_in seed is not a row, and its category page links where it is listed",
          "p006" not in rows and "](https://github.com/o/p006)" in page_a and "](../../catalog/engines.md)" in page_a
          and not rowline("p006"), page_a[-600:])
    check("tables: no count of projects pushed in the last 2 years", readme and "pushed in the last" not in readme,
          [x for x in readme.splitlines() if "pushed" in x])

    w2 = World(os.path.join(tmp, "listed-in-stale"))
    spec_path = os.path.join(w2.root, "tools", "domains", "fake.json")
    spec = json.load(open(spec_path))
    spec["seeds"][6]["listed_in"] = "catalog/other.md"
    json.dump(spec, open(spec_path, "w"))
    plant_outputs(w2)
    p, _ = w2.build()
    ok, lines = one_line(p)
    check("tables: listed_in a page that does not list the repository stops the build",
          p.returncode != 0 and ok and all(v == "SENTINEL " + k for k, v in w2.outputs().items()),
          f"exit {p.returncode}; stderr {lines}")

    for name, scn, path in (("gh missing", {}, "empty"), ("gh not signed in", {"auth": "none"}, None),
                            ("gh token rejected", {"auth": "bad"}, None)):
        w = World(os.path.join(tmp, name.replace(" ", "-")))
        plant_outputs(w)
        w.scenario(scn)
        p, sleeps = w.build(path=w.empty if path == "empty" else None)
        ok, lines = one_line(p)
        check(f"build, {name}: one line, no traceback, no retries, outputs untouched",
              p.returncode != 0 and ok and "gh" in p.stderr and not sleeps and len(w.gh_calls()) <= 1
              and all(v == "SENTINEL " + k for k, v in w.outputs().items()),
              f"exit {p.returncode}; stderr {lines[-3:]}; sleeps {sleeps}; gh calls {len(w.gh_calls())}")

    w = World(os.path.join(tmp, "cached-no-gh"))
    p1, _ = w.build()
    p2, _ = w.build(path=w.empty)
    check("build, every lookup cached and no gh installed: builds",
          p1.returncode == 0 and p2.returncode == 0, f"exits {p1.returncode}, {p2.returncode}; {p2.stderr[-300:]!r}")


def fetch_checks(tmp):
    lists = ("bobeff.md", "michelpereira.md", "topic.json", "topics_extra.json")
    extra = ["fighting-game", "beat-em-up", "rollback-netcode", "racing-game", "sports-game", "rhythm-game",
             "sandbox-game"]
    topics = {"open-source-game": 250, **{t: 3 for t in extra}}
    cases = [
        ("topic search page 3 rate-limited", {"search_fault": {"topic:open-source-game|3": "rate_limit"}}),
        ("a genre topic search fails after the main one succeeded", {"search_fault": {"topic:racing-game|1": "rate_limit"}}),
        ("topic search reply marked incomplete", {"search_fault": {"topic:open-source-game|2": "incomplete"}}),
        ("topic search reply not JSON", {"search_fault": {"topic:open-source-game|1": "not_json"}}),
        ("topic search reply without items", {"search_fault": {"topic:sports-game|1": "no_items"}}),
        ("list download fails", {"contents_fail": ["repos/bobeff/open-source-games/contents/README.md"]}),
    ]
    for name, scn in cases:
        w = World(os.path.join(tmp, "fetch-" + name.replace(" ", "-")))
        work = os.path.join(w.root, "work")
        os.makedirs(os.path.join(work, "sources"))
        for f in lists:
            open(os.path.join(work, "sources", f), "w").write("SENTINEL " + f)
        w.scenario({"topics": topics, **scn})
        p = subprocess.run([BASH, os.path.join(TOOLS, "fetch_sources.sh")], capture_output=True, text=True, cwd=work,
                           env={"PATH": w.bin + os.pathsep + os.environ.get("PATH", ""), "FAKE_GH": w.fake,
                                "HOME": w.root})
        kept = {f: read(os.path.join(work, "sources", f)) == "SENTINEL " + f for f in lists}
        check(f"fetch_sources.sh, {name}: exits non-zero, every list left as it was",
              p.returncode != 0 and all(kept.values()), f"exit {p.returncode}; kept {kept}; {p.stderr[-300:]!r}")

    w = World(os.path.join(tmp, "fetch-ok"))
    work = os.path.join(w.root, "work")
    os.makedirs(work)
    w.scenario({"topics": topics})
    p = subprocess.run([BASH, os.path.join(TOOLS, "fetch_sources.sh")], capture_output=True, text=True, cwd=work,
                       env={"PATH": w.bin + os.pathsep + os.environ.get("PATH", ""), "FAKE_GH": w.fake, "HOME": w.root})
    topic = json.loads(read(os.path.join(work, "sources", "topic.json")) or "null")
    extra_out = json.loads(read(os.path.join(work, "sources", "topics_extra.json")) or "null")
    check("fetch_sources.sh, every search answers: writes every list in full",
          p.returncode == 0 and topic is not None and len(topic) == 250 and extra_out is not None
          and len(extra_out) == 3 * len(extra) and "bobeff" in (read(os.path.join(work, "sources", "bobeff.md")) or "")
          and not [f for f in os.listdir(os.path.join(work, "sources")) if f.endswith(".tmp")],
          f"exit {p.returncode}; topic {None if topic is None else len(topic)}; extra "
          f"{None if extra_out is None else len(extra_out)}; {p.stderr[-300:]!r}")

    w = World(os.path.join(tmp, "fetch-no-gh"))
    work = os.path.join(w.root, "work")
    os.makedirs(work)
    nogh = os.path.join(w.root, "nogh-bin")
    os.makedirs(nogh)
    for tool in ("mkdir", "rm", "mv", "python3", "cat"):
        found = shutil.which(tool)
        if found:
            os.symlink(found, os.path.join(nogh, tool))
    shutil.copy(os.path.join(w.bin, "git"), nogh)
    p = subprocess.run([BASH, os.path.join(TOOLS, "fetch_sources.sh")], capture_output=True, text=True, cwd=work,
                       env={"PATH": nogh, "HOME": w.root})
    ok, lines = one_line(p)
    check("fetch_sources.sh, gh missing: exits non-zero with one line naming gh",
          p.returncode != 0 and ok and "gh" in p.stderr, f"exit {p.returncode}; stderr {lines}")


def main():
    with tempfile.TemporaryDirectory(prefix="check_build.") as tmp:
        build_checks(tmp)
        fetch_checks(tmp)
    failed = [n for n, ok in results if not ok]
    print(f"{len(results)} checks, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
