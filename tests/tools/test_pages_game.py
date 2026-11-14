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
        self.assertEqual(guard, "inputs.deploy && (github.event_name == 'push' || github.event_name == 'workflow_dispatch') && github.ref == format('refs/heads/{0}', github.event.repository.default_branch)")
        print('deploy guard requires enabled deploy, allowed event and default branch')

    def test_cache_is_optional_without_lockfile(self):
        setup = next(s for s in self.steps if s.get('name') == 'Setup Node')['with']
        exists = "hashFiles(format('{0}/package-lock.json', inputs.working-directory)) != ''"
        self.assertEqual(setup['cache'], "${{ " + exists + " && 'npm' || '' }}")
        self.assertEqual(setup['cache-dependency-path'], "${{ " + exists + " && format('{0}/package-lock.json', inputs.working-directory) || '' }}")
        print('missing lockfile: npm cache and dependency path disabled')

    def test_artifact_names_and_bare_fixture(self):
        inputs = self.workflow.get('on', self.workflow.get(True))['workflow_call']['inputs']
        self.assertEqual(inputs['artifact-name']['default'], 'github-pages')
        upload = next(s for s in self.steps if s.get('name') == 'Upload Pages artifact')
        deploy = next(s for s in self.workflow['jobs']['deploy']['steps'] if s.get('name') == 'Deploy Pages')
        self.assertEqual(upload['with']['name'], '${{ inputs.artifact-name }}')
        self.assertEqual(deploy['with']['artifact_name'], '${{ inputs.artifact-name }}')
        selftest = yaml.safe_load((ROOT / '.github/workflows/pages-game-selftest.yml').read_text())
        calls = [j['with'] for j in selftest['jobs'].values()]
        self.assertEqual(len(calls), 3)
        self.assertEqual(len({j['artifact-name'] for j in calls}), 3)
        bare = next(j for j in calls if j['working-directory'] == 'fixtures/pages-game-bare')
        for key in ('install', 'test', 'build'):
            self.assertEqual(bare[key], '')
        self.assertIs(bare['deploy'], False)
        self.assertEqual(bare['artifact-path'], 'site')
        folder = ROOT / bare['working-directory']
        self.assertEqual(sorted(str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file()), ['site/index.html'])
        print('three distinct artifacts; bare fixture has only site/index.html')

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
        for name, key in [('Install', 'install'), ('Test', 'test'),
                          ('Typecheck', 'typecheck'), ('Build', 'build'),
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
