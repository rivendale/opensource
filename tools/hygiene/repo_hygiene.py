#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Repository hygiene checks shared by the rivendale open-source repos.

    python3 tools/hygiene/repo_hygiene.py [--root DIR] [--config .hygiene.json] [--base REF]
    python3 tools/hygiene/repo_hygiene.py --print-root-safety    the config's root_safety commands, one per line
    python3 tools/hygiene/repo_hygiene.py --selftest             check the checker in a temp git repo, no network

Checks, each configured in the repo's .hygiene.json (schema: tools/hygiene/README.md):
  modes         a tracked file with a shebang went from 100755 to 100644 between the merge base of --base and HEAD
                (pushing through the GitHub API resets modes)
  invisible     a raw character a reader cannot see in a tracked text file or path: every format (Cf) and control (Cc)
                character except whitespace, plus the U+E0000 tag block; the same set as strip_hidden() in
                tools/build_catalog.py. Bidi controls are Trojan Source (CVE-2021-42574). A BOM at file start is allowed.
  claims        a number written in a file disagrees with a count taken from the repo ("12 skills" vs skills/*/SKILL.md)
  stale         a dated marker ("checked YYYY-MM-DD") older than max_age_days; fenced code blocks are skipped;
                a warning unless stale_fails is true
  instructions  an agent instruction file is over its byte limit, or its sentinel line is missing or not the last line
Root safety (running commands as root in a throwaway container) is a job in .github/workflows/hygiene.yml.

Exit 0 when clean, 1 on any failure (warnings print but do not fail), 2 when the config is unreadable or invalid.
Standard library only; needs git on PATH.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata

DEFAULTS = {
    "modes": True,
    "invisible": True,
    "invisible_allow": [],
    "claims": [],
    "stale": True,
    "stale_pattern": r"\b(?:checked|verified|as of)[:\s]+(\d{4}-\d{2}-\d{2})\b",
    "stale_globs": ["**/*.md"],
    "stale_exclude": [],
    "max_age_days": 45,
    "stale_fails": False,
    "instructions": [],
    "root_safety": [],
}
CLAIM_KEYS = {"file", "pattern", "count_glob", "count_json", "count_lines"}
INSTRUCTION_KEYS = {"file", "max_bytes", "sentinel"}
BIDI = set("\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")
BOM = "\ufeff"


class ConfigError(Exception):
    pass


# ---------------------------------------------------------------- helpers

def git(root, *args, text=True):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=text, check=True).stdout


def tracked(root):
    return [p for p in git(root, "ls-files", "-z").split("\0") if p]


def is_hidden(ch):
    """True for a character strip_hidden() in tools/build_catalog.py would remove, or one in the tag block."""
    cp = ord(ch)
    if 0xE0000 <= cp <= 0xE007F:
        return True
    return not ch.isspace() and unicodedata.category(ch) in ("Cf", "Cc")


def _hidden_rx():
    ranges, start, prev = [], None, None
    for cp in range(0x110000):
        if 0xD800 <= cp <= 0xDFFF or not is_hidden(chr(cp)):
            continue
        if start is not None and cp == prev + 1:
            prev = cp
            continue
        if start is not None:
            ranges.append((start, prev))
        start = prev = cp
    ranges.append((start, prev))
    return re.compile("[" + "".join(re.escape(chr(a)) if a == b else f"{re.escape(chr(a))}-{re.escape(chr(b))}"
                                    for a, b in ranges) + "]")


HIDDEN = _hidden_rx()


def describe(ch):
    kind = "bidi control" if ch in BIDI else "tag character" if 0xE0000 <= ord(ch) <= 0xE007F else \
        "control character" if unicodedata.category(ch) == "Cc" else "format character"
    name = unicodedata.name(ch, "")
    return f"U+{ord(ch):04X} ({kind}{', ' + name if name else ''})"


def show(path):
    """A path safe to print: ascii() when it holds anything hidden or non-printable."""
    return path if path.isprintable() and not HIDDEN.search(path) else ascii(path)


def glob_rx(pattern):
    """Gitignore-style glob to regex: * and ? stay within one path segment, **/ spans zero or more directories."""
    out, i, n = [], 0, len(pattern)
    while i < n:
        c = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        elif c == "[" and "]" in pattern[i + 2:]:
            j = pattern.index("]", i + 2)
            body = pattern[i + 1:j]
            out.append("[" + ("^" + body[1:] if body.startswith("!") else body).replace("\\", "\\\\") + "]")
            i = j + 1
        else:
            out.append(re.escape(c))
            i += 1
    return re.compile("".join(out))


def matcher(patterns):
    rxs = [glob_rx(p) for p in patterns]
    return lambda path: any(rx.fullmatch(path) for rx in rxs)


def read_text(full):
    """The file's text, or None for a symlink, a missing file, a binary (a NUL byte) or anything not UTF-8."""
    if os.path.islink(full) or not os.path.isfile(full):
        return None
    with open(full, "rb") as f:
        data = f.read()
    if b"\0" in data:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


# ---------------------------------------------------------------- config

def _globs(cfg, key):
    v = cfg[key]
    if not isinstance(v, list):
        raise ConfigError(f"{key} must be a list")
    out = []
    for item in v:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict) and isinstance(item.get("glob"), str) and isinstance(item.get("why"), str) \
                and set(k for k in item if not k.startswith("_")) <= {"glob", "why"}:
            out.append(item["glob"])
        else:
            raise ConfigError(f"{key} entries are a glob string or {{\"glob\": ..., \"why\": ...}}: {item!r}")
    return out


def _known(obj, keys, where):
    extra = sorted(k for k in obj if k not in keys and not k.startswith("_"))
    if extra:
        raise ConfigError(f"{where}: unknown key(s) {', '.join(extra)}")


def load_config(cfg):
    """Defaults filled in and every value checked. Keys starting with _ are comments, at any level."""
    if not isinstance(cfg, dict):
        raise ConfigError("the config must be a JSON object")
    _known(cfg, DEFAULTS, "config")
    cfg = {**DEFAULTS, **{k: v for k, v in cfg.items() if not k.startswith("_")}}
    for key in ("modes", "invisible", "stale", "stale_fails"):
        if not isinstance(cfg[key], bool):
            raise ConfigError(f"{key} must be true or false")
    if not isinstance(cfg["max_age_days"], int) or isinstance(cfg["max_age_days"], bool) or cfg["max_age_days"] < 0:
        raise ConfigError("max_age_days must be a whole number of days")
    cfg["invisible_allow"] = _globs(cfg, "invisible_allow")
    cfg["stale_globs"] = _globs(cfg, "stale_globs")
    cfg["stale_exclude"] = _globs(cfg, "stale_exclude")
    try:
        rx = re.compile(cfg["stale_pattern"], re.IGNORECASE)
    except (re.error, TypeError) as e:
        raise ConfigError(f"stale_pattern is not a regex: {e}")
    if rx.groups < 1:
        raise ConfigError("stale_pattern needs a group that captures the YYYY-MM-DD date")
    for c in cfg["claims"]:
        if not isinstance(c, dict):
            raise ConfigError(f"claims entries are objects: {c!r}")
        _known(c, CLAIM_KEYS, f"claim {c.get('file')!r}")
        counts = [k for k in ("count_glob", "count_json", "count_lines") if k in c]
        if not isinstance(c.get("file"), str) or not isinstance(c.get("pattern"), str) or len(counts) != 1:
            raise ConfigError(f"a claim needs file, pattern and exactly one of count_glob, count_json, count_lines: {c!r}")
        try:
            if re.compile(c["pattern"]).groups < 1:
                raise ConfigError(f"claim pattern needs a group that captures the number: {c['pattern']!r}")
        except re.error as e:
            raise ConfigError(f"claim pattern is not a regex: {c['pattern']!r}: {e}")
    for item in cfg["instructions"]:
        if not isinstance(item, dict) or not isinstance(item.get("file"), str):
            raise ConfigError(f"instructions entries are objects with a file: {item!r}")
        _known(item, INSTRUCTION_KEYS, f"instructions {item['file']!r}")
        mb = item.get("max_bytes", 32768)
        if not isinstance(mb, int) or isinstance(mb, bool) or mb <= 0:
            raise ConfigError(f"instructions {item['file']!r}: max_bytes must be a positive whole number")
        if "sentinel" in item and (not isinstance(item["sentinel"], str) or not item["sentinel"].strip()
                                   or "\n" in item["sentinel"]):
            raise ConfigError(f"instructions {item['file']!r}: sentinel must be one non-empty line")
    rs = cfg["root_safety"]
    if not isinstance(rs, list) or not all(isinstance(x, str) and x.strip() and "\n" not in x for x in rs):
        raise ConfigError("root_safety must be a list of one-line shell commands")
    return cfg


# ---------------------------------------------------------------- checks

def check_modes(root, base, out):
    if not base:
        return
    try:
        raw = git(root, "diff", "--raw", "-z", "-M", "--no-abbrev", f"{base}...HEAD")
    except subprocess.CalledProcessError as e:
        out["fail"].append(f"modes: cannot diff against {base}: {e.stderr.strip()}")
        return
    parts = raw.split("\0")
    i = 0
    while i < len(parts) - 1:
        head = parts[i]
        if not head.startswith(":"):
            i += 1
            continue
        src_mode, dst_mode, _src, dst_sha, status = head[1:].split(" ")
        npaths = 2 if status[:1] in ("R", "C") else 1
        path = parts[i + npaths]
        i += 1 + npaths
        if src_mode != "100755" or dst_mode != "100644":
            continue
        blob = git(root, "cat-file", "blob", dst_sha, text=False)
        if blob[:2] == b"#!":
            out["fail"].append(f"modes: {show(path)} lost its executable bit (100755 -> 100644); "
                               f"restore with: git update-index --chmod=+x {show(path)}")


def check_invisible(root, files, cfg, out):
    allowed = matcher(cfg["invisible_allow"])
    for path in files:
        if allowed(path):
            continue
        m = HIDDEN.search(path)
        if m:
            out["fail"].append(f"invisible: the path {show(path)} holds raw {describe(m.group())}; rename it")
        full = os.path.join(root, path)
        if os.path.islink(full):
            target = os.readlink(full)
            m = HIDDEN.search(target)
            if m:
                out["fail"].append(f"invisible: the symlink {show(path)} points at a target holding raw {describe(m.group())}")
            continue
        text = read_text(full)
        if text is None:
            continue
        for n, line in enumerate(text.split("\n"), 1):
            for m in HIDDEN.finditer(line):
                if n == 1 and m.start() == 0 and m.group() == BOM:
                    continue
                out["fail"].append(f"invisible: {show(path)}:{n}:{m.start() + 1} raw {describe(m.group())}; "
                                   f"write it as an escape (\\u{ord(m.group()):04x} or an HTML entity)")


def count_for(root, files, claim):
    if "count_glob" in claim:
        match = matcher([claim["count_glob"]])
        return sum(1 for p in files if match(p))
    if "count_json" in claim:  # {"file": ..., "key": "a.b"} -> len(value at that key)
        spec = claim["count_json"]
        with open(os.path.join(root, spec["file"]), encoding="utf-8") as f:
            v = json.load(f)
        for k in filter(None, spec.get("key", "").split(".")):
            v = v[k]
        return len(v)
    spec = claim["count_lines"]  # {"file": ..., "pattern": regex} -> lines that match
    rx = re.compile(spec["pattern"])
    with open(os.path.join(root, spec["file"]), encoding="utf-8") as f:
        return sum(1 for line in f if rx.search(line))


def check_claims(root, files, cfg, out):
    for claim in cfg["claims"]:
        try:
            with open(os.path.join(root, claim["file"]), encoding="utf-8") as f:
                text = f.read()
            actual = count_for(root, files, claim)
        except (OSError, ValueError, KeyError, TypeError, IndexError, re.error) as e:
            out["fail"].append(f"claims: {claim['file']}: cannot check {claim['pattern']!r}: {type(e).__name__}: {e}")
            continue
        found = [m.group(1) for m in re.finditer(claim["pattern"], text)]
        if not found:
            out["fail"].append(f"claims: {claim['file']}: pattern {claim['pattern']!r} not found")
            continue
        for stated in found:
            if int(stated.replace(",", "")) != actual:
                out["fail"].append(f"claims: {claim['file']} states {stated} for {claim['pattern']!r}; "
                                   f"the repo has {actual}")


FENCE = re.compile(r" {0,3}(`{3,}|~{3,})")


def check_stale(root, files, cfg, out, today):
    rx = re.compile(cfg["stale_pattern"], re.IGNORECASE)
    wanted, excluded = matcher(cfg["stale_globs"]), matcher(cfg["stale_exclude"])
    limit = cfg["max_age_days"]
    bucket = "fail" if cfg["stale_fails"] else "warn"
    for path in files:
        if not wanted(path) or excluded(path):
            continue
        text = read_text(os.path.join(root, path))
        if text is None:
            continue
        fence = None  # the opening fence while inside a fenced code block
        old = []  # (date, line) of each stale marker; one message per file
        for n, line in enumerate(text.split("\n"), 1):
            f = FENCE.match(line)
            if fence is None and f:
                fence = f.group(1)
                continue
            if fence is not None:
                if f and f.group(1)[0] == fence[0] and len(f.group(1)) >= len(fence) \
                        and not line[f.end():].strip():
                    fence = None
                continue
            for m in rx.finditer(line):
                try:
                    when = dt.date.fromisoformat(m.group(1))
                except (ValueError, TypeError):
                    continue
                if (today - when).days > limit:
                    old.append((when, n))
        if old:
            when, n = min(old)
            out[bucket].append(f"stale: {show(path)}:{n} {len(old)} dated marker(s) older than {limit} days; "
                               f"oldest {when} ({(today - when).days} days ago). Recheck and redate, or drop the date")


def check_instructions(root, cfg, out):
    for item in cfg["instructions"]:
        path = os.path.join(root, item["file"])
        if os.path.islink(path) or not os.path.isfile(path):
            out["fail"].append(f"instructions: {item['file']} is missing (or a symlink)")
            continue
        size = os.path.getsize(path)
        limit = item.get("max_bytes", 32768)
        if size > limit:
            out["fail"].append(f"instructions: {item['file']} is {size} bytes, over its limit of {limit}")
        sentinel = item.get("sentinel")
        if sentinel:
            text = read_text(path)
            lines = [l for l in (text or "").split("\n") if l.strip()]
            if not lines or lines[-1].strip() != sentinel.strip():
                out["fail"].append(f"instructions: {item['file']} must end with the sentinel line {sentinel!r}")


def run(root, cfg, base, today=None):
    cfg = load_config(cfg)
    out = {"fail": [], "warn": []}
    files = tracked(root)
    if cfg["modes"]:
        check_modes(root, base, out)
    if cfg["invisible"]:
        check_invisible(root, files, cfg, out)
    check_claims(root, files, cfg, out)
    if cfg["stale"]:
        check_stale(root, files, cfg, out, today or dt.date.today())
    check_instructions(root, cfg, out)
    return out


# ---------------------------------------------------------------- selftest

def selftest():
    """Every check against a planted defect in a temp git repo. No network, no user or system git config."""
    ok = True

    def expect(name, cond):
        nonlocal ok
        print(("PASS  " if cond else "FAIL  ") + name)
        ok &= bool(cond)

    def fails(r, *needles):
        return any(all(s in x for s in needles) for x in r["fail"])

    with tempfile.TemporaryDirectory() as d:
        os.environ.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1", HOME=d,
                          GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
                          GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
        repo = os.path.join(d, "repo")
        os.mkdir(repo)

        def sh(*a):
            subprocess.run(["git", "-C", repo, "-c", "commit.gpgsign=false", *a], check=True, capture_output=True)

        def put(rel, text, mode=0o644):
            full = os.path.join(repo, rel)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8", newline="") as f:
                f.write(text)
            os.chmod(full, mode)

        sh("init", "-q")
        sh("config", "core.fileMode", "true")
        for s in "ab":
            put(f"skills/{s}/SKILL.md", "x\n")
        put("skills/a/nested/SKILL.md", "not a skill dir\n")
        put("run.sh", "#!/bin/sh\necho hi\n", 0o755)
        put("old name.sh", "#!/bin/sh\necho renamed\n", 0o755)
        put("data.txt", "no shebang\n", 0o755)
        put("README.md", "Two skills: 2 skills.\nchecked 2026-01-01\n\tTabs, CRLF\r\n and a BOM later are fine.\n")
        put("bom.txt", BOM + "a file that starts with a BOM\n")
        put("AGENTS.md", "rules\nSentinel: end\n\n")
        put("fixtures/trap.json", '{"t": "\u202e"}\n')
        sh("add", "-A")
        sh("commit", "-qm", "base")
        cfg = {"_comment": "keys starting with _ are comments",
               "claims": [{"file": "README.md", "pattern": r"(\d+) skills", "count_glob": "skills/*/SKILL.md"}],
               "instructions": [{"file": "AGENTS.md", "max_bytes": 100, "sentinel": "Sentinel: end"}],
               "invisible_allow": [{"glob": "fixtures/**", "why": "planted on purpose"}]}
        today = dt.date(2026, 1, 20)
        r = run(repo, cfg, "HEAD", today)
        expect("clean repo: no failures, no warnings (BOM at start, tabs, CR, allow-listed fixture)",
               r == {"fail": [], "warn": []})
        expect("count_glob * stays in one directory", not fails(r, "claims"))

        sh("mv", "old name.sh", "new name.sh")
        for name in ("run.sh", "data.txt", "new name.sh"):
            os.chmod(os.path.join(repo, name), 0o644)
        put("README.md", "Now 3 skills.\nchecked 2025-10-01\n```\nchecked 2020-01-01 in a fence\n```\n"
                         "~~~~\n```\nchecked 2020-02-02 still fenced\n~~~~\nverified: 2025-09-09\n")
        put("x.py", "s = 'admin\u202e'  # bidi\nt = '1\u200b2'\nu = '\x1b[31m'\nv = 'tag\U000e0041'\n"
                    "w = 'soft\u00adhyphen'\nz = 'late \ufeff BOM'\n")
        put("bad\u200bname.txt", "x\n")
        put("AGENTS.md", "Sentinel: end\nappended after the sentinel\n")
        sh("add", "-A")
        sh("commit", "-qm", "bad")
        r = run(repo, cfg, "HEAD~1", today)
        expect("lost executable bit is caught", fails(r, "run.sh lost its executable bit"))
        expect("lost executable bit is caught through a rename and a space", fails(r, "new name.sh lost"))
        expect("a mode change on a file without a shebang is ignored", not fails(r, "data.txt"))
        expect("bidi control is caught", fails(r, "x.py:1:", "U+202E", "bidi"))
        expect("zero-width space is caught", fails(r, "x.py:2:", "U+200B"))
        expect("ESC control character is caught", fails(r, "x.py:3:", "U+001B"))
        expect("tag-block character is caught", fails(r, "x.py:4:", "U+E0041", "tag"))
        expect("soft hyphen (Cf) is caught", fails(r, "x.py:5:", "U+00AD"))
        expect("a BOM after the start of the file is caught", fails(r, "x.py:6:", "U+FEFF"))
        expect("a hidden character in a path is caught and printed escaped",
               fails(r, "the path 'bad\\u200bname.txt'"))
        expect("no message holds a raw hidden character", not any(HIDDEN.search(x) for x in r["fail"]))
        expect("README count drift is caught", fails(r, "states 3", "has 2"))
        expect("sentinel not last is caught", fails(r, "must end with the sentinel"))
        warned = "\n".join(r["warn"])
        expect("stale date warns, does not fail", "README.md:" in warned and not fails(r, "stale"))
        expect("dates inside ``` and ~~~~ fences are skipped", "2020-" not in warned)
        expect("the line after a fence is checked again; one message per file, oldest first",
               len(r["warn"]) == 1 and "README.md:10 2 dated marker(s)" in warned and "oldest 2025-09-09" in warned)
        r = run(repo, {**cfg, "stale_fails": True}, "HEAD~1", today)
        expect("stale_fails turns the warning into a failure", fails(r, "stale: README.md:10 "))
        r = run(repo, {**cfg, "stale_pattern": r"reviewed (\d{4}-\d{2}-\d{2})"}, "HEAD~1", today)
        expect("a custom stale_pattern replaces the default", not r["warn"])
        r = run(repo, {**cfg, "stale_exclude": ["README.md"]}, "HEAD~1", today)
        expect("stale_exclude skips a file", not r["warn"])
        r = run(repo, cfg, "HEAD~1", dt.date(2025, 9, 1))
        expect("a date in the future is not stale", not r["warn"])
        r = run(repo, {**cfg, "invisible_allow": ["x.py"]}, "HEAD~1", today)
        expect("invisible_allow skips a listed file", not fails(r, "x.py"))
        r = run(repo, {**cfg, "invisible_allow": ["*.py"]}, "HEAD~1", today)
        expect("globs: *.py matches only at the top level", not fails(r, "x.py"))
        r = run(repo, {**cfg, "invisible_allow": []}, "HEAD~1", today)
        expect("without its allow-list entry the fixture is caught", fails(r, "fixtures/trap.json:1:"))
        r = run(repo, {**cfg, "modes": False, "invisible": False}, "HEAD~1", today)
        expect("modes and invisible can be turned off", not fails(r, "modes:") and not fails(r, "invisible:"))
        big = {**cfg, "instructions": [{"file": "AGENTS.md", "max_bytes": 5}]}
        expect("byte limit is enforced", fails(run(repo, big, None, today), "over its limit of 5"))
        r = run(repo, {**cfg, "instructions": [{"file": "MISSING.md"}]}, None, today)
        expect("a missing instruction file fails", fails(r, "MISSING.md is missing"))
        r = run(repo, {**cfg, "claims": [{"file": "NOPE.md", "pattern": r"(\d+)", "count_glob": "*"}]}, None, today)
        expect("a claim on a missing file fails instead of crashing", fails(r, "NOPE.md: cannot check"))
        r = run(repo, {**cfg, "claims": [{"file": "README.md", "pattern": r"(\d+) skills",
                                          "count_lines": {"file": "x.py", "pattern": r"^\w ="}}]}, None, today)
        expect("count_lines counts matching lines", fails(r, "states 3", "has 6"))
        r = run(repo, cfg, "no-such-ref", today)
        expect("an unknown --base fails", fails(r, "cannot diff against no-such-ref"))
        for bad, why in (({"stale_globz": []}, "unknown key"), ({"stale_pattern": "no group"}, "needs a group"),
                         ({"invisible_allow": [{"glob": "x"}]}, "glob"), ({"root_safety": ["a\nb"]}, "one-line"),
                         ({"claims": [{"file": "a", "pattern": "(1)"}]}, "exactly one"),
                         ({"max_age_days": "45"}, "whole number")):
            try:
                run(repo, bad, None, today)
                expect(f"config error: {why}", False)
            except ConfigError as e:
                expect(f"config error: {why}", why in str(e))
    print("all checks hold" if ok else "SELFTEST FAILED")
    return 0 if ok else 1


# ---------------------------------------------------------------- main

def annotate(level, msg):
    if os.environ.get("GITHUB_ACTIONS") == "true":
        msg = msg.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        return f"::{level}::{msg}"
    return f"{'FAIL' if level == 'error' else 'WARN'}  {msg}"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--config", help="config path relative to --root (default .hygiene.json, optional)")
    ap.add_argument("--base", help="git ref to compare modes against (a PR's base commit)")
    ap.add_argument("--today", type=dt.date.fromisoformat, help="date for the stale check, YYYY-MM-DD")
    ap.add_argument("--print-root-safety", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    cfg_path = os.path.join(a.root, a.config or ".hygiene.json")
    cfg = {}
    try:
        if os.path.isfile(cfg_path):
            with open(cfg_path, encoding="utf-8") as f:
                cfg = json.load(f)
        elif a.config:
            raise ConfigError(f"{cfg_path} does not exist")
        if a.print_root_safety:
            for cmd in load_config(cfg)["root_safety"]:
                print(cmd)
            return 0
        r = run(a.root, cfg, a.base, a.today)
    except (ConfigError, ValueError) as e:
        print(annotate("error", f"config {cfg_path}: {e}"))
        return 2
    for w in r["warn"]:
        print(annotate("warning", w))
    for x in r["fail"]:
        print(annotate("error", x))
    print(f"{len(r['fail'])} failure(s), {len(r['warn'])} warning(s)")
    return 1 if r["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
