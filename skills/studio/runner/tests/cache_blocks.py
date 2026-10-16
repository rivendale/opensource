#!/usr/bin/env python3
"""Native block failure directions through actual handler; no socket/provider."""
import copy,email.message,io,json,sys,threading,types
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import agent,cache_api,proxy
KEY=b'SYNTHETIC-NATIVE-BLOCK-MARKER';MODEL='synthetic-model'
def check():
 request=dict(model=MODEL,messages=[{'role':'system','content':'owned'},{'role':'user','content':'brief'}],tools=agent.TOOLS,stream=False,temperature=0,seed=0)
 for block in [{'type':'text','text':'caller','cache_control':{'type':'ephemeral'}},{'type':'thinking','thinking':'caller','signature':'fixture','cache_control':{'type':'ephemeral'}}]:
  value=copy.deepcopy(request);value['messages'].append({'role':'assistant','_native_content':[block]})
  try:cache_api.native_request(value,{'system':'owned','brief':'brief'})
  except ValueError:pass
  else:raise AssertionError('native marker accepted')
 value=copy.deepcopy(request);value['messages'].append({'role':'user','content':[{'type':'text','text':'caller','cache_control':{'type':'ephemeral'}}]})
 try:cache_api.native_request(value,{'system':'owned','brief':'brief'})
 except ValueError:pass
 else:raise AssertionError('plain text marker accepted')
 for block in [{'type':'thinking','thinking':'fixture','signature':None},{'type':'unknown','text':'fixture'}]:
  result=cache_api.native_response({'model':MODEL,'role':'assistant','stop_reason':'end_turn','content':[block],'usage':{'input_tokens':10,'output_tokens':2}},MODEL)
  assert result['_native_error'] and result['usage']['total_tokens']==12
 for block in [{'type':'thinking','thinking':KEY.decode(),'signature':'synthetic signature'},{'type':'tool_use','id':'t1','name':'shell','input':{'command':KEY.decode()}},None]:
  body=json.dumps({'model':MODEL,'role':'assistant','stop_reason':'end_turn','content':[block],'usage':{'input_tokens':10,'output_tokens':2}}).encode();upstream_calls=[]
  class Response:
   status=200
   def read(self,_):return body
  class Upstream:
   def __init__(self,*args,**kwargs):pass
   def request(self,*args,**kwargs):upstream_calls.append(True)
   def getresponse(self):return Response()
   def close(self):pass
  relay=object.__new__(proxy.Relay);relay.routes={('api.anthropic.com','/v1/messages'):'model'};relay.keys={'api.anthropic.com':KEY};relay.model=MODEL;relay.turn_limit=10;relay.calls=0;relay.lock=threading.Lock();relay.log=[];relay.context=None;relay.incident=False;relay.limit_hit=False;relay.budgets={};relay.cache_prefix={'system':'owned','brief':'brief'}
  handler=object.__new__(proxy.Handler);handler.server=relay;handler.connection=types.SimpleNamespace(settimeout=lambda _:None);handler.path='https://api.anthropic.com/v1/messages';handler.command='POST';handler.headers=email.message.Message();packet=copy.deepcopy(request)
  if block is None:packet['messages'].append({'role':'user','content':'雪'*180000})
  payload=json.dumps(packet,ensure_ascii=False).encode();assert len(payload)<proxy.MAX_BODY
  handler.headers['Content-Length']=str(len(payload));handler.rfile=io.BytesIO(payload);handler.wfile=io.BytesIO();statuses=[];handler.send_response=lambda status:statuses.append(status);handler.send_header=lambda *args:None;handler.end_headers=lambda:None
  saved=proxy.http.client.HTTPSConnection;proxy.http.client.HTTPSConnection=Upstream
  try:handler.do_POST()
  finally:proxy.http.client.HTTPSConnection=saved
  if block is None:assert statuses==[413] and not upstream_calls and not relay.incident
  else:assert statuses==[502] and relay.incident and KEY not in handler.wfile.getvalue()
 print('8 block/size failure directions pass: native/text markers, malformed blocks, nested raw key echoes; signature cryptography remains provider-owned')
if __name__=='__main__':check()
