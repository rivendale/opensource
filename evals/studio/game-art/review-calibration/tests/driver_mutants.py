#!/usr/bin/env python3
"""Guard sensitivity for implemented components; component mutations; full contract coverage is still pending."""
import json,shutil,subprocess,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parents[1];ROOT=HERE.parents[3]
MUTANTS=[
 ('settings','driver.py',"if settings!=SETTINGS or any(type(settings[k]) is not type(v) for k,v in SETTINGS.items()):","if False:",'test_driver_plan.py'),
 ('prompt-filename','@reviewer',"Name what you see","images/e62f4a63.png Name what you see",'test_driver_collect.py'),
 ('retry','driver.py'," except Exception as error:\n"," except Exception as error:\n  if not getattr(relay,'_retried',False):\n   relay._retried=True;relay.calls=0;return collect_pairs(relay,settings,here)\n",'test_driver_collect.py'),
 ('repeat-order','driver.py'," for repeat in range(3):\n  for image in images:"," for image in images:\n  for repeat in range(3):",'test_driver_plan.py'),
 ('invented-record','driver.py',"name=name['name'],features=features['features']","name='invented',features=features['features']",'test_driver_plan.py'),
 ('incident-suppression','driver.py'," if status=='incident':events=[];records=[];plans=[]"," if False:events=[];records=[];plans=[]",'test_driver_collect.py'),
 ('decoded-key-scan','driver.py',"if relay.output_has_key(json.dumps(event,ensure_ascii=True).encode()):","if False:",'test_driver_collect.py'),
 ('wrong-rate','driver.py',"Decimal(prompt)*3+Decimal(completion)*15","Decimal(prompt)*0+Decimal(completion)*15",'test_driver_collect.py'),
 ('mixed-batch-events','driver.py',"if [e.get('kind') for e in group]!=list(EVENT_KINDS) or any(e.get('pair')!=pair['pair'] for e in group):","if False:",'test_driver_plan.py'),
 ('output-scan','driver.py',"if relay.output_has_key(body):","if False:",'test_driver_persist.py'),
 ('existing-output','driver.py',"output.mkdir(mode=0o700,exist_ok=False)","output.mkdir(mode=0o700,exist_ok=True)",'test_driver_persist.py'),
 ('disk-readback','driver.py',"written={name:(output/name).read_bytes() for name in payloads}","written=payloads",'test_driver_persist.py'),
 ('missing-comparison','driver.py',"compared=subprocess.run([sys.executable,str(here/'compare_batches.py'),str(Path(baseline)),str(output/'records.json')],capture_output=True,timeout=30,check=False)","compared=subprocess.CompletedProcess([],0,b'',b'')",'test_driver_collect.py'),
 ('request-ceiling','driver.py',"if requests>=settings['requests'] or spend>=Decimal(settings['hard_stop_usd']):","if spend>=Decimal(settings['hard_stop_usd']):",'test_driver_collect.py'),
 ('scorer-exit-preserved','driver.py',"report['score_exit']=scored.returncode","report['score_exit']=0",'test_driver_collect.py'),
 ('consumer-error-status','driver.py',"if scored.returncode in (0,1) and compared.returncode==0:","if scored.returncode in (0,1,2) and compared.returncode==0:",'test_driver_collect.py'),
 ('copied-in-file','driver.py',"if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:","if False:",'test_driver_batch.py'),
 ('event-identity','driver.py',"if any(e.get('run_id')!=receipt['run_id'] for e in events):","if False:",'test_driver_batch.py'),
 ('single-intake','driver.py',"read_key_fds(key_fds),SETTINGS['model']","{},SETTINGS['model']",'test_driver_entry.py'),
 ('receipt-output-scan','driver.py',"if relay.output_has_key(body):\n  relay.incident=True\n  for name in ARTIFACT_NAMES:","if False:\n  relay.incident=True\n  for name in ARTIFACT_NAMES:",'test_driver_batch.py')]
def main():
 structural='--structural-only' in sys.argv
 selected=[m for m in MUTANTS if not structural or m[4] in ('test_driver_plan.py','test_driver_persist.py','test_driver_entry.py')]
 for test in sorted({m[4] for m in selected}):
  result=subprocess.run([sys.executable,str(HERE/'tests'/test)],capture_output=True,timeout=30)
  if result.returncode:raise RuntimeError('unmodified baseline must pass: '+test)
 results=[]
 for name,path,old,new,test in selected:
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);calib=root/HERE.relative_to(ROOT);calib.parent.mkdir(parents=True)
   shutil.copytree(HERE,calib,ignore=shutil.ignore_patterns('__pycache__'))
   shutil.copytree(HERE.parent/'review-plans',calib.parent/'review-plans',ignore=shutil.ignore_patterns('__pycache__'))
   runner=root/'skills/studio/runner';runner.parent.mkdir(parents=True);shutil.copytree(ROOT/'skills/studio/runner',runner,ignore=shutil.ignore_patterns('__pycache__'))
   target=runner/'reviewer.py' if path=='@reviewer' else calib/path;text=target.read_text()
   if old not in text:raise RuntimeError('mutation target missing: '+name)
   target.write_text(text.replace(old,new,1));result=subprocess.run([sys.executable,str(calib/'tests'/test)],capture_output=True,text=True,timeout=30)
   if result.returncode==0 or 'SyntaxError' in result.stderr or 'ImportError' in result.stderr:raise RuntimeError('mutation not killed by behavior: '+name)
   results.append(dict(mutation=name,behavioral_test_failed=True))
 print(json.dumps({'mutants':results,'component_mutations':len(results),'renderer_dependent_mutations':'not run' if structural else 'run','remaining_contract':['independent review and operator execution; no live validation claimed'],'real_provider_calls':0},indent=2))
if __name__=='__main__':main()
