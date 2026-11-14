"""Local workflow contract checks. Requires PyYAML; no network or GitHub API."""
import os
from pathlib import Path
import subprocess
import shutil
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[2]


class PagesGame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = yaml.safe_load(
            (ROOT / '.github/workflows/pages-game.yml').read_text())
        cls.steps = cls.workflow['jobs']['test']['steps']

    def test_deploy_refuses_pull_requests_and_disabled_deploy(self):
        guard = self.workflow['jobs']['deploy']['if']
        self.assertEqual(guard, "inputs.deploy && github.event_name != 'pull_request'")
        for enabled, event, expected in [
            (False, 'push', False), (True, 'pull_request', False),
            (False, 'pull_request', False), (True, 'push', True),
        ]:
            actual = enabled and event != 'pull_request'
            self.assertEqual(actual, expected)
            print(f'deploy={enabled}, event={event}: {"allowed" if actual else "REFUSED"}')

    def test_failed_command_stops_step(self):
        step = next(s for s in self.steps if s.get('name') == 'Test')
        result = subprocess.run(['bash', '-e', '-c', step['run']],
                                env={**os.environ, 'COMMAND': 'echo deliberate-failure; exit 17'},
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 17)
        print(f'{result.stdout.strip()}: exit {result.returncode}')

    def test_command_is_data_until_bash_executes_it(self):
        for job in self.workflow['jobs'].values():
            for step in job['steps']:
                self.assertNotIn('${{', step.get('run', ''))
        step = next(s for s in self.steps if s.get('name') == 'Test')
        result = subprocess.run(['bash', '-e', '-c', step['run']],
                                env={**os.environ, 'COMMAND': 'printf "%s\\n" \'literal " quotation\''},
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, 'literal " quotation\n')
        print('command quotation preserved; no input interpolated into scripts')

    def test_optional_steps_skip_empty_commands(self):
        for name, key in [('Typecheck', 'typecheck'), ('Build', 'build'),
                          ('Install Playwright', 'e2e'), ('E2E', 'e2e')]:
            step = next(s for s in self.steps if s.get('name') == name)
            self.assertEqual(step['if'], f"inputs.{key} != ''")
            print(f'empty {key}: {name} SKIPPED')

    def test_fixture_refuses_missing_static_page(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            shutil.copy(ROOT / 'fixtures/pages-game/package.json', directory)
            result = subprocess.run(['npm', 'test'], cwd=directory,
                                    capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ENOENT', result.stderr)
        print('missing static/index.html: ENOENT; npm test exit 1')

    def test_smoke_failure_is_not_swallowed(self):
        step = self.workflow['jobs']['deploy']['steps'][-1]
        self.assertEqual(step['if'], "inputs.smoke-url != ''")
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            curl = Path(directory) / 'curl'
            curl.write_text('#!/bin/bash\nprintf "curl failure stub: %s\\n" "$*"\nexit 22\n')
            curl.chmod(0o755)
            result = subprocess.run(['bash', '-e', '-c', step['run']],
                                    env={**os.environ, 'PATH': directory + ':' + os.environ['PATH'],
                                         'SMOKE_URL': 'https://example.invalid/a?x=1&y=2'},
                                    capture_output=True, text=True)
        self.assertEqual(result.returncode, 22)
        self.assertIn('--retry 6 --retry-delay 5 --retry-all-errors --max-time 40', result.stdout)
        self.assertIn('https://example.invalid/a?x=1&y=2', result.stdout)
        print(result.stdout.strip() + '; exit 22')


if __name__ == '__main__':
    unittest.main(verbosity=2)
