#!/usr/bin/env python3
"""Disk boundary failures from DRIVER-FAILURES; synthetic data, no renderer/network."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('driver',HERE/'driver.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PersistTests(unittest.TestCase):
 def setUp(self):
  self.fixture=json.loads((HERE/'tests/fixtures/synthetic-pair.json').read_text())
  self.result=dict(status='partial',pairs_completed=1,events=self.fixture['events'],records=[self.fixture['record']],plan_records=[])
  self.relay=object.__new__(m.Relay);self.relay.keys={'synthetic':b'SYNTHETIC-PERSIST-MARKER'};self.relay.incident=False
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.output=Path(self.temp.name)/'batch'
 def persist(self):
  with patch.object(m,'build_plan',return_value=[self.fixture['pair']]):return m.persist_collection(self.relay,self.result,self.output)
 def test_disk_roundtrip_never_claims_finished_or_writes_receipt(self):
  result=self.persist();self.assertEqual(result['status'],'partial');self.assertEqual(result['artifacts_written'],3)
  self.assertEqual(json.loads((self.output/'records.json').read_text()),self.result['records'])
  self.assertEqual(set(p.name for p in self.output.iterdir()),{'records.json','plan-records.json','events.jsonl'})
  self.assertEqual(result['disk_records_verified'],True)
  self.assertEqual(len(result['sha256']),3)
 def test_existing_directory_or_symlink_never_overwritten(self):
  self.output.mkdir();self.assertEqual(self.persist()['artifacts_written'],0);sentinel=self.output/'records.json';sentinel.write_text('existing')
  self.assertEqual(self.persist()['artifacts_written'],0);self.assertEqual(sentinel.read_text(),'existing')
  self.output=Path(self.temp.name)/'link';self.output.symlink_to(sentinel.parent,target_is_directory=True)
  self.assertEqual(self.persist()['artifacts_written'],0);self.assertEqual(sentinel.read_text(),'existing')
 def test_disagreement_refused_before_any_output(self):
  self.result['records'][0]['name']='invented'
  self.assertEqual(self.persist()['artifacts_written'],0);self.assertFalse(self.output.exists())
 def test_each_artifact_scanned_and_incident_suppresses_tree(self):
  original=m.Relay.output_has_key
  for target in (b'"image"',b'[]',b'"kind"'):
   with self.subTest(target=target):
    self.relay.incident=False;self.output=Path(self.temp.name)/str(len(target))
    def scan(relay,body):return target in body or original(relay,body)
    with patch.object(m.Relay,'output_has_key',scan), patch.object(Path,'open',side_effect=AssertionError('write before complete scan')):result=self.persist()
    self.assertEqual(result['status'],'incident');self.assertFalse(self.output.exists())
 def test_unwritable_file_is_partial_and_not_complete(self):
  with patch.object(Path,'open',side_effect=PermissionError('synthetic write denial')):result=self.persist()
  self.assertEqual(result['status'],'partial');self.assertEqual(result['artifacts_written'],0)
 def test_later_write_denial_retains_partial_counts(self):
  original=Path.open
  def deny(path,*args,**kwargs):
   if path.name=='plan-records.json':raise PermissionError('synthetic write denial')
   return original(path,*args,**kwargs)
  with patch.object(Path,'open',deny):result=self.persist()
  self.assertEqual(result['status'],'partial');self.assertEqual(result['artifacts_written'],1)
  self.assertFalse(result['disk_records_verified']);self.assertFalse((self.output/'receipt.json').exists())
 def test_existing_incident_never_creates_output(self):
  self.relay.incident=True
  self.assertEqual(self.persist()['status'],'incident');self.assertFalse(self.output.exists())
 def test_disk_corruption_detected_after_writes(self):
  original=Path.read_bytes
  def corrupt(path):
   data=original(path)
   return data.replace(b'a synthetic shape',b'different shape') if path.name=='records.json' else data
  with patch.object(Path,'read_bytes',corrupt):result=self.persist()
  self.assertEqual(result['status'],'partial');self.assertFalse(result['disk_records_verified'])
if __name__=='__main__':unittest.main()
