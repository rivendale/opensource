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
                character except tab, LF, CR, FF and VT, the U+E0000 tag block, blank fillers (EXTRA_HIDDEN), and a
                variation selector after a character it cannot modify; also a text file that is not valid UTF-8.
                Bidi controls are Trojan Source (CVE-2021-42574). A BOM at file start is allowed. Binary files
                (git's rule: a NUL in the first 8000 bytes, or -text / binary in .gitattributes) are skipped.
  claims        a number written in a file disagrees with a count taken from the repo ("12 skills" vs skills/*/SKILL.md)
  stale         a dated marker ("checked YYYY-MM-DD") older than max_age_days; fenced code blocks are skipped;
                a warning unless stale_fails is true
  instructions  an agent instruction file is over its byte limit, or its sentinel line is missing or not the last line
With --base, a change that loosens .hygiene.json against the base prints a notice.
Root safety (running commands as root in a throwaway container) is tools/hygiene/root_safety.sh, run by
.github/workflows/hygiene.yml.

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


# Blank-looking characters that are not whitespace and not Cf/Cc: the Hangul fillers (Lo), the braille blank (So)
# and the combining grapheme joiner (Mn).
EXTRA_HIDDEN = {0x115F, 0x1160, 0x3164, 0xFFA0, 0x2800, 0x034F}
# The only control characters allowed raw. str.isspace() would also let 0x1C-0x1F and U+0085 through.
WHITESPACE = set("\t\n\r\f\v")
VS_RX = re.compile("[\U0000FE00-\U0000FE0F\U000E0100-\U000E01EF]")
# A variation selector is legitimate right after a character it can modify: a symbol or emoji (So, Sm, Sk), the
# keycap bases, a few emoji with other categories, and the scripts with standardized or ideographic variants.
VS_BASES = {0x23, 0x2A, *range(0x30, 0x3A), 0x203C, 0x2049, 0x2139, 0x3030, 0x303D}
CJK = ((0x2E80, 0x2FDF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF), (0x20000, 0x3FFFF))
VS_SCRIPTS = ((0x1000, 0x109F), (0x1800, 0x18AF), (0xA840, 0xA87F))  # Myanmar, Mongolian, Phags-pa


def is_hidden(ch):
    """A character a reader cannot see: every Cf and Cc character except the five whitespace controls (the set
    strip_hidden() in tools/build_catalog.py removes, without the extra controls isspace() exempts), the U+E0000
    tag block, and EXTRA_HIDDEN. Variation selectors depend on what precedes them; see vs_ok()."""
    cp = ord(ch)
    if 0xE0000 <= cp <= 0xE007F or cp in EXTRA_HIDDEN:
        return True
    return ch not in WHITESPACE and unicodedata.category(ch) in ("Cf", "Cc")


def vs_ok(prev, vs):
    """True when the variation selector vs directly follows a character it can apply to."""
    if not prev:
        return False
    cp = ord(prev)
    within = lambda ranges: any(a <= cp <= b for a, b in ranges)
    if ord(vs) >= 0xE0100:  # ideographic variation selectors
        return within(CJK)
    return unicodedata.category(prev) in ("So", "Sm", "Sk") or cp in VS_BASES or within(CJK) or within(VS_SCRIPTS)


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
HIDDEN_RUN = re.compile(HIDDEN.pattern + "+")


def describe(ch):
    cp = ord(ch)
    kind = "bidi control" if ch in BIDI else "tag character" if 0xE0000 <= cp <= 0xE007F else \
        "variation selector" if VS_RX.match(ch) else "blank character" if cp in EXTRA_HIDDEN else \
        "control character" if unicodedata.category(ch) == "Cc" else "format character"
    name = unicodedata.name(ch, "")
    return f"U+{cp:04X} ({kind}{', ' + name if name else ''})"


def escape(ch):
    """The Python escape for one character (in JSON, one above U+FFFF is a surrogate pair of \\u escapes)."""
    return f"\\u{ord(ch):04x}" if ord(ch) <= 0xFFFF else f"\\U{ord(ch):08x}"


def show(path):
    """A path safe to print: ascii() when it holds anything hidden or non-printable."""
    return path if path.isprintable() and not HIDDEN.search(path) else ascii(path)


def glob_rx(pattern):
    """Gitignore-style glob to regex: * and ? stay within one path segment, a ** segment spans zero or more
    directories, [abc] and [!abc] match one character other than /. Raises ConfigError for what it does not
    support: ** inside a segment, a POSIX class, / or [ inside a class, an invalid range."""
    if not isinstance(pattern, str) or not pattern:
        raise ConfigError(f"a glob must be a non-empty string: {pattern!r}")
    out, i, n = [], 0, len(pattern)
    while i < n:
        c = pattern[i]
        if pattern.startswith("**", i):
            if (i and pattern[i - 1] != "/") or (i + 2 < n and pattern[i + 2] != "/"):
                raise ConfigError(f"glob {pattern!r}: ** must be a whole path segment (a/**/b, **/x, a/**)")
            if i + 2 < n:
                out.append("(?:.*/)?")
                i += 3
            else:
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
            neg = body[:1] in ("!", "^")
            body = body[1:] if neg else body
            if "[" in body or "/" in body:
                raise ConfigError(f"glob {pattern!r}: a class cannot hold [, / or a POSIX class like [:alpha:]")
            out.append(("[^/" if neg else "[") + body.replace("\\", "\\\\") + "]")
            i = j + 1
        else:
            out.append(re.escape(c))
            i += 1
    try:
        return re.compile("".join(out))
    except re.error as e:
        raise ConfigError(f"glob {pattern!r} is not valid: {e}")


def matcher(patterns):
    rxs = [glob_rx(p) for p in patterns]
    return lambda path: any(rx.fullmatch(path) for rx in rxs)


def read_bytes(full):
    """A regular file's bytes, or None for a symlink or a missing file."""
    if os.path.islink(full) or not os.path.isfile(full):
        return None
    with open(full, "rb") as f:
        return f.read()


def decode(data):
    """(text, valid): undecodable bytes are kept as surrogate escapes, so the rest can still be scanned."""
    try:
        return data.decode("utf-8"), True
    except UnicodeDecodeError:
        return data.decode("utf-8", "surrogateescape"), False


def binary_by_attr(root, files):
    """Paths .gitattributes marks as not text: -text, or the binary macro."""
    if not files:
        return set()
    r = subprocess.run(["git", "-C", root, "check-attr", "-z", "--stdin", "text", "binary"],
                       input=("\0".join(files) + "\0").encode(), capture_output=True, check=True)
    parts = r.stdout.decode("utf-8", "surrogateescape").split("\0")
    out = set()
    for k in range(0, len(parts) - 2, 3):
        path, attr, value = parts[k:k + 3]
        if (attr, value) in (("text", "unset"), ("binary", "set")):
            out.add(path)
    return out


def is_binary(data):
    """git's own test: a NUL byte in the first 8000 bytes."""
    return b"\0" in data[:8000]


# ---------------------------------------------------------------- config

def _globs(cfg, key, catch_all_ok=True):
    v = cfg[key]
    if not isinstance(v, list):
        raise ConfigError(f"{key} must be a list")
    out = []
    for item in v:
        if isinstance(item, str):
            g = item
        elif isinstance(item, dict) and isinstance(item.get("glob"), str) and isinstance(item.get("why"), str) \
                and set(k for k in item if not k.startswith("_")) <= {"glob", "why"}:
            g = item["glob"]
        else:
            raise ConfigError(f"{key} entries are a glob string or {{\"glob\": ..., \"why\": ...}}: {item!r}")
        glob_rx(g)
        if not catch_all_ok and set(g) <= set("*/"):
            raise ConfigError(f"{key}: {g!r} matches every file; list the paths that need it")
        out.append(g)
    return out


def _known(obj, keys, where):
    extra = sorted(k for k in obj if k not in keys and not k.startswith("_"))
    if extra:
        raise ConfigError(f"{where}: unknown key(s) {', '.join(extra)}")


def _regex(pattern, where, groups=0):
    if not isinstance(pattern, str):
        raise ConfigError(f"{where}: the pattern must be a string")
    try:
        rx = re.compile(pattern)
    except re.error as e:
        raise ConfigError(f"{where}: {pattern!r} is not a regex: {e}")
    if rx.groups < groups:
        raise ConfigError(f"{where}: {pattern!r} needs a group that captures the number")
    return rx


def _spec(c, key, required, optional=()):
    spec = c[key]
    where = f"claim {c['file']!r} {key}"
    if not isinstance(spec, dict):
        raise ConfigError(f"{where} must be an object with {', '.join(required)}")
    _known(spec, set(required) | set(optional), where)
    missing = [k for k in required if k not in spec]
    if missing:
        raise ConfigError(f"{where} is missing {', '.join(missing)}")
    for k, v in spec.items():
        if not k.startswith("_") and not isinstance(v, str):
            raise ConfigError(f"{where}: {k} must be a string")


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
    cfg["invisible_allow"] = _globs(cfg, "invisible_allow", catch_all_ok=False)
    cfg["stale_globs"] = _globs(cfg, "stale_globs")
    cfg["stale_exclude"] = _globs(cfg, "stale_exclude", catch_all_ok=False)
    if not isinstance(cfg["stale_pattern"], str):
        raise ConfigError("stale_pattern must be a string")
    try:
        rx = re.compile(cfg["stale_pattern"], re.IGNORECASE)
    except re.error as e:
        raise ConfigError(f"stale_pattern is not a regex: {e}")
    if rx.groups < 1:
        raise ConfigError("stale_pattern needs a group that captures the YYYY-MM-DD date")
    for key in ("claims", "instructions", "root_safety"):
        if not isinstance(cfg[key], list):
            raise ConfigError(f"{key} must be a list")
    for c in cfg["claims"]:
        if not isinstance(c, dict):
            raise ConfigError(f"claims entries are objects: {c!r}")
        _known(c, CLAIM_KEYS, f"claim {c.get('file')!r}")
        counts = [k for k in ("count_glob", "count_json", "count_lines") if k in c]
        if not isinstance(c.get("file"), str) or not isinstance(c.get("pattern"), str) or len(counts) != 1:
            raise ConfigError(f"a claim needs file, pattern and exactly one of count_glob, count_json, count_lines: {c!r}")
        _regex(c["pattern"], f"claim {c['file']!r} pattern", groups=1)
        if "count_glob" in c:
            glob_rx(c["count_glob"])
        elif "count_json" in c:
            _spec(c, "count_json", ["file"], ["key"])
        else:
            _spec(c, "count_lines", ["file", "pattern"])
            _regex(c["count_lines"]["pattern"], f"claim {c['file']!r} count_lines")
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
    if not all(isinstance(x, str) and x.strip() and "\n" not in x for x in cfg["root_safety"]):
        raise ConfigError("root_safety must be a list of one-line shell commands")
    return cfg


def loosened(old, new):
    """What new turns off or widens compared with old (both valid configs): notices, not failures."""
    old, new = load_config(old), load_config(new)
    out = []
    for key in ("modes", "invisible", "stale", "stale_fails"):
        if old[key] and not new[key]:
            out.append(f"turns {key} off")
    if new["max_age_days"] > old["max_age_days"]:
        out.append(f"raises max_age_days from {old['max_age_days']} to {new['max_age_days']}")
    for key in ("invisible_allow", "stale_exclude"):
        for g in new[key]:
            if g not in old[key]:
                out.append(f"adds {g!r} to {key}")
    for g in old["stale_globs"]:
        if g not in new["stale_globs"]:
            out.append(f"drops {g!r} from stale_globs")
    if new["stale_pattern"] != old["stale_pattern"]:
        out.append("changes stale_pattern")
    dump = lambda c: json.dumps({k: v for k, v in c.items() if not k.startswith("_")}, sort_keys=True)
    new_claims = {dump(c) for c in new["claims"]}
    for c in old["claims"]:
        if dump(c) not in new_claims:
            out.append(f"drops or changes a claim on {c['file']}")
    new_ins = {i["file"]: i for i in new["instructions"]}
    for i in old["instructions"]:
        n = new_ins.get(i["file"])
        if n is None:
            out.append(f"drops the instructions check on {i['file']}")
            continue
        if n.get("max_bytes", 32768) > i.get("max_bytes", 32768):
            out.append(f"raises max_bytes for {i['file']}")
        if i.get("sentinel") and n.get("sentinel") != i.get("sentinel"):
            out.append(f"drops or changes the sentinel for {i['file']}")
    for cmd in old["root_safety"]:
        if cmd not in new["root_safety"]:
            out.append(f"drops the root_safety command {cmd!r}")
    return out


def config_notices(root, rel, cfg, base):
    """Notices for a config that loosens the checks compared with the one at the merge base."""
    try:
        mb = git(root, "merge-base", base, "HEAD").strip()
    except subprocess.CalledProcessError:
        return []
    try:
        old = json.loads(git(root, "show", f"{mb}:{rel}"))
    except subprocess.CalledProcessError:
        return [f"config: {rel} is new in this change; review its allow-lists and exclusions"]
    except ValueError:
        return [f"config: {rel} at the base {mb[:12]} is not valid JSON; not compared"]
    try:
        return [f"config: this change to {rel} {x}; review it" for x in loosened(old, cfg)]
    except ConfigError:
        return [f"config: {rel} at the base {mb[:12]} is not a valid config; not compared"]


# ---------------------------------------------------------------- checks

def check_modes(root, base, out):
    if not base:
        return
    try:
        raw = git(root, "diff", "--raw", "-z", "-M", "--no-abbrev", f"{base}...HEAD")
    except subprocess.CalledProcessError as e:
        out["fail"].append(f"modes: cannot diff against {base}: {(e.stderr.strip().splitlines() or [''])[0]}")
        return
    parts = raw.split("\0")
    deleted, added = [], []  # 100755 files deleted, shebang files added as 100644: a rename git did not pair
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
        if status == "D" and src_mode == "100755":
            deleted.append(path)
            continue
        if dst_mode != "100644" or (src_mode != "100755" and status != "A"):
            continue
        if git(root, "cat-file", "blob", dst_sha, text=False)[:2] != b"#!":
            continue
        if status == "A":
            added.append(path)
        else:
            out["fail"].append(f"modes: {show(path)} lost its executable bit (100755 -> 100644); "
                               f"restore with: git update-index --chmod=+x {show(path)}")
    for path in added:
        for gone in deleted:
            if os.path.dirname(gone) == os.path.dirname(path) or os.path.basename(gone) == os.path.basename(path):
                out["fail"].append(f"modes: {show(path)} has a shebang and mode 100644, and {show(gone)} (100755) "
                                   f"was deleted in the same change: a rename that lost its executable bit? "
                                   f"restore with: git update-index --chmod=+x {show(path)}")
                break


def check_invisible(root, files, cfg, out):
    allowed = matcher(cfg["invisible_allow"])
    by_attr = binary_by_attr(root, files)
    for path in files:
        m = HIDDEN.search(path)
        if m:  # checked even when the file is allow-listed
            out["fail"].append(f"invisible: the path {show(path)} holds raw {describe(m.group())}; rename it")
        if allowed(path):
            continue
        full = os.path.join(root, path)
        if os.path.islink(full):
            m = HIDDEN.search(os.readlink(full))
            if m:
                out["fail"].append(f"invisible: the symlink {show(path)} points at a target holding raw {describe(m.group())}")
            continue
        data = read_bytes(full)
        if data is None or path in by_attr or is_binary(data):
            continue
        text, valid = decode(data)
        if not valid:
            out["fail"].append(f"invisible: {show(path)} is not valid UTF-8; convert it, or mark it binary in "
                               f".gitattributes if it is not text")
        for n, line in enumerate(text.split("\n"), 1):
            for m in HIDDEN_RUN.finditer(line):
                run_, col = m.group(), m.start()
                if n == 1 and col == 0 and run_[0] == BOM:
                    run_, col = run_[1:], 1
                    if not run_:
                        continue
                more = f" and {len(run_) - 1} more hidden character(s) after it" if len(run_) > 1 else ""
                out["fail"].append(f"invisible: {show(path)}:{n}:{col + 1} raw {describe(run_[0])}{more}; "
                                   f"write it as an escape ({escape(run_[0])} or an HTML entity)")
            for m in VS_RX.finditer(line):
                col = m.start()
                if not vs_ok(line[col - 1] if col else "", m.group()):
                    out["fail"].append(f"invisible: {show(path)}:{n}:{col + 1} raw {describe(m.group())} not after a "
                                       f"character it can modify; write it as an escape ({escape(m.group())})")


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


NUMBER = re.compile(r"\d{1,3}(?:,\d{3})+|\d+")


def check_claims(root, files, cfg, out):
    for claim in cfg["claims"]:
        where = f"claims: {claim['file']}"
        try:
            with open(os.path.join(root, claim["file"]), encoding="utf-8") as f:
                text = f.read()
            actual = count_for(root, files, claim)
        except (OSError, ValueError, KeyError, TypeError, IndexError, re.error) as e:
            out["fail"].append(f"{where}: cannot check {claim['pattern']!r}: {type(e).__name__}: {e}")
            continue
        found = [m.group(1) for m in re.finditer(claim["pattern"], text)]
        if not found:
            out["fail"].append(f"{where}: pattern {claim['pattern']!r} not found")
            continue
        for stated in found:
            if stated is None or not NUMBER.fullmatch(stated):
                out["fail"].append(f"{where}: pattern {claim['pattern']!r} matched, but its group 1 captured "
                                   f"{stated!r}, not a number; fix the pattern")
            elif int(stated.replace(",", "")) != actual:
                out["fail"].append(f"{where} states {stated} for {claim['pattern']!r}; the repo has {actual}")


FENCE = re.compile(r" {0,3}(`{3,}|~{3,})")


def check_stale(root, files, cfg, out, today):
    rx = re.compile(cfg["stale_pattern"], re.IGNORECASE)
    wanted, excluded = matcher(cfg["stale_globs"]), matcher(cfg["stale_exclude"])
    limit = cfg["max_age_days"]
    bucket = "fail" if cfg["stale_fails"] else "warn"
    for path in files:
        if not wanted(path) or excluded(path):
            continue
        data = read_bytes(os.path.join(root, path))
        if data is None or is_binary(data):
            continue
        text = decode(data)[0]
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
            text = decode(read_bytes(path))[0]
            if text.startswith(BOM):
                text = text[1:]
            lines = [l for l in text.split("\n") if l.strip()]
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
        put("x.py", "s = 'admin\u202e'  # bidi\nt = '1\u200b2'\nu = '\x1b[31m'\nv = 'tag\U000e0041\U000e0042\U000e0043'\n"
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
        expect("tag-block character is caught, with a long escape", fails(r, "x.py:4:", "U+E0041", "tag", "\\U000e0041"))
        expect("a run of hidden characters is one message", fails(r, "x.py:4:", "and 2 more hidden character(s)")
               and sum(x.startswith("invisible: x.py:4:") for x in r["fail"]) == 1)
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
        expect("globs: [!a] never matches /", not glob_rx("[!a]").fullmatch("/"))
        expect("globs: a/**/b matches a/b and a/x/y/b", glob_rx("a/**/b").fullmatch("a/b")
               and glob_rx("a/**/b").fullmatch("a/x/y/b") and not glob_rx("a/**/b").fullmatch("ab"))
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
        r = run(repo, {**cfg, "claims": [{"file": "README.md", "pattern": r"(\d+) widgets", "count_glob": "*"}]},
                None, today)
        expect("a claim whose pattern is not found fails", fails(r, "pattern '(\\\\d+) widgets' not found"))
        r = run(repo, {**cfg, "claims": [{"file": "README.md", "pattern": r"(\d+)?checked", "count_glob": "*"}]},
                None, today)
        expect("a claim group that did not take part fails cleanly", fails(r, "captured None, not a number"))
        r = run(repo, {**cfg, "claims": [{"file": "README.md", "pattern": r"(\w+) 3 skills", "count_glob": "*"}]},
                None, today)
        expect("a claim group that captured a word fails cleanly", fails(r, "captured 'Now', not a number"))

        # second round: binary detection, the wider invisible set, variation selectors, symlinks, renames
        sh("mv", "run.sh", "gone.sh")
        sh("commit", "-qm", "rename")
        put("tools/big.sh", "#!/bin/sh\n" + "".join(f"echo line {k}\n" for k in range(60)), 0o755)
        sh("add", "-A")
        sh("commit", "-qm", "big")
        sh("rm", "-q", "tools/big.sh")
        put("tools/big3.sh", "#!/bin/sh\necho rewritten\n")
        with open(os.path.join(repo, "late-nul.sh"), "wb") as f:
            f.write(b"#!/bin/sh\necho \"\xe2\x80\xae\"\n" + b"#" * 9000 + b"\0\n")
        with open(os.path.join(repo, "early-nul.bin"), "wb") as f:
            f.write(b"\0\xe2\x80\xae binary\n")
        with open(os.path.join(repo, "latin.md"), "wb") as f:
            f.write(b"caf\xe9 \x1b[2J\n")
        put(".gitattributes", "*.dat binary\nraw.txt -text\n")
        put("marked.dat", "x\U0000202ey\n")
        put("raw.txt", "x\U0000202ey\n")
        put("y.txt", "a\U00003164b\nc\U00002800d\ne\U0000034ff\ng\x1ch\ni\x85j\nform\x0cfeed\x0bvtab\n"
                     "heart \U00002764\U0000FE0F keycap 1\U0000FE0F\U000020E3 flag \U0001F3F3\U0000FE0F ideograph "
                     "\U00004E00\U000E0100\n"
                     "bare a\U0000FE0F and a\U000E0100 and twice \U00002764\U0000FE0F\U0000FE0F\n")
        os.symlink("tgt\U0000200b", os.path.join(repo, "fixtures", "link"))
        put("fixtures/odd\U00002066name.txt", "x\n")
        put("ONE.md", BOM + "Sentinel: end\n")
        sh("add", "-A")
        sh("commit", "-qm", "round2")
        r = run(repo, {**cfg, "instructions": [{"file": "ONE.md", "sentinel": "Sentinel: end"}]}, "HEAD~1", today)
        expect("a deleted 100755 script and an added 100644 one beside it are a lost bit (rename plus rewrite)",
               fails(r, "tools/big3.sh has a shebang and mode 100644", "tools/big.sh (100755) was deleted"))
        r2 = run(repo, cfg, "HEAD~2", today)
        expect("a plain rename that keeps the bit is not flagged", not fails(r2, "gone.sh"))
        expect("a NUL after the first 8000 bytes is text and is scanned", fails(r, "late-nul.sh:2:", "U+202E"))
        expect("a NUL in the first 8000 bytes is binary and skipped", not fails(r, "early-nul.bin"))
        expect("a file that is not UTF-8 fails", fails(r, "latin.md is not valid UTF-8"))
        expect("a file that is not UTF-8 is still scanned", fails(r, "latin.md:1:", "U+001B"))
        expect("the binary attribute and -text skip a file", not fails(r, "marked.dat") and not fails(r, "raw.txt"))
        for line, cp in ((1, "U+3164"), (2, "U+2800"), (3, "U+034F"), (4, "U+001C"), (5, "U+0085")):
            expect(f"{cp} is caught", fails(r, f"y.txt:{line}:", cp))
        expect("form feed and vertical tab are whitespace", not fails(r, "y.txt:6:"))
        expect("variation selectors after an emoji, a keycap base or an ideograph pass", not fails(r, "y.txt:7:"))
        expect("a variation selector after a letter is caught", fails(r, "y.txt:8:7 ", "U+FE0F"))
        expect("an ideographic variation selector after a letter is caught", fails(r, "y.txt:8:14 ", "U+E0100"))
        expect("a second variation selector in a row is caught", fails(r, "y.txt:8:", "U+FE0F")
               and sum(x.startswith("invisible: y.txt:8:") for x in r["fail"]) == 3)
        expect("an allow-listed symlink is skipped",
               not fails(r, "fixtures/link"))
        r3 = run(repo, {**cfg, "invisible_allow": []}, "HEAD~1", today)
        expect("a symlink whose target holds a hidden character is caught", fails(r3, "the symlink fixtures/link"))
        expect("a path name is checked even when the file is allow-listed", fails(r, "the path 'fixtures/odd\\u2066name.txt'"))
        expect("a BOM before a one-line sentinel file is allowed", not fails(r, "ONE.md"))

        expect("loosening: identical configs give no notices", loosened(cfg, cfg) == [])
        notes = loosened(cfg, {**cfg, "invisible": False, "invisible_allow": ["fixtures/**", "src/x.py"],
                               "instructions": [], "max_age_days": 90})
        expect("loosening: turning a check off, widening an allow-list, dropping instructions, a longer age",
               any("turns invisible off" in x for x in notes) and any("'src/x.py'" in x for x in notes)
               and any("drops the instructions check on AGENTS.md" in x for x in notes)
               and any("max_age_days from 45 to 90" in x for x in notes))
        expect("loosening: tightening gives no notices", loosened(cfg, {**cfg, "stale_fails": True}) == [])
        r = run(repo, cfg, "no-such-ref", today)
        expect("an unknown --base fails", fails(r, "cannot diff against no-such-ref"))
        for bad, why in (({"stale_globz": []}, "unknown key"), ({"stale_pattern": "no group"}, "needs a group"),
                         ({"invisible_allow": [{"glob": "x"}]}, "glob"), ({"root_safety": ["a\nb"]}, "one-line"),
                         ({"claims": [{"file": "a", "pattern": "(1)"}]}, "exactly one"),
                         ({"max_age_days": "45"}, "whole number"),
                         ({"claims": [{"file": "a", "pattern": "(1)", "count_glob": "*", "typo": 1}]}, "unknown key(s) typo"),
                         ({"claims": [{"file": "a", "pattern": "(1)", "count_json": {"file": "d", "kye": "a"}}]},
                          "unknown key(s) kye"),
                         ({"claims": [{"file": "a", "pattern": "(1)", "count_json": "d.json"}]}, "must be an object"),
                         ({"claims": [{"file": "a", "pattern": "(1)", "count_json": {"file": 3}}]}, "must be a string"),
                         ({"claims": [{"file": "a", "pattern": "(1)", "count_lines": {"file": "d", "patern": "x"}}]},
                          "unknown key(s) patern"),
                         ({"claims": [{"file": "a", "pattern": "(1)", "count_lines": {"file": "d", "pattern": "("}}]},
                          "is not a regex"),
                         ({"invisible_allow": ["[z-a]"]}, "is not valid"), ({"stale_globs": ["[[:alpha:]]"]}, "POSIX"),
                         ({"stale_globs": ["docs**.md"]}, "whole path segment"),
                         ({"invisible_allow": ["**"]}, "matches every file"),
                         ({"invisible_allow": ["**/*"]}, "matches every file"),
                         ({"stale_exclude": ["*"]}, "matches every file"),
                         ({"claims": {"file": "a"}}, "claims must be a list"),
                         ({"instructions": ["AGENTS.md"]}, "objects with a file"),
                         ({"stale_pattern": 5}, "must be a string")):
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
    return f"{ {'error': 'FAIL', 'warning': 'WARN'}.get(level, 'NOTE')}  {msg}"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--config", help="config path relative to --root (default .hygiene.json, optional)")
    ap.add_argument("--base", help="git ref to compare modes and the config against (a PR's base commit)")
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
        notices = config_notices(a.root, a.config or ".hygiene.json", cfg, a.base) if a.base else []
    except (ConfigError, ValueError) as e:
        print(annotate("error", f"config {cfg_path}: {e}"))
        return 2
    for x in notices:
        print(annotate("notice", x))
    for w in r["warn"]:
        print(annotate("warning", w))
    for x in r["fail"]:
        print(annotate("error", x))
    print(f"{len(r['fail'])} failure(s), {len(r['warn'])} warning(s)")
    return 1 if r["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
