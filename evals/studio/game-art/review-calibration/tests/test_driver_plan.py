#!/usr/bin/env python3
"""Fixed-run-list tests written before the batch driver."""
import copy,hashlib,importlib.util,json,unittest,tempfile,shutil
from unittest.mock import patch
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('driver',HERE/'driver.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PlanTests(unittest.TestCase):
 def test_exact_repeat_major_58_pair_order(self):
  pairs=m.build_plan(HERE);self.assertEqual(len(pairs),58);self.assertEqual([p['pair'] for p in pairs],list(range(58)))
  self.assertEqual([p['repeat'] for p in pairs[:42]],[0]*14+[1]*14+[2]*14)
  self.assertEqual([p['image'] for p in pairs[:14]],[p['image'] for p in pairs[14:28]])
  self.assertTrue(all(p['plan'] is None for p in pairs[:42]));self.assertTrue(all(p['repeat']==0 and p['plan'] for p in pairs[42:]))
 def test_no_answer_truth_in_reviewer_items(self):
  for pair in m.build_plan(HERE):self.assertEqual(set(pair['item']),{'file','features','subject_words'})
 def test_fixed_settings_checked_without_transport(self):
  self.assertIsNone(m.validate_settings(m.SETTINGS))
  for field in m.SETTINGS:
   changed=copy.deepcopy(m.SETTINGS);changed[field]='wrong'
   with self.assertRaises(ValueError):m.validate_settings(changed)
 def test_small_synthetic_fixture_reconstructs_and_refuses_reordering(self):
  data=json.loads((HERE/'tests/fixtures/synthetic-pair.json').read_text());records,plans=m.derive_records(data['events'],[data['pair']]);self.assertEqual(records,[data['record']]);self.assertEqual(plans,[])
  data['events'][0]['pair']=1
  with self.assertRaises(ValueError):m.derive_records(data['events'],[data['pair']])
 def test_registered_opus_model_and_fixed_other_settings(self):
  self.assertEqual(m.SETTINGS,{'model':'claude-opus-5-5','host':'api.anthropic.com','path':'/v1/chat/completions','temperature':None,'seed':0,'prompt_cache':False,'scale':16,'requests':116,'hard_stop_usd':'5.00','review_max_tokens':1024})
  self.assertIn('RUN-LIST-opus55-room.md',m.INPUT_SHA256)
 def test_hash_consistent_list_with_another_model_is_refused(self):
  with tempfile.TemporaryDirectory() as directory:
   target=Path(directory)/'calibration';shutil.copytree(HERE,target)
   shutil.copytree(HERE.parent/'review-plans',target.parent/'review-plans')
   path=target/'RUN-LIST-opus55-room.md'
   path.write_text(path.read_text().replace('| reviewer model | `claude-opus-5-5`','| reviewer model | `different-model`'))
   hashes=dict(m.INPUT_SHA256,**{'RUN-LIST-opus55-room.md':hashlib.sha256(path.read_bytes()).hexdigest()})
   with patch.object(m,'INPUT_SHA256',hashes):
    with self.assertRaises(ValueError):m.build_plan(target)
 def test_unknown_setting_refused(self):
  changed=dict(m.SETTINGS,extra='unreviewed')
  with self.assertRaises(ValueError):m.validate_settings(changed)
if __name__=='__main__':unittest.main()
