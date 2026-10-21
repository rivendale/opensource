#!/usr/bin/env python3
"""Real reviewer + trusted Relay method, fake HTTPS only; no socket/key/provider."""
import hashlib,importlib.util,json,sys,threading,unittest,tempfile,subprocess
from pathlib import Path
from contextlib import nullcontext
from unittest.mock import patch
HERE=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('driver',HERE/'driver.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
import proxy
def compatible_preflight(commit='a'*40):
 return {'mode':'preflight','status':'compatible','model':m.SETTINGS['model'],'settings':dict(m.SETTINGS),'source_commit':commit,
         'run_list_sha256':m.INPUT_SHA256['RUN-LIST-opus55-notemp.md'],'requests_used':1,
         'usage':{'prompt_tokens':3,'completion_tokens':1,'total_tokens':4},'spend_usd':'0.000032','error':None}
class CollectTests(unittest.TestCase):
 def collect(self,mode='valid',execute=None):
  calls=[];marker=b'SYNTHETIC-CALIBRATION-MARKER'
  relay=object.__new__(proxy.Relay);relay.review_temperature=None;relay.model=m.SETTINGS['model'];relay.routes={(m.SETTINGS['host'],m.SETTINGS['path']):'model'};relay.keys={m.SETTINGS['host']:marker};relay.calls=0;relay.turn_limit=116;relay.context=None;relay.lock=threading.Lock();relay.log=[];relay.incident=False;relay.limit_hit=False
  class Response:
   status=400 if mode in ('reject-temperature','reject-seed','provider-error','error-key','error-encoded-key','error-nonjson','error-oversize') else 200
   def read(self,_):
    req=calls[-1];first=req['max_tokens']==128;n=6 if len(calls)<=84 else 5
    text=json.dumps({'name':'a synthetic geometric shape'} if first else {'features':[False]*n})
    usage={'prompt_tokens':10,'completion_tokens':2,'total_tokens':12};model=m.SETTINGS['model']
    if mode=='bad-json':text='not json'
    if mode=='empty':text=''
    if mode=='schema':text='{"name":"shape","extra":true}'
    if mode=='late-schema' and len(calls)==4:text='{"features":[1,0]}'
    if mode in ('key','decoded-key'):text=marker.decode()
    if mode=='usage':usage={}
    if mode=='usage-total':usage['total_tokens']=11
    if mode=='usage-negative':usage.update(prompt_tokens=-1,total_tokens=1)
    if mode=='usage-bool':usage.update(prompt_tokens=True,total_tokens=3)
    if mode=='usage-cache':usage['prompt_tokens_details']={'cached_tokens':1}
    if mode=='model':model='different-model'
    if mode=='cost':usage={'prompt_tokens':300000,'completion_tokens':2,'total_tokens':300002}
    data=json.dumps({'model':model,'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':text,**({'refusal':'synthetic refusal'} if mode=='refusal' else {})}}],'usage':usage}).encode()
    if mode in ('provider-error','provider-error-200','error-key','error-encoded-key'):
     data=json.dumps({'error':{'type':'invalid_request_error','message':marker.decode() if mode not in ('provider-error','provider-error-200') else 'Synthetic setting rejected'},'unrelated':'NEVER-RETAIN-THIS'}).encode()
    if mode=='wire-json':data=b'not JSON transport'
    if mode=='error-nonjson':data=b'<html>SYNTHETIC RAW BODY NOT RETAINED</html>'
    if mode=='error-oversize':data=b'x'*(proxy.MAX_BODY+1)
    if mode=='error-encoded-key':data=data.replace(marker,b''.join(('\\u%04x'%c).encode() for c in marker))
    if mode=='decoded-key':data=data.replace(marker,b''.join(('\\u%04x'%c).encode() for c in marker))
    return data
  class HTTPS:
   def __init__(self,host,port,**kwargs):assert(host,port)==('api.anthropic.com',443)
   def request(self,method,path,payload,headers):
    req=json.loads(payload);assert set(req)=={'model','messages','stream','seed','max_tokens'}|({'temperature'} if mode=='ordinary' else set()) and req['seed']==0 and req['stream'] is False;assert mode!='ordinary' or req['temperature']==0;assert path==m.SETTINGS['path'];calls.append(req)
    for message in req['messages']:
     text=message.get('content')
     if isinstance(text,str):assert 'answers.json' not in text and 'images/' not in text and not any(word in text.lower().split() for word in ['coin','key','potion','heart','mushroom','boot'])
    if mode=='http':raise OSError('synthetic network failure')
   def getresponse(self):return Response()
   def close(self):pass
  plan_context=nullcontext()
  if mode=='overflow':
   plan=m.build_plan();plan.append(dict(plan[-1],pair=58));plan_context=patch.object(m,'build_plan',return_value=plan)
  with patch.object(proxy.http.client,'HTTPSConnection',HTTPS),plan_context:result=(execute or m.collect_pairs)(relay)
  self.relay=relay
  return result,calls
 def test_full_batch_116_requests_in_order(self):
  r,calls=self.collect();self.assertEqual(r['status'],'collected');self.assertEqual(len(calls),116);self.assertEqual(r['pairs_completed'],58);self.assertEqual(len(r['records']),42);self.assertEqual(len(r['plan_records']),16);self.assertEqual([c['max_tokens'] for c in calls],[128,256]*58)
  self.assertTrue(all(e['scale']==16 for e in r['events'] if e['kind'].endswith('-request')));self.assertEqual(r['spend_usd'],'0.00928')
 def test_full_batch_persisted_and_consumed_from_disk(self):
  result,_=self.collect()
  with tempfile.TemporaryDirectory() as directory:
   output=Path(directory)/'batch';stage=m.persist_collection(self.relay,result,output)
   self.assertTrue(stage['disk_records_verified'])
   original_bytes=(output/'records.json').read_bytes();(output/'records.json').write_bytes(original_bytes.replace(b'a synthetic geometric shape',b'changed shape'))
   with patch.object(m.subprocess,'run',side_effect=AssertionError('corrupt disk batch was scored')):
    refused=m.consume_written(self.relay,result,stage,output,output/'records.json')
   self.assertEqual(refused['status'],'partial');self.assertIsNone(refused['score_exit']);(output/'records.json').write_bytes(original_bytes)
   real_run=subprocess.run
   with patch.object(m.subprocess,'run',wraps=real_run) as consumer_calls:
    consumed=m.consume_written(self.relay,result,stage,output,output/'records.json')
   self.assertEqual([Path(call.args[0][1]).name for call in consumer_calls.call_args_list],['score.py','compare_batches.py'])
   self.assertEqual(consumed['status'],'consumed');self.assertEqual(consumed['score_exit'],1);self.assertEqual(consumed['compare_exit'],0)
   expected=subprocess.run([sys.executable,str(HERE/'score.py'),str(output/'records.json')],capture_output=True,check=False)
   self.assertEqual((output/'score.stdout.json').read_bytes(),expected.stdout)
   self.assertEqual(hashlib.sha256((output/'score.stdout.json').read_bytes()).hexdigest(),consumed['sha256']['score.stdout.json'])
   self.assertFalse(consumed['review_gate']);self.assertFalse((output/'receipt.json').exists())
   # Existing scorer output must never be replaced on a repeat invocation.
   again=m.consume_written(self.relay,result,stage,output,output/'records.json');self.assertEqual(again['status'],'partial')
   self.assertEqual((output/'score.stdout.json').read_bytes(),expected.stdout)
   incident_output=Path(directory)/'incident-batch';incident_stage=m.persist_collection(self.relay,result,incident_output)
   poisoned=subprocess.CompletedProcess([],0,b'SYNTHETIC-CALIBRATION-MARKER',b'')
   with patch.object(m.subprocess,'run',return_value=poisoned):
    incident=m.consume_written(self.relay,result,incident_stage,incident_output,output/'records.json')
   self.assertEqual(incident['status'],'incident');self.assertEqual(list(incident_output.iterdir()),[])
 def test_partial_never_invokes_disk_consumers(self):
  result,_=self.collect('late-schema')
  with tempfile.TemporaryDirectory() as directory:
   output=Path(directory)/'batch';stage=m.persist_collection(self.relay,result,output)
   with patch.object(m.subprocess,'run',side_effect=AssertionError('partial batch was scored')):
    consumed=m.consume_written(self.relay,result,stage,output,output/'records.json')
   self.assertEqual(consumed['status'],'partial');self.assertIsNone(consumed['score_exit'])
 def test_bad_reply_http_usage_model_cost_stop_without_retry(self):
  for mode in ['reject-temperature','reject-seed','bad-json','http','usage','usage-total','usage-negative','usage-bool','usage-cache','model','cost','refusal','empty','schema']:
   with self.subTest(mode=mode):
    r,calls=self.collect(mode);self.assertEqual(r['status'],'partial');self.assertEqual(len(calls),1);self.assertEqual(r['pairs_completed'],0)
    if mode.startswith('usage') or mode in ('http','model'):self.assertTrue(r['usage_unverified'])
 def test_extra_planned_pair_stops_before_request_117(self):
  r,calls=self.collect('overflow');self.assertEqual(r['status'],'partial');self.assertEqual(len(calls),116);self.assertEqual(r['requests_used'],116);self.assertEqual(r['pairs_completed'],58)
 def test_consumer_errors_and_unwritable_score_never_finish(self):
  result,_=self.collect()
  with tempfile.TemporaryDirectory() as directory:
   for label,score_exit,compare_exit in [('scorer-error',2,0),('comparison-error',1,1)]:
    output=Path(directory)/label;stage=m.persist_collection(self.relay,result,output)
    responses=[subprocess.CompletedProcess([],score_exit,b'whole stdout\n',b'error'),subprocess.CompletedProcess([],compare_exit,b'comparison output',b'')]
    with patch.object(m.subprocess,'run',side_effect=responses):consumed=m.consume_written(self.relay,result,stage,output,output/'records.json')
    self.assertEqual(consumed['status'],'partial');self.assertEqual(consumed['score_exit'],score_exit);self.assertEqual(consumed['compare_exit'],compare_exit)
    self.assertEqual((output/'score.stdout.json').read_bytes(),b'whole stdout\n');self.assertFalse(consumed['review_gate'])
   output=Path(directory)/'write-denied';stage=m.persist_collection(self.relay,result,output);original=Path.open
   def deny(path,*args,**kwargs):
    if path.name=='score.stdout.json':raise PermissionError('synthetic score write denial')
    return original(path,*args,**kwargs)
   with patch.object(Path,'open',deny):consumed=m.consume_written(self.relay,result,stage,output,output/'records.json')
   self.assertEqual(consumed['status'],'partial');self.assertEqual(consumed['reason'],'PermissionError');self.assertFalse((output/'score.stdout.json').exists())
 def test_late_failure_preserves_only_completed_pairs_and_usage(self):
  r,calls=self.collect('late-schema');self.assertEqual(r['status'],'partial');self.assertEqual(len(calls),4);self.assertEqual(r['pairs_completed'],1);self.assertEqual(len(r['records']),1);self.assertEqual(r['prompt_tokens'],40);self.assertEqual(r['completion_tokens'],8)
 def test_key_incident_suppresses_records_and_events(self):
  for mode in ('key','decoded-key'):
   with self.subTest(mode=mode):
    r,calls=self.collect(mode);self.assertEqual(r['status'],'incident');self.assertEqual(len(calls),1);self.assertEqual(r['records'],[]);self.assertEqual(r['events'],[])
if __name__=='__main__':unittest.main()
