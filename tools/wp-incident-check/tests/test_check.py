"""Failure-first CLI checks; synthetic offline snapshots only. No real site or keys."""
import base64
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

if __name__=='__main__':unittest.main(verbosity=2)
