#!/usr/bin/env python3
"""Batch completion, copied-in artifacts, receipt scans, and partial receipts."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import test_driver_collect as fixture_collect
HERE=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('batch_driver',HERE/'driver.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class BatchTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
 def batch(self,mode='valid',name='batch-A'):
  harness=fixture_collect.CollectTests();result,_=harness.collect(mode);output=self.root/name
  baseline=self.root/(name+'-baseline.json');baseline.write_text(json.dumps(result['records']))
  report,calls=harness.collect(mode,execute=lambda relay:m.run_batch(relay,output,baseline,'a'*40,preflight=fixture_collect.compatible_preflight()))
  self.assertLessEqual(len(calls),116)
  return report,output,harness.relay
 def test_completed_disk_batch_receipt_and_strict_rows(self):
  report,output,_=self.batch();self.assertEqual(report['status'],'complete');receipt=m.verify_receipt(output)
  self.assertEqual(receipt['run_id'],'batch-A');self.assertEqual(receipt['requests_used'],116);self.assertEqual(receipt['pairs_completed'],58)
  self.assertEqual(receipt['score_exit'],1);self.assertEqual(receipt['compare_exit'],0);self.assertFalse(receipt['review_gate']);self.assertEqual(receipt['key_scan'],'passed')
  self.assertEqual(len(receipt['sha256']),4);self.assertEqual(receipt['record_counts'],{'records':42,'plan_records':16})
  self.assertTrue(all(json.loads(line)['run_id']=='batch-A' for line in (output/'events.jsonl').read_text().splitlines()))
  self.assertEqual(set(json.loads((output/'records.json').read_text())[0]),{'image','repeat','name','features'})
  self.assertEqual(len(json.loads((output/'plan-records.json').read_text())[0]),6)
 def test_recorded_model_must_match_registered_list(self):
  _,output,_=self.batch();path=output/'receipt.json';receipt=json.loads(path.read_text())
  self.assertEqual(receipt['model'],'claude-opus-5-5')
  self.assertEqual(receipt['rates']['input_per_million'],'4')
  self.assertEqual(receipt['rates']['output_per_million'],'20')
  receipt['model']='different-model';path.write_text(json.dumps(receipt))
  with self.assertRaises(ValueError):m.verify_receipt(output)
 def test_completed_receipt_requires_compatible_preflight(self):
  _,output,_=self.batch();path=output/'receipt.json';receipt=json.loads(path.read_text())
  self.assertEqual(receipt['preflight']['status'],'compatible')
  self.assertEqual(receipt['total_spend_usd'],'0.009312')
  receipt['preflight']['status']='rejected';path.write_text(json.dumps(receipt))
  with self.assertRaises(ValueError):m.verify_receipt(output)
 def test_copied_in_file_refused_by_receipt_hash(self):
  _,output,_=self.batch('late-schema');_,other,_=self.batch(name='batch-B')
  (output/'records.json').write_bytes((other/'records.json').read_bytes())
  with self.assertRaises(ValueError):m.verify_receipt(output)
 def test_event_run_id_refused_even_if_receipt_hash_is_rewritten(self):
  import hashlib
  _,output,_=self.batch();p=output/'events.jsonl';p.write_text(p.read_text().replace('batch-A','batch-B'));r=output/'receipt.json';receipt=json.loads(r.read_text());receipt['sha256']['events.jsonl']=hashlib.sha256(p.read_bytes()).hexdigest();r.write_text(json.dumps(receipt))
  with self.assertRaises(ValueError):m.verify_receipt(output)
 def test_partial_receipt_never_scores_and_repeat_never_calls_provider(self):
  report,output,relay=self.batch('late-schema');self.assertEqual(report['status'],'partial');receipt=m.verify_receipt(output);self.assertIsNone(receipt['score_exit']);self.assertEqual(receipt['pairs_completed'],1)
  with patch.object(m,'collect_pairs',side_effect=AssertionError('existing batch called provider')):
   report=m.run_batch(relay,output,output/'records.json','a'*40,preflight=fixture_collect.compatible_preflight())
  self.assertEqual(report['status'],'partial');self.assertEqual(report['reason'],'FileExistsError')
 def test_receipt_payload_key_scan_precedes_write_and_suppresses_artifacts(self):
  harness=fixture_collect.CollectTests();result,_=harness.collect();relay=harness.relay;output=self.root/'receipt-incident';stage=m.persist_collection(relay,result,output)
  consumed=m.consume_written(relay,result,stage,output,output/'records.json');result['rates_source']='SYNTHETIC-CALIBRATION-MARKER'
  report=m.finish_receipt(relay,result,stage,consumed,output,'a'*40)
  self.assertEqual(report['status'],'incident');self.assertEqual(list(output.iterdir()),[])
 def test_failed_receipt_readback_cannot_leave_complete_claim(self):
  harness=fixture_collect.CollectTests();result,_=harness.collect();relay=harness.relay;output=self.root/'bad-receipt';stage=m.persist_collection(relay,result,output)
  consumed=m.consume_written(relay,result,stage,output,output/'records.json');original=Path.read_bytes
  def corrupt(path):return b'corrupted' if path.name=='receipt.json' else original(path)
  with patch.object(Path,'read_bytes',corrupt):
   with self.assertRaises(ValueError):m.finish_receipt(relay,result,stage,consumed,output,'a'*40)
  self.assertFalse((output/'receipt.json').exists())
 def test_incident_receipt_suppresses_records(self):
  report,output,_=self.batch('decoded-key');self.assertEqual(report['status'],'incident');receipt=m.verify_receipt(output);self.assertEqual(receipt['key_scan'],'incident');self.assertEqual(receipt['sha256'],{})
  self.assertEqual({p.name for p in output.iterdir()},{'receipt.json'})
if __name__=='__main__':unittest.main()
