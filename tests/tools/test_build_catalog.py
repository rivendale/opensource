#!/usr/bin/env python3
"""License classes for SPDX expressions, and repository descriptions made inert in the catalog's markdown.

    python3 tests/tools/test_build_catalog.py
"""
import datetime, importlib.util, os, pathlib, tempfile, unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("build_catalog", ROOT / "tools/build_catalog.py")
bc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bc)

LICENSES = [
    # single ids and no license
    ("MIT", "copy"), ("LGPL-2.1-only", "library"), ("GPL-3.0", "study"), ("BUSL-1.1", "check"),
    (None, "check"), ("", "check"), ("NOASSERTION", "check"), ("OTHER", "check"),
    # OR: the reuser may choose, so the most permissive operand
    ("MIT OR GPL-3.0-only", "copy"), ("GPL-3.0-only OR MIT", "copy"), ("LGPL-2.1-only OR GPL-2.0-only", "library"),
    ("GPL-2.0-only OR GPL-3.0-only", "study"), ("BUSL-1.1 OR GPL-3.0", "study"), ("Apache-2.0 OR MIT", "copy"),
    # AND: every part applies, so the most restrictive operand
    ("Apache-2.0 AND MIT", "copy"), ("MIT AND BUSL-1.1", "check"), ("MIT AND GPL-3.0", "study"),
    ("GPL-3.0 AND MIT", "study"), ("LGPL-2.1 AND MIT", "library"), ("MPL-2.0 AND BUSL-1.1", "check"),
    # WITH: the base license's class
    ("GPL-2.0-only WITH Classpath-exception-2.0", "study"), ("Apache-2.0 WITH LLVM-exception", "copy"),
    ("GPL-3.0 WITH additional terms", "study"), ("LGPL-3.0-only WITH LGPL-3.0-linking-exception", "library"),
    # AND binds tighter than OR, WITH tighter than both
    ("MIT AND Apache-2.0 OR GPL-3.0", "copy"), ("GPL-3.0 AND MIT OR BUSL-1.1", "study"),
    ("GPL-2.0-only WITH Classpath-exception-2.0 OR MIT", "copy"), ("MIT AND GPL-2.0-only WITH Classpath-exception-2.0", "study"),
    # not parsed: lower-case operators, dangling operators, parentheses
    ("Apache-2.0 and MIT", "check"), ("MIT or GPL-3.0", "check"), ("MIT OR ", "check"), (" AND MIT", "check"),
    ("MIT WITH ", "check"), ("(MIT OR Apache-2.0)", "check"), ("(MIT AND Apache-2.0)", "check"),
]


class LicenseClass(unittest.TestCase):
    def test_table(self):
        for spdx, want in LICENSES:
            with self.subTest(spdx=spdx):
                self.assertEqual(bc.license_class(spdx), want)


DESCRIPTIONS = [
    ("", ""),
    ("a game", "a game"),
    ("one\ntwo\r\nthree\rfour", "one two three four"),
    ("x | y", "x \\| y"),
    ("run `rm -rf`", "run \\`rm -rf\\`"),
    ("<script>alert(1)</script>", "&lt;script&gt;alert(1)&lt;/script&gt;"),
    ("<https://evil.example>", "&lt;https://evil.example&gt;"),
    ("[click](https://evil.example)", "\\[click\\](https://evil.example)"),
    ("![x](https://evil.example/x.png)", "!\\[x\\](https://evil.example/x.png)"),
    ("a\\[b", "a\\\\\\[b"),
    ("fast \N{EM DASH} small", "fast - small"),
]


class Description(unittest.TestCase):
    def test_table(self):
        self.assertEqual(bc.esc_desc(None), "")
        for text, want in DESCRIPTIONS:
            with self.subTest(text=text):
                self.assertEqual(bc.esc_desc(text), want)

    def test_cut_before_escaping(self):
        self.assertEqual(bc.esc_desc("<" * 200, 120), "&lt;" * 120)
        self.assertEqual(bc.esc_desc("a" * 119 + "|tail", 120), "a" * 119 + "\\|")
        self.assertEqual(bc.esc_desc("a" * 200, 120), "a" * 120)

    def test_catalog_page_cell(self):
        row = {"name": "g", "genre": "puzzle", "repo": "https://github.com/o/g", "license": "MIT", "license_from": "github",
               "reuse": "copy", "language": "C", "stars": 1, "pushed": "2026-09-01", "archived": False, "active": True,
               "note": None, "description": "ok\n| x | y |\n<img src=x onerror=alert(1)> [a](javascript:alert(1)) `c`"}
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "catalog"))
            bc.write_markdown([row], tmp, datetime.date(2026, 10, 1), {})
            page = open(os.path.join(tmp, "catalog", "puzzle.md"), encoding="utf-8").read()
        line = next(x for x in page.splitlines() if x.startswith("| [g]("))
        self.assertEqual(len(page.splitlines()), 7, page)
        self.assertNotIn("<", line)
        self.assertNotIn("[a](", line)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt; \\[a\\](javascript:alert(1)) \\`c\\`", line)
        self.assertEqual(line.replace("\\|", "").count("|"), 8, line)


if __name__ == "__main__":
    unittest.main()
