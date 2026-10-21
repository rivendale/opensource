"""Failure-first CLI checks; synthetic offline snapshots only. No real site or keys."""
import base64
import gzip
import io
import zipfile
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
TOOL = Path(os.environ.get('WP_INCIDENT_UNDER_TEST', HERE / 'wp-incident-check'))


class Contract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='wp-check-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.site = self.root / 'site'; self.site.mkdir()
        (self.site/'index.php').write_text('<?php echo "Synthetic only";')
        self.db = self.root/'export.sql'; self.db.write_text('-- synthetic empty SQL export\n')
        self.cron = self.root/'cron.txt'; self.cron.write_text('# synthetic empty crontab\n')
        self.keys = self.root/'keys.txt'; self.known = self.root/'known.txt'
        key = 'ssh-ed25519 ' + base64.b64encode(b'SYNTHETIC-PUBLIC-KEY').decode() + '\n'
        self.keys.write_text(key); self.known.write_text(key)
        self.args = ['--authorized-owner', '--site', str(self.site), '--database-export', str(self.db),
                     '--cron-export', str(self.cron), '--ssh-keys', str(self.keys), '--known-ssh-keys', str(self.known),
                     '--plugin-version', '3.0.124', '--installed-at', '2026-10-17T10:00:00+00:00']
    def run_tool(self, args=None, env=None, prefix=None):
        return subprocess.run((prefix or [sys.executable, '-B']) + [str(TOOL)] + (self.args if args is None else args),
                              capture_output=True, text=True, timeout=20,
                              env={**os.environ, 'PYTHONDONTWRITEBYTECODE':'1', **(env or {})})
    def snapshot(self):
        result = {}
        for p in [self.site, self.site/'index.php', self.db, self.cron, self.keys, self.known]:
            st=p.stat();result[str(p)]=(st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns,st.st_atime_ns)
        return result
    def test_authorization_precedes_all_reads_and_scanner_import(self):
        fake=self.root/'fake';fake.mkdir();marker=self.root/'launched'
        (fake/'yara.py').write_text('from pathlib import Path\nPath('+repr(str(marker))+').write_text("launched")\nraise RuntimeError("scanner invoked")\n')
        before=self.snapshot()
        r=self.run_tool([x for x in self.args if x!='--authorized-owner'],env={'PYTHONPATH':str(fake)})
        self.assertEqual(r.returncode,64);self.assertIn('authorization',r.stderr.lower())
        self.assertFalse(marker.exists());self.assertEqual(before,self.snapshot())
    def test_clean_snapshot_real_yara_and_no_write(self):
        before=self.snapshot();r=self.run_tool()
        self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual(before,self.snapshot())
        self.assertIn('YARA 4.5.4',r.stdout);self.assertIn('A clean result does not prove a site clean.',r.stdout)
        self.assertIn('No indicators found',r.stdout);self.assertIn('No remediation performed',r.stdout)
    def test_each_published_literal_is_found(self):
        for value,target in [('_uf6qdn2hmm','db'),('t8krdk990phb','db'),('_np5pvf754c','db'),
                             ('wpsupport_synthetic','db'),('#ms6v46','cron'),('rank1cdn.com','site')]:
            with self.subTest(value=value):
                path={'db':self.db,'cron':self.cron,'site':self.site/'index.php'}[target]
                original=path.read_bytes();path.write_text('Synthetic indicator '+value+'\n')
                before=self.snapshot();r=self.run_tool()
                self.assertEqual(r.returncode,1,r.stdout+r.stderr);self.assertIn('Potential indicator',r.stdout)
                self.assertEqual(before,self.snapshot());path.write_bytes(original)
    def test_unsupported_exports_fail_closed_without_changing_evidence(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('export.sql','_uf6qdn2hmm')
        for data in ['_uf6qdn2hmm'.encode('utf-16'), gzip.compress(b'_uf6qdn2hmm'),
                     stream.getvalue(), b'plain\x00text', b'x'*70000+b'\x00']:
            for path in [self.db,self.cron]:
                with self.subTest(path=path.name,signature=data[:4]):
                    old=path.read_bytes();path.write_bytes(data);before=self.snapshot()
                    r=self.run_tool()
                    self.assertEqual(r.returncode,2,r.stdout+r.stderr)
                    self.assertIn('unsupported export format',r.stdout)
                    self.assertNotIn('No indicators found',r.stdout)
                    self.assertEqual(before,self.snapshot());path.write_bytes(old)

    def test_large_export_chunk_boundary_and_site_budget_independence(self):
        # A match crossing the first 64 KiB read and another beyond 8 MiB.
        self.db.write_bytes(b'x'*(65536-5)+b'_uf6qdn2hmm'+b'x'*(11*1024*1024)+b't8krdk990phb')
        self.cron.write_text('#ms6v46')
        for i in range(12000): (self.site/('image-%05d.jpg'%i)).touch()
        before=self.snapshot();r=self.run_tool()
        self.assertEqual(r.returncode,2,r.stdout+r.stderr)
        self.assertIn('published option-name text',r.stdout)
        self.assertIn('published cron-marker text',r.stdout)
        self.assertIn('Checked: database export text',r.stdout)
        self.assertIn('Checked: cron export text',r.stdout)
        self.assertIn('site file-count limit',r.stdout)
        self.assertNotIn('database export unreadable',r.stdout)
        self.assertEqual(before,self.snapshot())

    def test_large_export_and_split_literal_are_checked_without_site_limit(self):
        for data in [b'x'*(65536-5)+b'_uf6qdn2hmm',b'x'*(11*1024*1024)+b't8krdk990phb']:
            self.db.write_bytes(data);r=self.run_tool()
            self.assertEqual(r.returncode,1,r.stdout+r.stderr)
            self.assertIn('published option-name text',r.stdout)

    def test_export_cap_names_the_actual_limit_and_still_checks_cron(self):
        with self.db.open('wb') as f: f.truncate(256*1024*1024+1)
        self.cron.write_text('#ms6v46');before=self.snapshot();r=self.run_tool()
        self.assertEqual(r.returncode,2,r.stdout+r.stderr)
        self.assertIn('database export not fully checked: export byte limit (256 MiB)',r.stdout)
        self.assertIn('Checked: cron export text',r.stdout)
        self.assertIn('published cron-marker text',r.stdout)
        self.assertEqual(before,self.snapshot())

    def test_case_variants_and_explicit_published_omissions(self):
        (self.site/'index.php').write_text('RANK1CDN.COM')
        r=self.run_tool();self.assertEqual(r.returncode,1,r.stdout+r.stderr)
        self.assertIn('callback-domain',r.stdout)
        for omission in ['class-wp-cache-util.php','@wp-mail.net','xmmqhn','.cache-as-PHP']:
            self.assertIn(omission,r.stdout)

    def test_account_match_does_not_claim_confirmed_admin_or_echo_data(self):
        self.db.write_text('-- wpsupport_synthetic\n-- secret=SYNTHETIC-SECRET-DO-NOT-PRINT\n')
        r=self.run_tool();self.assertEqual(r.returncode,1,r.stdout+r.stderr)
        self.assertIn('role/activity not verified',r.stdout);self.assertNotIn('SYNTHETIC-SECRET',r.stdout+r.stderr)
    def test_window_boundaries_and_unknown_install_history(self):
        for day,expected in [('2026-10-15T20:01:59+00:00',0),('2026-10-15T20:02:00+00:00',1),
                             ('2026-10-16T07:12:00+00:00',1),('2026-10-16T07:12:01+00:00',0)]:
            args=self.args.copy();args[args.index('--plugin-version')+1]='3.0.123';args[-1]=day
            r=self.run_tool(args);self.assertEqual(r.returncode,expected,r.stdout+r.stderr)
        args=self.args[:-4];r=self.run_tool(args);self.assertEqual(r.returncode,2);self.assertIn('installation history not checked',r.stdout)
    def test_unexpected_ssh_key_requires_baseline_and_never_prints_key(self):
        self.keys.write_text('ssh-ed25519 '+base64.b64encode(b'SYNTHETIC-UNKNOWN-KEY').decode()+'\n')
        r=self.run_tool();self.assertEqual(r.returncode,1,r.stdout+r.stderr)
        self.assertIn('Unexpected SSH keys: 1',r.stdout);self.assertNotIn('ssh-ed25519',r.stdout)
        args=self.args.copy();i=args.index('--known-ssh-keys');del args[i:i+2]
        r=self.run_tool(args);self.assertEqual(r.returncode,2);self.assertIn('SSH baseline not checked',r.stdout)
    def test_partial_input_is_not_clean(self):
        self.db.unlink();r=self.run_tool();self.assertEqual(r.returncode,2);self.assertIn('PARTIAL',r.stdout)
        self.assertNotIn('No indicators found',r.stdout)
    def test_symlink_is_not_followed(self):
        outside=self.root/'outside.php';outside.write_text('rank1cdn.com')
        (self.site/'escape.php').symlink_to(outside)
        before=outside.stat();r=self.run_tool();after=outside.stat()
        self.assertEqual(r.returncode,2);self.assertIn('symlink',r.stdout.lower());self.assertNotIn('Potential indicator',r.stdout)
        self.assertEqual(before.st_atime_ns,after.st_atime_ns)
    def test_oversize_file_is_reported_partial(self):
        (self.site/'large.php').write_bytes(b'x'*(8*1024*1024+1))
        r=self.run_tool();self.assertEqual(r.returncode,2);self.assertIn('size limit',r.stdout)
    def test_scanner_failure_and_missing_engine_fail_closed(self):
        fake=self.root/'fake';fake.mkdir();(fake/'yara.py').write_text('__version__="4.5.4"\ndef compile(**kw): raise RuntimeError("SYNTHETIC-SECRET")\n')
        r=self.run_tool(env={'PYTHONPATH':str(fake)});self.assertEqual(r.returncode,2)
        self.assertNotIn('SYNTHETIC-SECRET',r.stdout+r.stderr)
        r=self.run_tool(prefix=[sys.executable,'-S','-B']);self.assertEqual(r.returncode,2)
    def test_no_network_or_site_execution(self):
        guard=self.root/'guard';guard.mkdir()
        (guard/'sitecustomize.py').write_text('import socket,subprocess\ndef deny(*a,**k): raise RuntimeError("network/process forbidden")\nsocket.socket=deny\nsubprocess.Popen=deny\n')
        (self.site/'index.php').write_text('<?php file_put_contents("PWNED", "rank1cdn.com"); ?>')
        r=self.run_tool(env={'PYTHONPATH':str(guard)});self.assertEqual(r.returncode,1,r.stdout+r.stderr)
        self.assertFalse((self.site/'PWNED').exists());self.assertFalse((Path.cwd()/'PWNED').exists())
    def test_combined_indicators_and_reports_are_read_only(self):
        self.db.write_text('_uf6qdn2hmm wpsupport_synthetic');self.cron.write_text('#ms6v46')
        (self.site/'index.php').write_text('rank1cdn.com')
        before=self.snapshot();r=self.run_tool();self.assertEqual(r.returncode,1,r.stdout+r.stderr)
        self.assertGreaterEqual(r.stdout.count('Potential indicator'),4);self.assertEqual(before,self.snapshot())
        self.assertIn('https://rankmath.com/kb/pro-3-0-123-security-incident/',r.stdout)


class Gaps(unittest.TestCase):
    """Promises made by the README and FAILURES.md that a mutation pass over the tool found unpinned (each test is written from the stated promise, not from the code)."""
    setUp = Contract.setUp
    run_tool = Contract.run_tool
    snapshot = Contract.snapshot

    def fake_yara(self, version='4.5.4', match_raises=False):
        fake = self.root/'fake'; fake.mkdir(exist_ok=True)
        (fake/'yara.py').write_text('__version__=%r\nclass E:\n    def match(self, data=None, timeout=None):\n        %s\ndef compile(**kw): return E()\n'
                                    % (version, 'raise RuntimeError("SYNTHETIC-SECRET")' if match_raises else 'return []'))
        return {'PYTHONPATH': str(fake)}

    def rules_file(self, change):
        doc = json.loads((HERE/'rules/rank-math-pro-3.0.123.json').read_text()); change(doc)
        path = self.root/'rules.json'; path.write_text(json.dumps(doc)); return ['--rules', str(path)]

    def test_scanner_failure_while_matching_is_partial_never_clean(self):
        r = self.run_tool(env=self.fake_yara(match_raises=True))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr); self.assertNotIn('No indicators found', r.stdout)
        self.assertIn('scanner error', r.stdout); self.assertNotIn('SYNTHETIC-SECRET', r.stdout + r.stderr)

    def test_a_different_scanner_version_is_not_used(self):
        r = self.run_tool(env=self.fake_yara(version='4.5.3'))
        self.assertEqual(r.returncode, 2, r.stdout + r.stderr); self.assertIn('PARTIAL', r.stdout); self.assertNotIn('No indicators found', r.stdout)

    def test_rules_that_change_source_or_carry_unprintable_literals_are_refused(self):
        for label, change in [('source', lambda d: d['checks'][0].__setitem__('source', 'https://example.org/other')),
                              ('literal', lambda d: d['checks'][0]['literals'].append('bad\nliteral')),
                              ('target', lambda d: d['checks'][0].__setitem__('targets', ['site', 'registry']))]:
            with self.subTest(label):
                r = self.run_tool(self.args + self.rules_file(change))
                self.assertEqual(r.returncode, 2, r.stdout + r.stderr); self.assertIn('PARTIAL: pinned YARA scanner/rules', r.stdout)

    def test_an_indicator_only_counts_in_the_inputs_its_rule_names(self):
        (self.site/'index.php').write_text('_uf6qdn2hmm wpsupport_synthetic t8krdk990phb')   # database-only literals in a site file
        self.cron.write_text('wpsupport_synthetic _np5pvf754c\n')                          # database-only literals in a crontab
        r = self.run_tool(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr); self.assertNotIn('Potential indicator', r.stdout)

    def test_the_update_window_needs_the_affected_version(self):
        args = self.args.copy(); args[args.index('--installed-at') + 1] = '2026-10-16T01:00:00+00:00'
        r = self.run_tool(args); self.assertEqual(r.returncode, 0, r.stdout + r.stderr)                 # version 3.0.124 inside the window
        self.assertNotIn('Potential indicator', r.stdout)
        args[args.index('--plugin-version') + 1] = '3.0.123'; r = self.run_tool(args)
        self.assertEqual(r.returncode, 1); self.assertIn('owner-recorded update', r.stdout)

    def test_an_install_time_without_a_timezone_is_not_assumed(self):
        args = self.args.copy(); args[args.index('--plugin-version') + 1] = '3.0.123'; args[args.index('--installed-at') + 1] = '2026-10-16T01:00:00'
        r = self.run_tool(args); self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        self.assertIn('invalid timezone/date', r.stdout); self.assertNotIn('owner-recorded update', r.stdout)

    def test_ssh_comparison_runs_from_supplied_keys_to_baseline_and_rejects_bad_lines(self):
        a = 'ssh-ed25519 ' + base64.b64encode(b'KEY-A').decode() + '\n'; b = 'ssh-ed25519 ' + base64.b64encode(b'KEY-B').decode() + '\n'
        self.keys.write_text(a + b); self.known.write_text(a)
        r = self.run_tool(); self.assertEqual(r.returncode, 1); self.assertIn('Unexpected SSH keys: 1', r.stdout)
        self.keys.write_text(a); self.known.write_text(a + b)               # a baseline that lists more keys than the host has is not a finding
        r = self.run_tool(); self.assertEqual(r.returncode, 0, r.stdout + r.stderr); self.assertNotIn('Unexpected SSH keys', r.stdout)
        for bad in ('ssh-bogus ' + base64.b64encode(b'x').decode() + '\n', 'ssh-ed25519 not*base64!\n'):
            self.keys.write_text(bad); r = self.run_tool()
            self.assertEqual(r.returncode, 2, bad); self.assertIn('SSH baseline not checked', r.stdout)

    def test_a_hostile_file_name_cannot_inject_terminal_codes_or_lines(self):
        (self.site/'x\x1b[31mred\nPotential indicator: forged line.php').write_text('rank1cdn.com')
        r = self.run_tool(); self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertNotIn('\x1b', r.stdout)
        self.assertEqual([ln for ln in r.stdout.splitlines() if ln.startswith('Potential indicator: forged')], [])
        self.assertEqual(len([ln for ln in r.stdout.splitlines() if ln.startswith('Potential indicator')]), 1)

    def test_a_match_inside_the_chunk_overlap_is_reported_once(self):
        self.db.write_bytes(b'a' * (65536 - 20) + b'rank1cdn.com' + b'b' * 70000)
        r = self.run_tool(); self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertEqual(len([ln for ln in r.stdout.splitlines() if ln.startswith('Potential indicator') and 'database export' in ln]), 1)

    def test_the_overlap_covers_the_longest_permitted_literal(self):
        literal = 'L' * 128
        def change(d):
            d['checks'] = [{'id': 'long_literal', 'targets': ['database'], 'literals': [literal], 'label': 'synthetic long literal', 'source': d['window']['source']}]
        self.db.write_bytes(b'x' * (65536 - 100) + literal.encode() + b'y' * 70000)       # 100 bytes in the first chunk, 28 in the next
        r = self.run_tool(self.args + self.rules_file(change)); self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn('synthetic long literal', r.stdout)

    def test_special_files_deep_trees_and_symlinks_are_named_in_the_report(self):
        os.mkfifo(self.site/'pipe'); (self.site/'link.php').symlink_to(self.db)
        path = self.site
        for _ in range(40): path = path/'d'; path.mkdir()
        r = self.run_tool(); self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
        for line in ('Not checked: special file skipped', 'Not checked: symlink skipped', 'Not checked: directory depth limit'):
            self.assertIn(line, r.stdout)

if __name__=='__main__':unittest.main(verbosity=2)
