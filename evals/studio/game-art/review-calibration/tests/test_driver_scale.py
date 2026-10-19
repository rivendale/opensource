#!/usr/bin/env python3
"""T38 policy and recorded-scale regressions; synthetic transport, no provider."""
import copy, hashlib, json, struct, subprocess, tempfile, unittest, zlib
from pathlib import Path
import test_driver_batch as batch_module
m = batch_module.m

reviewer = m.reviewer

def png(width, height):
 def chunk(kind, data):
  return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
 pixels = b''.join(b'\0' + b''.join(bytes((x % 256, y % 256, 91, 128 if x % 2 else 255)) for x in range(width)) for y in range(height))
 return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(pixels)) + chunk(b'IEND', b'')

class ScaleTests(unittest.TestCase):
 def test_calibration_policy_and_ordinary_default(self):
  image = png(16, 16)
  self.assertEqual(reviewer.view_metadata(image)['scale'], 8)
  self.assertEqual(reviewer.view_metadata(image, policy=reviewer.ViewPolicy.CALIBRATION)['dimensions'], [256, 256])
  self.assertEqual(m.SETTINGS['scale'], 16)
  with self.assertRaises(reviewer.ReviewError):
   reviewer.view_metadata(image, policy=16)

 def test_pixels_backgrounds_non_square_and_512_bound(self):
  image = png(16, 24)
  for view, background in zip(reviewer.neutral_views(image, policy=reviewer.ViewPolicy.CALIBRATION), ('#808080', '#dddddd')):
   self.assertEqual(reviewer.png_dimensions(view), (256, 384))
   native = subprocess.check_output(['convert', 'png:-', '-background', background, '-alpha', 'remove', '-alpha', 'off', '-strip', 'PNG32:-'], input=image)
   raw = subprocess.check_output(['convert', 'png:-', '-depth', '8', 'rgba:-'], input=native)
   expected = b''.join(b''.join(raw[(y*16+x)*4:(y*16+x+1)*4]*16 for x in range(16))*16 for y in range(24))
   actual = subprocess.check_output(['convert', 'png:-', '-depth', '8', 'rgba:-'], input=view)
   self.assertEqual(actual, expected)
  for size, factor in ((32,16), (33,15), (65,7), (256,2), (512,1)):
   metadata = reviewer.view_metadata(png(size,size), policy=reviewer.ViewPolicy.CALIBRATION)
   self.assertEqual(metadata['scale'], factor)
   self.assertLessEqual(max(metadata['dimensions']), 512)

 def test_receipt_and_hash_consistent_events_refuse_wrong_scale(self):
  batch = batch_module.BatchTests()
  batch.setUp()
  try:
   report, output, _ = batch.batch()
   self.assertEqual(report['status'], 'complete')
   receipt = json.loads((output/'receipt.json').read_text())
   changed = copy.deepcopy(receipt); changed['settings']['scale'] = 8
   (output/'receipt.json').write_text(json.dumps(changed))
   with self.assertRaises(ValueError): m.verify_receipt(output)
   events = [json.loads(line) for line in (output/'events.jsonl').read_text().splitlines()]
   request = next(e for e in events if e['kind'].endswith('-request'))
   request['scale'] = 8
   body = ''.join(json.dumps(e)+'\n' for e in events).encode()
   (output/'events.jsonl').write_bytes(body)
   receipt['sha256']['events.jsonl'] = hashlib.sha256(body).hexdigest()
   (output/'receipt.json').write_text(json.dumps(receipt))
   with self.assertRaises(ValueError): m.verify_receipt(output)
  finally:
   batch.doCleanups()

if __name__ == '__main__': unittest.main()
