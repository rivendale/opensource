"""Synthetic compatibility and redacted provider-error controls; no provider or keys."""
import copy, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import test_driver_collect as fixture
m=fixture.m

class CompatibilityTests(unittest.TestCase):
 def check(self,mode='valid'):
  harness=fixture.CollectTests()
  def execute(relay):
   relay.turn_limit=1
   return m.preflight(relay,'a'*40)
  with patch.object(m.reviewer,'neutral_views',side_effect=AssertionError('preflight rendered an image')):
   report,calls=harness.collect(mode,execute=execute)
  self.relay=harness.relay
  return report,calls
 def test_preflight_one_text_request_registered_settings_and_cost(self):
  report,calls=self.check()
  self.assertEqual(report['status'],'compatible');self.assertEqual(len(calls),1)
  self.assertNotIn('temperature',calls[0]);self.assertEqual(calls[0]['seed'],0)
  self.assertEqual(calls[0]['model'],'claude-opus-5-5')
  self.assertTrue(all(isinstance(x['content'],str) for x in calls[0]['messages']))
  self.assertLessEqual(calls[0]['max_tokens'],8)
  self.assertEqual(report['usage'],{'prompt_tokens':10,'completion_tokens':2,'total_tokens':12})
  self.assertEqual(report['spend_usd'],'0.00008')
 def test_rejected_or_incompatible_preflight_never_authorizes_run(self):
  for mode in ['provider-error','error-nonjson','error-oversize','model','usage','refusal','empty','bad-json']:
   with self.subTest(mode=mode):
    report,calls=self.check(mode);self.assertEqual(report['status'],'rejected');self.assertEqual(len(calls),1)
    with tempfile.TemporaryDirectory() as directory:
     output=Path(directory)/'preflight';m.persist_preflight(self.relay,report,output)
     with self.assertRaises(ValueError):m.load_preflight(output/'receipt.json','a'*40)
 def test_provider_error_status_and_only_error_fields_survive_in_events_and_receipt(self):
  harness=fixture.CollectTests()
  def execute(relay):
   with tempfile.TemporaryDirectory() as directory:
    output=Path(directory)/'batch';baseline=Path(directory)/'baseline.json';baseline.write_text('[]')
    report=m.run_batch(relay,output,baseline,'a'*40,preflight=fixture.compatible_preflight())
    receipt=json.loads((output/'receipt.json').read_text());events=(output/'events.jsonl').read_text()
    expected={'http_status':400,'type':'invalid_request_error','message':'Synthetic setting rejected'}
    self.assertEqual(receipt['error'],expected);self.assertIn('provider-stop',events)
    self.assertIn('Synthetic setting rejected',events);self.assertNotIn('NEVER-RETAIN-THIS',events+json.dumps(receipt))
    self.assertEqual(report['status'],'partial')
    return report
  _,calls=harness.collect('provider-error',execute=execute);self.assertEqual(len(calls),1)
 def test_decoded_error_key_is_redacted_and_never_written(self):
  for mode in ['error-key','error-encoded-key']:
   report,calls=self.check(mode);self.assertEqual(report['status'],'incident');self.assertEqual(len(calls),1)
   self.assertNotIn('SYNTHETIC-CALIBRATION-MARKER',json.dumps(report))
   with tempfile.TemporaryDirectory() as directory:
    output=Path(directory)/'preflight';m.persist_preflight(self.relay,report,output)
    for path in output.iterdir():self.assertNotIn('SYNTHETIC-CALIBRATION-MARKER',path.read_text())
 def test_preflight_inventory_and_identity_are_required(self):
  report,_=self.check()
  with tempfile.TemporaryDirectory() as directory:
   output=Path(directory)/'preflight';m.persist_preflight(self.relay,report,output)
   self.assertEqual(m.load_preflight(output/'receipt.json','a'*40)['status'],'compatible')
   for field,value in [('source_commit','b'*40),('model','wrong-model'),('settings',dict(m.SETTINGS,seed=9)),('spend_usd','0')]:
    bad=copy.deepcopy(report);bad[field]=value
    with self.assertRaises(ValueError):m.validate_preflight(bad,'a'*40)
   events=output/'events.jsonl';events.write_text('changed')
   with self.assertRaises(ValueError):m.load_preflight(output/'receipt.json','a'*40)
 def test_missing_or_rejected_preflight_refuses_batch_before_transport(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);baseline=root/'baseline.json';baseline.write_text('[]')
   for value in [None,dict(fixture.compatible_preflight(),status='rejected')]:
    with patch.object(m,'collect_pairs',side_effect=AssertionError('batch called without valid preflight')):
     result=m.run_batch(None,root/'batch',baseline,'a'*40,preflight=value)
    self.assertEqual(result['status'],'partial');self.assertFalse((root/'batch').exists())
 def test_ordinary_reviewer_keeps_temperature_zero(self):
  def execute(relay):
   relay.review_temperature=0
   return relay.review_request([{'role':'user','content':'ping'}],8)
  _,calls=fixture.CollectTests().collect('ordinary',execute=execute)
  self.assertEqual(calls[0]['temperature'],0)

if __name__=='__main__':unittest.main()
