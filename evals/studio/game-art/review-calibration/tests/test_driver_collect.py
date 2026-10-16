#!/usr/bin/env python3
"""Real reviewer + trusted Relay method, fake HTTPS only; no socket/key/provider."""
import hashlib,importlib.util,json,sys,threading,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parents[1];spec=importlib.util.spec_from_file_location('driver',HERE/'driver.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
import proxy
class CollectTests(unittest.TestCase):
 def collect(self,mode='valid'):
  calls=[];marker=b'SYNTHETIC-CALIBRATION-MARKER'
  relay=object.__new__(proxy.Relay);relay.model=m.SETTINGS['model'];relay.routes={(m.SETTINGS['host'],m.SETTINGS['path']):'model'};relay.keys={m.SETTINGS['host']:marker};relay.calls=0;relay.turn_limit=116;relay.context=None;relay.lock=threading.Lock();relay.log=[];relay.incident=False;relay.limit_hit=False
  class Response:
   status=200
   def read(self,_):
    req=calls[-1];first=req['max_tokens']==128;n=6 if len(calls)<=84 else 5
    text=json.dumps({'name':'a synthetic geometric shape'} if first else {'features':[False]*n})
    usage={'prompt_tokens':10,'completion_tokens':2,'total_tokens':12};model=m.SETTINGS['model']
    if mode=='bad-json':text='not json'
    if mode=='empty':text=''
    if mode=='schema':text='{"name":"shape","extra":true}'
    if mode=='late-schema' and len(calls)==4:text='{"features":[1,0]}'
    if mode=='key':text=marker.decode()
    if mode=='usage':usage={}
    if mode=='model':model='different-model'
    if mode=='cost':usage={'prompt_tokens':400000,'completion_tokens':2,'total_tokens':400002}
    return json.dumps({'model':model,'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':text,**({'refusal':'synthetic refusal'} if mode=='refusal' else {})}}],'usage':usage}).encode()
  class HTTPS:
   def __init__(self,host,port,**kwargs):assert(host,port)==('api.anthropic.com',443)
   def request(self,method,path,payload,headers):
    req=json.loads(payload);assert set(req)=={'model','messages','stream','temperature','seed','max_tokens'} and req['temperature']==req['seed']==0 and req['stream'] is False;assert path==m.SETTINGS['path'];calls.append(req)
    for message in req['messages']:
     text=message.get('content')
     if isinstance(text,str):assert 'answers.json' not in text and 'images/' not in text and not any(word in text.lower().split() for word in ['coin','key','potion','heart','mushroom','boot'])
    if mode=='http':raise OSError('synthetic network failure')
   def getresponse(self):return Response()
   def close(self):pass
  with patch.object(proxy.http.client,'HTTPSConnection',HTTPS):result=m.collect_pairs(relay)
  return result,calls
 def test_full_batch_116_requests_in_order(self):
  r,calls=self.collect();self.assertEqual(r['status'],'completed');self.assertEqual(len(calls),116);self.assertEqual(r['pairs_completed'],58);self.assertEqual(len(r['records']),42);self.assertEqual(len(r['plan_records']),16);self.assertEqual([c['max_tokens'] for c in calls],[128,256]*58)
  self.assertTrue(all(e['scale']==8 for e in r['events'] if e['kind'].endswith('-request')));self.assertEqual(r['spend_usd'],'0.00696')
 def test_bad_reply_http_usage_model_cost_stop_without_retry(self):
  for mode in ['bad-json','http','usage','model','cost','refusal','empty','schema']:
   with self.subTest(mode=mode):
    r,calls=self.collect(mode);self.assertEqual(r['status'],'partial');self.assertEqual(len(calls),1);self.assertEqual(r['pairs_completed'],0)
 def test_late_failure_preserves_only_completed_pairs_and_usage(self):
  r,calls=self.collect('late-schema');self.assertEqual(r['status'],'partial');self.assertEqual(len(calls),4);self.assertEqual(r['pairs_completed'],1);self.assertEqual(len(r['records']),1);self.assertEqual(r['prompt_tokens'],40);self.assertEqual(r['completion_tokens'],8)
 def test_key_incident_suppresses_records_and_events(self):
  r,calls=self.collect('key');self.assertEqual(r['status'],'incident');self.assertEqual(len(calls),1);self.assertEqual(r['records'],[]);self.assertEqual(r['events'],[])
if __name__=='__main__':unittest.main()
