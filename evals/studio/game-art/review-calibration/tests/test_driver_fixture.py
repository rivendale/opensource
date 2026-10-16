#!/usr/bin/env python3
"""Unchanged first-batch fixture retains its known failed floors; no provider."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
HASHES={'records.json':'03a69dcccf40835b0d458f1222ef9ab0dda58e3ee03dbae29e4d68a7722acd48','plan-records.json':'9d8cbbf5ef99298cba90cf343c6e27993be9c1fe9c16f6953f510917a4a257ec','events.jsonl':'3286eee8a79654a524ec47e7eb1d95efa0083d58ab21087c13db4b1c0c4d9bd2','receipt.json':'5303676e4f491e335e65c7acf164c03d823d5f7d9d762501cf20972f4362b9ae'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixture',type=Path);a=p.parse_args();FIXTURE=a.fixture
 if FIXTURE is None:
  print(json.dumps({'status':'fixture absent','reason':'operator-held raw first-batch fixture not supplied','provider_calls':0}));return
 if not FIXTURE.is_dir():raise SystemExit('Explicit fixture path does not exist')
 manifest={}
 for line in (HERE/'tests/fixtures/first-batch/SHA256SUMS').read_text().splitlines():
  digest,name=line.split(maxsplit=1);manifest[name.lstrip('* ')]=digest
 if manifest!=HASHES:raise ValueError('committed fixture manifest differs from pinned hashes')
 for name,digest in HASHES.items():assert hashlib.sha256((FIXTURE/name).read_bytes()).hexdigest()==digest
 result=subprocess.run([sys.executable,str(HERE/'score.py'),str(FIXTURE/'records.json')],capture_output=True,text=True);score=json.loads(result.stdout)
 assert result.returncode==1
 assert {r['id'] for r in score['rules'] if not r['pass']}=={'names_drawn','packet_agree','feature_all','feature_each'}
 compare=subprocess.run([sys.executable,str(HERE/'compare_batches.py'),str(FIXTURE/'records.json'),str(FIXTURE/'records.json')],capture_output=True,text=True)
 assert compare.returncode==0;summary=json.loads(compare.stdout.splitlines()[-1]);assert summary['same_class']==14 and not summary['gained_yes'] and not summary['lost_yes']
 import importlib.util
 spec=importlib.util.spec_from_file_location('driver',HERE/'driver.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 events=[json.loads(line) for line in (FIXTURE/'events.jsonl').read_text().splitlines()]
 records,plans=m.derive_records(events,m.build_plan(HERE))
 assert records==json.loads((FIXTURE/'records.json').read_text()) and plans==json.loads((FIXTURE/'plan-records.json').read_text())
 changed=[dict(e) for e in events];changed[2]['content']='{"name":"changed recorded reply"}'
 altered,_=m.derive_records(changed,m.build_plan(HERE));assert altered!=records
 changed=[dict(e) for e in events];changed[1]['pair']=1
 try:m.derive_records(changed,m.build_plan(HERE))
 except ValueError:pass
 else:raise AssertionError('mixed event pairs accepted')
 print('Unchanged first-batch fixture: score exit 1 with known four failed floors; same-batch comparison exit 0')
if __name__=='__main__':main()
