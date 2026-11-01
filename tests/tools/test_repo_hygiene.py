#!/usr/bin/env python3
"""tools/hygiene/repo_hygiene.py: its selftest, its command line, and this repo's own .hygiene.json.

    python3 tests/tools/test_repo_hygiene.py

The selftest plants each defect in a temp git repo. These tests cover what the selftest does not: exit codes,
GitHub annotation escaping, config errors on the command line, and that this repo passes its own config.
"""
import json, os, pathlib, subprocess, sys, tempfile, unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/hygiene/repo_hygiene.py"
ROOT_SAFETY = ROOT / "tools/hygiene/root_safety.sh"
ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "GITHUB_ACTIONS": "",
       "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}


def tool(*args, env=None):
    return subprocess.run([sys.executable, str(TOOL), *args], capture_output=True, text=True,
                          env={**ENV, **(env or {})})


KEEP = []  # the temp dirs live until the process exits, so Repo(...).path stays valid


class Repo:
    def __init__(self, files, config=None):
        self.dir = tempfile.TemporaryDirectory()
        KEEP.append(self.dir)
        self.path = self.dir.name
        for rel, text in files.items():
            p = pathlib.Path(self.path, rel)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text, encoding="utf-8")
        if config is not None:
            pathlib.Path(self.path, ".hygiene.json").write_text(json.dumps(config), encoding="utf-8")
        for a in (["init", "-q"], ["add", "-A"], ["-c", "commit.gpgsign=false", "commit", "-qm", "c"]):
            subprocess.run(["git", "-C", self.path, *a], check=True, capture_output=True, env=ENV)


class Hygiene(unittest.TestCase):
    def test_selftest_passes(self):
        r = tool("--selftest")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("all checks hold", r.stdout)

    def test_tools_are_executable_and_ascii(self):
        for t in (TOOL, ROOT_SAFETY):
            self.assertTrue(os.access(t, os.X_OK), t)
            self.assertTrue(t.read_text(encoding="utf-8").isascii(), t)

    def test_this_repo_passes_its_own_config(self):
        r = tool("--root", str(ROOT))
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_this_repo_root_safety_commands(self):
        r = tool("--root", str(ROOT), "--print-root-safety")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("python3 tools/evals/runner.py glean", r.stdout.splitlines())

    def test_exit_codes(self):
        clean = Repo({"a.md": "ok\n"})
        self.assertEqual(tool("--root", clean.path).returncode, 0)
        dirty = Repo({"a.md": "x\u202ey\n"})
        r = tool("--root", dirty.path)
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("FAIL  invisible: a.md:1:2 raw U+202E", r.stdout)

    def test_stale_warns_with_exit_0_and_fails_with_stale_fails(self):
        files = {"docs/a.md": "License checked 2026-01-01.\n"}
        r = tool("--root", Repo(files).path, "--today", "2026-06-01")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("WARN  stale: docs/a.md:1", r.stdout)
        r = tool("--root", Repo(files, {"stale_fails": True}).path, "--today", "2026-06-01")
        self.assertEqual(r.returncode, 1, r.stdout)

    def test_config_errors_exit_2(self):
        r = tool("--root", Repo({"a": "x\n"}, {"stale_globz": []}).path)
        self.assertEqual(r.returncode, 2, r.stdout)
        self.assertIn("unknown key(s) stale_globz", r.stdout)
        broken = Repo({"a": "x\n"})
        pathlib.Path(broken.path, ".hygiene.json").write_text("{not json", encoding="utf-8")
        self.assertEqual(tool("--root", broken.path).returncode, 2)
        self.assertEqual(tool("--root", broken.path, "--config", "missing.json").returncode, 2)

    def test_github_annotations_are_escaped(self):
        repo = Repo({"a.md": "ok\n"}, {"claims": [{"file": "a.md", "pattern": "100% (\\d+)", "count_glob": "*"}]})
        r = tool("--root", repo.path, env={"GITHUB_ACTIONS": "true"})
        self.assertEqual(r.returncode, 1)
        line = [l for l in r.stdout.splitlines() if l.startswith("::error::")][0]
        self.assertIn("100%25", line)
        self.assertNotIn("100% ", line)


class RootSafety(unittest.TestCase):
    """tools/hygiene/root_safety.sh against a fake system tree, without a container."""

    def setUp(self):
        self.d = pathlib.Path(tempfile.mkdtemp(prefix="rootsafety-"))
        self.addCleanup(subprocess.run, ["rm", "-rf", "--", str(self.d)])
        self.sys = self.d / "sys"
        (self.sys / "bin").mkdir(parents=True)
        (self.sys / "f").write_text("keep\n")
        (self.sys / "bin" / "tool").write_text("#!/bin/sh\n")
        (self.sys / "bin" / "tool").chmod(0o755)
        self.work = self.d / "work"
        self.work.mkdir()

    def run_sh(self, *commands, dirs=None):
        cmds = self.d / "commands.txt"
        cmds.write_text("".join(c + "\n" for c in commands))
        env = {**os.environ, "ROOT_SAFETY_DIRS": dirs or str(self.sys), "ROOT_SAFETY_HASH_DIRS": str(self.sys / "bin")}
        return subprocess.run(["bash", str(ROOT_SAFETY), str(cmds), str(self.work)], capture_output=True, text=True,
                              env=env)

    def test_clean_commands_pass_and_new_files_are_fine(self):
        r = self.run_sh("true", f"touch {self.sys}/new")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_deleting_a_file_fails_even_when_the_command_also_deletes_snapshot_files(self):
        # The reviewer's case: the old job kept its snapshots in /tmp, so a command could remove them.
        r = self.run_sh(f"rm -f {self.sys}/f; rm -rf /tmp/before /tmp/after {self.d}/before")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn(f"{self.sys}/f", r.stdout)

    def test_a_mode_change_through_a_symlink_fails(self):
        r = self.run_sh(f"ln -s {self.sys}/bin/tool {self.work}/link && chmod 644 {self.work}/link")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("755", r.stdout)

    def test_a_write_through_a_symlink_into_a_bin_directory_fails(self):
        r = self.run_sh(f"ln -s {self.sys}/bin/tool {self.work}/link && echo x >> {self.work}/link")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("/bin/tool", r.stdout)

    def test_removing_a_snapshot_directory_fails_instead_of_passing(self):
        r = self.run_sh(f"rm -rf {self.sys}")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("snapshot after the commands failed", r.stdout)

    def test_no_snapshot_directory_fails(self):
        r = self.run_sh("true", dirs=str(self.d / "missing"))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("none of the snapshot directories exist", r.stdout)

    def test_a_failing_command_fails_and_stdin_is_closed(self):
        r = self.run_sh("read x; echo \"got [$x]\"", "false", "touch after-false")
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("got []", r.stdout)
        self.assertTrue((self.work / "after-false").exists())


class ConfigNotice(unittest.TestCase):
    def test_loosening_the_config_prints_a_notice_not_a_failure(self):
        repo = Repo({"a.md": "ok\n"}, {"stale_fails": True})
        pathlib.Path(repo.path, ".hygiene.json").write_text(json.dumps({"stale_fails": False, "modes": False}))
        for a in (["add", "-A"], ["-c", "commit.gpgsign=false", "commit", "-qm", "loosen"]):
            subprocess.run(["git", "-C", repo.path, *a], check=True, capture_output=True, env=ENV)
        r = tool("--root", repo.path, "--base", "HEAD~1")
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertIn("NOTE  config: this change to .hygiene.json turns modes off", r.stdout)
        self.assertIn("turns stale_fails off", r.stdout)
        r = tool("--root", repo.path, "--base", "HEAD~1", env={"GITHUB_ACTIONS": "true"})
        self.assertIn("::notice::config:", r.stdout)


if __name__ == "__main__":
    unittest.main()
