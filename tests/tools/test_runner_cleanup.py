#!/usr/bin/env python3
"""The eval runner's temp cleanup must never change the mode of anything outside its temp root.

The runner's toolbin holds symlinks to the real bash, env, python3 and git. os.chmod follows symlinks, so a cleanup
that chmods every entry strips the execute bits from those system binaries when the runner runs as root.

    python3 tests/tools/test_runner_cleanup.py
"""
import importlib.util, os, pathlib, stat, sys, tempfile, unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("evals_runner", ROOT / "tools/evals/runner.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def mode(p):
    return stat.S_IMODE(os.stat(p).st_mode)


class RemoveTree(unittest.TestCase):
    def setUp(self):
        self.outside = pathlib.Path(tempfile.mkdtemp(prefix="cleanup-outside-"))
        self.target = self.outside / "tool"
        self.target.write_text("#!/bin/sh\n")
        self.target.chmod(0o755)
        self.target_dir = self.outside / "dir"
        self.target_dir.mkdir()
        self.target_dir.chmod(0o755)
        self.root = pathlib.Path(tempfile.mkdtemp(prefix="cleanup-root-"))
        (self.root / "toolbin").mkdir()
        (self.root / "toolbin" / "bash").symlink_to(self.target)
        (self.root / "linked-dir").symlink_to(self.target_dir, target_is_directory=True)
        locked = self.root / "work" / "locked"
        locked.mkdir(parents=True)
        (locked / "file").write_text("x")
        locked.chmod(0o000)

    def tearDown(self):
        for p in (self.outside, self.target_dir):
            os.chmod(p, 0o755)
        runner.shutil.rmtree(self.outside, ignore_errors=True)
        runner.shutil.rmtree(self.root, ignore_errors=True)

    def test_symlink_targets_keep_their_mode(self):
        runner.remove_tree(self.root)
        self.assertEqual(mode(self.target), 0o755)
        self.assertEqual(mode(self.target_dir), 0o755)
        self.assertTrue(self.target.exists() and self.target_dir.is_dir())

    def test_tree_is_removed_even_when_locked(self):
        runner.remove_tree(self.root)
        self.assertFalse(self.root.exists())


if __name__ == "__main__":
    unittest.main()
