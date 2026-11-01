#!/usr/bin/env python3
"""glean-check keeps a card's `copy` class only when its license evidence is a file in the card's own repository
(credit.source_url) at the card's own commit (where.sha). Another repository or a moving branch is no evidence.

    python3 tests/tools/test_glean_check.py
"""
import json, pathlib, subprocess, sys, tempfile, unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
SHA = "a1b2c3d4e5f60718293a4b5c6d7e8f9012345678"
OTHER_SHA = "0" * 40
SOURCE = "https://github.com/o/r"


def card(evidence, source=SOURCE, sha=SHA):
    return {"id": "c1", "idea": "stream the file in chunks", "where": {"file": "src/reader.py", "line": 42, "sha": sha},
            "solves": "memory use on large inputs", "decision": "port", "target": "Ship the reader",
            "done_when": "a 2 GB file reads in 64 MB", "adds": [],
            "license": {"spdx": "MIT", "evidence_url": evidence, "classification": "copy"},
            "credit": {"author": "Jane Roe", "author_url": "https://github.com/o", "source_url": source,
                       "text": "adapted from Jane Roe's reader"}}


def check(c):
    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp, "cards.jsonl")
        path.write_text(json.dumps(c) + "\n", encoding="utf-8")
        r = subprocess.run([sys.executable, str(ROOT / "tools/glean-check"), str(path), "--now", "2026-11-01T00:00:00+00:00"],
                           capture_output=True, text=True, cwd=ROOT / "tools")
    out = json.loads(r.stdout)
    return out["cards"][0], [f["code"] for f in out["findings"]]


KEPT = [
    f"{SOURCE}/blob/{SHA}/LICENSE",                          # what glean-resolve prints
    f"{SOURCE}/blob/{SHA}/docs/LICENSE.md#L1",
    f"https://github.com/O/R/blob/{SHA.upper()}/LICENSE",    # GitHub names and SHAs are case-insensitive
]
REFUSED = [
    f"https://github.com/other/r/blob/{SHA}/LICENSE",        # another repository
    f"https://github.com/o/r2/blob/{SHA}/LICENSE",           # a repository whose name starts with the card's
    f"https://github.com/o/blob/{SHA}/LICENSE",
    f"https://gitlab.com/o/r/-/blob/{SHA}/LICENSE",          # another host
    f"http://github.com/o/r/blob/{SHA}/LICENSE",             # another scheme
    f"{SOURCE}/blob/main/LICENSE",                            # a moving branch
    f"{SOURCE}/blob/v1.0/LICENSE",                            # a tag
    f"{SOURCE}/blob/{OTHER_SHA}/LICENSE",                     # another commit
    f"{SOURCE}/blob/{SHA[:12]}/LICENSE",                      # a short SHA
    f"{SOURCE}/tree/{SHA}",                                   # a directory, not a file
    f"{SOURCE}/blob/{SHA}/",                                  # no file
    f"{SOURCE}/blob/{SHA}/../../../other/r/blob/{SHA}/LICENSE",
    f"{SOURCE}/blob/{SHA}/%2e%2e/%2e%2e/LICENSE",
    f"{SOURCE}/blob/{SHA}/LICENSE?ref=main",
    f"{SOURCE}/commit/{SHA}",
    "https://example.test/x",
]


class EvidenceUrl(unittest.TestCase):
    def test_own_repo_and_commit_is_kept(self):
        for evidence in KEPT:
            with self.subTest(evidence=evidence):
                c, codes = check(card(evidence))
                self.assertEqual(c["license"]["classification"], "copy")
                self.assertEqual(c["decision"], "port")
                self.assertNotIn("license restricted", codes)

    def test_gitlab_blob_form(self):
        c, _ = check(card(f"https://gitlab.com/g/sub/p/-/blob/{SHA}/LICENSE", source="https://gitlab.com/g/sub/p"))
        self.assertEqual(c["license"]["classification"], "copy")

    def test_elsewhere_is_refused(self):
        for evidence in REFUSED:
            with self.subTest(evidence=evidence):
                c, codes = check(card(evidence))
                self.assertEqual(c["license"]["classification"], "check first")
                self.assertEqual(c["decision"], "take")
                self.assertIn("license restricted", codes)
                self.assertIn("port refused", codes)

    def test_card_pinned_to_a_branch_is_refused(self):
        c, codes = check(card(f"{SOURCE}/blob/main/LICENSE", sha="main"))
        self.assertEqual(c["license"]["classification"], "check first")
        self.assertIn("card has no WHERE", codes)

    def test_evidence_must_match_the_credited_source(self):
        c, _ = check(card(f"https://github.com/other/r/blob/{SHA}/LICENSE", source="https://github.com/o/r"))
        self.assertEqual(c["license"]["classification"], "check first")
        for source in (None, "https://github.com/o", "https://github.com/o/r?x=1"):
            with self.subTest(source=source):
                c, _ = check(card(f"{SOURCE}/blob/{SHA}/LICENSE", source=source))
                self.assertEqual(c["license"]["classification"], "check first")


if __name__ == "__main__":
    unittest.main()
