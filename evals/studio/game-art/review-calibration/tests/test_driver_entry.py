#!/usr/bin/env python3
"""Synthetic inherited-descriptor intake and a structural second-path refusal."""
import ast,importlib.util,unittest,tempfile,subprocess,sys,json
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parents[1];ROOT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('driver',HERE/'driver.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
import common
class EntryTests(unittest.TestCase):
 def test_one_helper_validates_synthetic_intake(self):
  with patch.object(common.os,'read',return_value=b'SYNTHETIC-ENTRY-MARKER\n') as read:
   self.assertEqual(common.read_key_fds({'api.anthropic.com':9}),{'api.anthropic.com':b'SYNTHETIC-ENTRY-MARKER'});read.assert_called_once_with(9,4097)
  for data in [b'',b'x'*4097,b'bad value',b'bad"quote',b'bad\\slash',b'\x00']:
   with self.subTest(data_length=len(data)),patch.object(common.os,'read',return_value=data):
    with self.assertRaises(ValueError):common.read_key_fds({'api.anthropic.com':9})
  for fds in [{'api.anthropic.com':True},{'api.anthropic.com':2},[]]:
   with patch.object(common.os,'read',side_effect=AssertionError('invalid mapping read')):
    with self.assertRaises(ValueError):common.read_key_fds(fds)
 def test_driver_builds_relay_through_shared_helper_only(self):
  with patch.object(common.os,'read',return_value=b'SYNTHETIC-ENTRY-MARKER'),patch.object(m,'Relay') as relay:
   m.build_relay(Path('/unused-synthetic-socket'),{'api.anthropic.com':9})
   self.assertEqual(relay.call_args.args[2],{'api.anthropic.com':b'SYNTHETIC-ENTRY-MARKER'});self.assertEqual(relay.call_args.args[4],116)
  with patch.object(common.os,'read',side_effect=AssertionError('wrong host read')):
   with self.assertRaises(ValueError):m.build_relay(Path('/unused'),{'other.invalid':9})
 def source_repo(self,root):
  source=root/'evals/studio/game-art/review-calibration';source.mkdir(parents=True);runner=root/'skills/studio/runner';runner.mkdir(parents=True)
  (source/'driver.py').write_text((HERE/'driver.py').read_text());(runner/'reviewer.py').write_text('')
  (runner/'proxy.py').write_text('class Relay: pass\n');(runner/'common.py').write_text('def read_key_fds(value): return {}\n')
  for args in [['init','-q'],['add','.'],['-c','user.name=fixture','-c','user.email=fixture@example.invalid','commit','-qm','fixture']]:subprocess.run(['git',*args],cwd=root,check=True,capture_output=True)
  return source,runner
 def test_source_identity_refuses_untracked_and_modified_code(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);source,runner=self.source_repo(root);self.assertEqual(len(m.source_identity(root)),40)
   for name in ('extra.py','extra.pyc','extra.so'):
    path=runner/name;path.write_bytes(b'synthetic')
    with self.subTest(name=name),self.assertRaises(ValueError):m.source_identity(root)
    path.unlink()
   (runner/'output.json').write_text('{}');self.assertEqual(len(m.source_identity(root)),40)
   (runner/'reviewer.py').write_text('# modified tracked code')
   with self.assertRaises(ValueError):m.source_identity(root)
 def test_live_entry_rejects_untracked_module_before_runner_import(self):
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);source,runner=self.source_repo(root);marker=root/'imported'
   (runner/'reviewer.py').write_text('import unexpected_module\n');subprocess.run(['git','add','.'],cwd=root,check=True,capture_output=True);subprocess.run(['git','-c','user.name=fixture','-c','user.email=fixture@example.invalid','commit','-qm','import fixture'],cwd=root,check=True,capture_output=True)
   (runner/'unexpected_module.py').write_text('from pathlib import Path\nPath('+repr(str(marker))+').write_text("import happened")\n')
   result=subprocess.run([sys.executable,str(source/'driver.py'),'--run'],cwd=root,capture_output=True,text=True,check=False)
   self.assertEqual(result.returncode,2);self.assertEqual(json.loads(result.stdout)['reason'],'ValueError');self.assertFalse(marker.exists())
 def test_no_second_descriptor_or_key_intake(self):
  tree=ast.parse((HERE/'driver.py').read_text());runner=ast.parse((ROOT/'skills/studio/runner/run.py').read_text())
  self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='read_key_fds' for n in ast.walk(runner)))
  self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='read_key_fds' for n in ast.walk(tree)))
  for node in ast.walk(tree):
   if isinstance(node,(ast.Import,ast.ImportFrom)):
    self.assertNotIn(getattr(node,'module',None),('os','io','socket','http.client','requests'))
    if isinstance(node,ast.Import):self.assertFalse(any(a.name in ('os','io','socket','http.client','requests') for a in node.names))
   if isinstance(node,ast.Call):
    name=node.func.id if isinstance(node.func,ast.Name) else getattr(node.func,'attr','')
    self.assertNotIn(name,('fdopen','read','readinto','openfd','getenv','get_environ','fromfd','dup','dup2'))
    if name=='open':self.assertTrue(isinstance(node.func,ast.Attribute));self.assertTrue(node.args and isinstance(node.args[0],ast.Constant) and node.args[0].value in ('xb',))
if __name__=='__main__':unittest.main()
