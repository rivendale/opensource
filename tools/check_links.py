#!/usr/bin/env python3
"""Check local Markdown links and heading anchors in this repository."""

import argparse
from bisect import bisect_right
import html
import os
from pathlib import Path
import re
import tempfile
import unicodedata
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parent.parent
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
ATX_HEADING = re.compile(r"^ {0,3}#{1,6}(?:[ \t]+|$)(.*)$")
SETEXT_HEADING = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
LIST_ITEM = re.compile(r"^ {0,3}(?:[-+*]|\d+[.)])[ \t]+")
DEFINITION = re.compile(r"^ {0,3}\[([^]]+)\]:[ \t]*(.*)$")
HTML_ANCHOR = re.compile(r"<a\s+[^>]*?\b(?:id|name)\s*=\s*([\"'])(.*?)\1[^>]*>", re.I)
ESCAPE = re.compile(r"\\([!\"#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~])")


def markdown_files(root):
    for directory, subdirs, files in os.walk(root):
        subdirs[:] = sorted(name for name in subdirs if name != ".git")
        for name in sorted(files):
            if name.endswith(".md"):
                yield Path(directory) / name


def visible_lines(path):
    """Retain source line numbers while removing block code and container prefixes."""
    marker = ""
    length = 0
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw
        while True:
            quote = re.match(r"^ {0,3}>[ \t]?", line)
            if not quote:
                break
            line = line[quote.end():]
        item = LIST_ITEM.match(line)
        list_start = bool(item)
        if item:
            line = line[item.end():]
        fence = FENCE.match(line)
        if marker:
            if fence and fence.group(1)[0] == marker and len(fence.group(1)) >= length:
                if not fence.group(2).strip():
                    marker = ""
            continue
        if fence:
            marker = fence.group(1)[0]
            length = len(fence.group(1))
            continue
        if line.startswith("    ") or line.startswith("\t"):
            continue
        yield number, line, list_start


def mask_code(text):
    def blank(match):
        return re.sub(r"[^\n]", " ", match.group())
    return re.sub(r"(`+)(.*?)\1", blank, text, flags=re.S)


def unescape(value):
    return ESCAPE.sub(r"\1", html.unescape(value))


def destination(text, start, inline):
    """Return a Markdown destination and the position after it, if complete."""
    position = start
    while position < len(text) and text[position].isspace():
        position += 1
    if position >= len(text):
        return None
    if text[position] == "<":
        end = position + 1
        while end < len(text):
            if text[end] == "\\" and end + 1 < len(text):
                end += 2
            elif text[end] == ">":
                break
            else:
                end += 1
        if end == len(text):
            return None
        target = text[position + 1:end]
        position = end + 1
    else:
        begin = position
        depth = 0
        while position < len(text):
            char = text[position]
            if char == "\\" and position + 1 < len(text):
                position += 2
                continue
            if char == "(":
                depth += 1
            elif char == ")":
                if depth == 0:
                    break
                depth -= 1
            elif char.isspace() and depth == 0:
                break
            position += 1
        target = text[begin:position]
        if depth:
            return None
    if not target:
        return None
    if not inline:
        return unescape(target), position
    spaced = position < len(text) and text[position].isspace()
    while position < len(text) and text[position].isspace():
        position += 1
    if spaced and position < len(text) and text[position] in "\"'":
        quote = text[position]
        position += 1
        while position < len(text) and text[position] != quote:
            if text[position] == "\\":
                position += 1
            position += 1
        if position >= len(text):
            return None
        position += 1
        while position < len(text) and text[position].isspace():
            position += 1
    if position >= len(text) or text[position] != ")":
        return None
    return unescape(target), position + 1


def closing_bracket(text, start):
    depth = 1
    position = start + 1
    while position < len(text):
        if text[position] == "\\":
            position += 2
            continue
        if text[position] == "[":
            depth += 1
        elif text[position] == "]":
            depth -= 1
            if depth == 0:
                return position
        position += 1
    return None


def links(lines):
    """Yield source line and target for inline, image, and reference links."""
    definitions = {}
    ignored = set()
    for index, (_, line, _) in enumerate(lines):
        match = DEFINITION.match(mask_code(line))
        if match:
            parsed = destination(line, match.start(2), False)
            if parsed:
                definitions.setdefault(unescape(match.group(1)).casefold(), parsed[0])
                ignored.add(index)
    text = "\n".join("" if index in ignored else line for index, (_, line, _) in enumerate(lines))
    masked = mask_code(text)
    starts = [0]
    starts.extend(match.end() for match in re.finditer("\n", text))
    reference_labels = set()
    for position, char in enumerate(masked):
        if char != "[" or position in reference_labels or (position and masked[position - 1] == "\\"):
            continue
        end = closing_bracket(masked, position)
        if end is None:
            continue
        label = unescape(text[position + 1:end])
        after = end + 1
        target = None
        if after < len(masked) and masked[after] == "(":
            parsed = destination(text, after + 1, True)
            if parsed:
                target = parsed[0]
        elif after < len(masked) and masked[after] == "[":
            reference_end = closing_bracket(masked, after)
            if reference_end is not None:
                reference_labels.add(after)
                reference = unescape(text[after + 1:reference_end]) or label
                target = definitions.get(reference.casefold())
        else:
            target = definitions.get(label.casefold())
        if target is not None:
            yield lines[bisect_right(starts, position) - 1][0], target


def heading_text(value):
    value = re.sub(r"[ \t]+#+[ \t]*$", "", value).strip()
    code = []
    def save_code(match):
        code.append(match.group(2))
        return f"\x00{len(code) - 1}\x00"
    value = re.sub(r"(`+)(.*?)\1", save_code, value)
    value = re.sub(r"!?\[([^]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\x00(\d+)\x00", lambda match: code[int(match.group(1))], value)
    value = re.sub(r"(?<!\w)[*_]+|[*_]+(?!\w)", "", value)
    return html.unescape(value).replace("~", "")


def slug(value):
    value = heading_text(value).lower()
    return "".join(
        "-" if char == " " else char
        for char in value
        if char in "-_ " or unicodedata.category(char)[0] in "LMN"
    )


def anchors(path):
    found = set()
    lines = list(visible_lines(path))
    for index, (_, line, _) in enumerate(lines):
        for match in HTML_ANCHOR.finditer(mask_code(line)):
            found.add(html.unescape(match.group(2)))
        heading = ATX_HEADING.match(line)
        if heading:
            title = heading.group(1)
        elif SETEXT_HEADING.match(line) and index:
            parts = []
            previous = index - 1
            while previous >= 0:
                number, candidate, list_start = lines[previous]
                if (number != lines[previous + 1][0] - 1 or not candidate.strip()
                        or list_start or ATX_HEADING.match(candidate)
                        or SETEXT_HEADING.match(candidate)):
                    break
                parts.append(candidate.strip())
                previous -= 1
            if not parts:
                continue
            title = "".join(reversed(parts))
        else:
            continue
        base = slug(title)
        unique = base
        suffix = 1
        while unique in found:
            unique = f"{base}-{suffix}"
            suffix += 1
        found.add(unique)
    return found


def check(root):
    problems = []
    checked = 0
    anchor_cache = {}
    for source in markdown_files(root):
        display = source.relative_to(root).as_posix()
        for number, target in links(list(visible_lines(source))):
            if SCHEME.match(target) or target.startswith("//"):
                continue
            checked += 1
            path_part, separator, fragment = target.partition("#")
            path_part = unquote(path_part.split("?", 1)[0])
            if path_part.startswith("/"):
                resolved = root / path_part.lstrip("/")
            else:
                resolved = source.parent / path_part if path_part else source
            if not resolved.exists():
                problems.append((display, number, "missing file", target))
            elif separator and fragment and (not path_part or resolved.suffix.lower() == ".md"):
                if resolved not in anchor_cache:
                    anchor_cache[resolved] = anchors(resolved)
                if unquote(fragment) not in anchor_cache[resolved]:
                    problems.append((display, number, "missing anchor", target))
    return problems, checked


def selftest():
    cases = [
        ("image", "![i](missing.png)", {}, [("missing file", "missing.png")]),
        ("nested image and link", "[![i](ok.png)](missing.md)", {"ok.png": ""}, [("missing file", "missing.md")]),
        ("full reference", "[guide][g]\n\n[g]: ./no-such.md", {}, [("missing file", "./no-such.md")]),
        ("collapsed reference", "[no-such.md][]\n\n[no-such.md]: no-such.md", {}, [("missing file", "no-such.md")]),
        ("shortcut reference", "[no-such.md]\n\n[no-such.md]: no-such.md", {}, [("missing file", "no-such.md")]),
        ("split destination", "[a](\nno-such.md)", {}, [("missing file", "no-such.md")]),
        ("wrapped label", "See the [long\ntext](missing.md).", {}, [("missing file", "missing.md")]),
        ("root relative", "[a](/missing.md)", {}, [("missing file", "/missing.md")]),
        ("root relative exists", "[a](/ok.md)", {"ok.md": ""}, []),
        ("code span", "Write `[label](no-such.md)` here.", {}, []),
        ("indented code", "    [label](no-such.md)", {}, []),
        ("list fence", "- ```\n  [label](no-such.md)\n  ```", {}, []),
        ("quote fence", "> ```\n> [label](no-such.md)\n> ```", {}, []),
        ("trailing heading space", "## Foo \n[l](#foo)", {}, []),
        ("emoji heading", "## Ship it 🚀\n[l](#ship-it-)", {}, []),
        ("symbol heading", "## Step → next\n[l](#step--next)", {}, []),
        ("code in heading", "## `<div>` element\n[l](#div-element)", {}, []),
        ("emphasis heading", "## _hello_\n[l](#hello)", {}, []),
        ("HTML id", '<a id="top"></a>\n[l](#top)', {}, []),
        ("HTML name", '<a name="top"></a>\n[l](#top)', {}, []),
        ("quote heading", "> # Foo\n[l](#foo)", {}, []),
        ("list heading", "- # Foo\n[l](#foo)", {}, []),
        ("wrapped setext", "Foo\nBar\n---\n[l](#foobar)", {}, []),
        ("indented setext", "   Foo\n---\n[l](#foo)", {}, []),
        ("list then rule", "- Foo\n---\n[a](#--foo)", {}, [("missing anchor", "#--foo")]),
        ("escaped underscore", r"[x](a\_b.md)", {"a_b.md": ""}, []),
        ("duplicate headings", "# Foo\n# Foo\n# Foo\n[x](#foo-1) [y](#foo-2)", {}, []),
        ("title", '[x](ok.md "title")', {"ok.md": ""}, []),
        ("angle target", "[x](<path with spaces.md>)", {"path with spaces.md": ""}, []),
        ("percent encoded", "[x](a%20b.md)", {"a b.md": ""}, []),
        ("column zero fence", "```\n[x](no-such.md)\n```", {}, []),
        ("scheme URL", "[x](https://example.invalid/no-such.md)", {}, []),
        ("broken anchor", "[x](#no-such)", {}, [("missing anchor", "#no-such")]),
    ]
    checked_overrides = {
        "nested image and link": 2,
        "code span": 0,
        "indented code": 0,
        "list fence": 0,
        "quote fence": 0,
        "duplicate headings": 2,
        "column zero fence": 0,
        "scheme URL": 0,
    }
    failures = []
    with tempfile.TemporaryDirectory() as temporary:
        for name, content, files, expected in cases:
            root = Path(temporary) / re.sub(r"[^a-z0-9]+", "-", name.lower())
            root.mkdir()
            (root / "README.md").write_text(content + "\n", encoding="utf-8")
            for filename, data in files.items():
                (root / filename).write_text(data, encoding="utf-8")
            problems, checked = check(root)
            actual = [(kind, target) for _, _, kind, target in problems]
            expected_checked = checked_overrides.get(name, 1)
            if actual != expected or checked != expected_checked:
                failures.append(
                    f"{name}: expected {expected} and {expected_checked} checked, "
                    f"got {actual} and {checked} checked"
                )
    for failure in failures:
        print(f"FAIL {failure}")
    print(f"Selftest: {len(cases) - len(failures)} of {len(cases)} cases passed.")
    return 1 if failures else 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="run temporary Markdown fixtures")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    problems, checked = check(ROOT)
    for display, number, kind, target in problems:
        print(f"{display}:{number}: {kind} {target}")
    print(f"Checked {checked} relative links; {len(problems)} problems.")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
