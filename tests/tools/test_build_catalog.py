#!/usr/bin/env python3
"""License classes for SPDX expressions, and repository descriptions made inert in the catalog's and the
scaffold lists' markdown.

    python3 tests/tools/test_build_catalog.py
"""
import datetime, importlib.util, os, pathlib, tempfile, unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("build_catalog", ROOT / "tools/build_catalog.py")
bc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bc)
spec = importlib.util.spec_from_file_location("find_scaffolds", ROOT / "tools/find_scaffolds.py")
fs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fs)

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
    # WITH an exception on the SPDX list: the base license's class
    ("GPL-2.0-only WITH Classpath-exception-2.0", "study"), ("Apache-2.0 WITH LLVM-exception", "copy"),
    ("LGPL-3.0-only WITH LGPL-3.0-linking-exception", "library"), ("GPL-3.0-or-later WITH GCC-exception-3.1", "study"),
    ("GPL-2.0-or-later WITH Autoconf-exception-2.0", "study"), ("GPL-3.0-or-later WITH Autoconf-exception-3.0", "study"),
    ("GPL-3.0-or-later WITH Bison-exception-2.2", "study"), ("GPL-2.0-only WITH Font-exception-2.0", "study"),
    ("GPL-2.0-only WITH OpenJDK-assembly-exception-1.0", "study"), ("GPL-2.0-only WITH Linux-syscall-note", "study"),
    ("MPL-2.0 WITH Classpath-exception-2.0", "library"), ("BUSL-1.1 WITH LLVM-exception", "check"),
    # WITH anything else: unknown terms, never the base license's class
    ("GPL-3.0 WITH additional terms", "check"), ("MIT WITH Commons-Clause", "check"),
    ("Apache-2.0 WITH Commons-Clause", "check"), ("Apache-2.0 WITH llvm-exception", "check"),
    ("Apache-2.0 WITH LLVM-exception-2.0", "check"), ("Apache-2.0 WITH MIT", "check"),
    ("Apache-2.0 WITH LLVM-exception WITH Commons-Clause", "check"), ("MIT WITH Nokia-Qt-exception-1.1", "check"),
    ("MIT AND Apache-2.0 WITH Commons-Clause", "check"), ("Apache-2.0 WITH Commons-Clause OR MIT", "copy"),
    ("Apache-2.0 WITH Commons-Clause OR GPL-3.0", "study"),
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
    # emphasis and strikethrough
    ("*bold* and **strong**", "\\*bold\\* and \\*\\*strong\\*\\*"),
    ("_it_ and __it__", "\\_it\\_ and \\_\\_it\\_\\_"),
    ("~gone~ ~~gone~~", "\\~gone\\~ \\~\\~gone\\~\\~"),
    ("snake_case_name", "snake\\_case\\_name"),
    # already escaped by the author: the backslash is escaped too and stays visible; nothing is escaped twice
    ("\\*not bold\\*", "\\\\\\*not bold\\\\\\*"),
    ("\\_ \\~ \\|", "\\\\\\_ \\\\\\~ \\\\\\|"),
    ("a < b & *c*", "a &lt; b &amp; \\*c\\*"),
    ("&lt;b&gt; &#x202E; &amp;", "&amp;lt;b&amp;gt; &amp;#x202E; &amp;amp;"),  # no character reference is decoded
    # bidi controls, zero-width characters and the byte order mark are removed
    ("abc\U0000202Egnp.exe", "abcgnp.exe"),
    ("a\U0000202A\U0000202B\U0000202C\U0000202D\U0000202Eb", "ab"),
    ("a\U00002066\U00002067\U00002068\U00002069b", "ab"),
    ("a\U0000200Eb\U0000200Fc\U0000061Cd", "abcd"),
    ("zero\U0000200Bwidth\U0000200C\U0000200D\U00002060\U0000FEFF", "zerowidth"),
    ("\U0000FEFF*x*", "\\*x\\*"),
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
        self.assertEqual(bc.esc_desc("a" * 119 + "*tail", 120), "a" * 119 + "\\*")
        self.assertEqual(bc.esc_desc("_" * 200, 120), "\\_" * 120)
        self.assertEqual(bc.esc_desc("\U0000200B" * 50 + "a" * 200, 120), "a" * 120)   # removed before the cut

    def test_esc_removes_invisible(self):
        self.assertEqual(bc.esc("na\U0000202Eme\U0000200B"), "name")

    def test_catalog_page_cell(self):
        row = {"name": "g", "genre": "puzzle", "repo": "https://github.com/o/g", "license": "MIT", "license_from": "github",
               "reuse": "copy", "language": "C", "stars": 1, "pushed": "2026-09-01", "archived": False, "active": True,
               "note": None, "description": "ok\n| x | y |\n<img src=x onerror=alert(1)> [a](javascript:alert(1)) `c` *e* ~s~\U0000202E"}
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "catalog"))
            bc.write_markdown([row], tmp, datetime.date(2026, 10, 1), {})
            with open(os.path.join(tmp, "catalog", "puzzle.md"), encoding="utf-8") as f:
                page = f.read()
        line = next(x for x in page.splitlines() if x.startswith("| [g]("))
        self.assertEqual(len(page.splitlines()), 7, page)
        self.assertNotIn("<", line)
        self.assertNotIn("[a](", line)
        self.assertIn("&lt;img src=x onerror=alert(1)&gt; \\[a\\](javascript:alert(1)) \\`c\\` \\*e\\* \\~s\\~ |", line)
        self.assertNotIn("\U0000202E", page)
        self.assertEqual(line.replace("\\|", "").count("|"), 8, line)


class ScaffoldPage(unittest.TestCase):
    """find_scaffolds.py writes repository descriptions through the same esc_desc as the catalog."""

    def test_description_cell(self):
        self.assertEqual(fs.esc_desc.__code__.co_filename, bc.esc_desc.__code__.co_filename)   # imported, not copied
        desc = "ok | x |\n<img src=x> [a](javascript:alert(1)) `c` *e* _u_ ~s~ \U0000202E" + "z" * 200
        row = {"name": "o/t", "repo": "https://github.com/o/t", "kind": "scaffold", "group": "Godot", "description": desc,
               "language": "GDScript", "license": "MIT", "reuse": "copy", "stars": 30, "pushed": "2026-09-01",
               "archived": False, "topics": []}
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "scaffolds"))
            fs.write_pages([row], tmp, datetime.date(2026, 10, 1))
            with open(os.path.join(tmp, "scaffolds", "scaffolds.md"), encoding="utf-8") as f:
                page = f.read()
        line = next(x for x in page.splitlines() if x.startswith("| [o/t]("))
        self.assertEqual(line, "| [o/t](https://github.com/o/t) | copy | MIT | GDScript | 30 | 2026-09-01 | "
                               + bc.esc_desc(desc, 110) + " |")
        self.assertIn("ok \\| x \\| &lt;img src=x&gt; \\[a\\](javascript:alert(1)) \\`c\\` \\*e\\* \\_u\\_ \\~s\\~ zz", line)
        self.assertNotIn("\U0000202E", page)
        self.assertEqual(line.replace("\\|", "").count("|"), 8, line)


if __name__ == "__main__":
    unittest.main()
