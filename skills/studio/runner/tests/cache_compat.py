#!/usr/bin/env python3
"""Compare real main/candidate OFF relay captures with synthetic upstream only."""
import argparse,hashlib,io,json,subprocess,sys,tarfile,tempfile
from pathlib import Path
HERE=Path(__file__).resolve();ROOT=HERE.parents[4]
BASELINE='350a45c62151c36ff310b5a513847386fcc1f6c9'
MODEL='synthetic-pinned-model';KEY=b'SYNTHETIC-COMPATIBILITY-MARKER'
def worker(root,handler_only=False):
 import http.client,socket,threading
 sys.path.insert(0,str(root));import proxy,agent
 seen=[]
 class Response:
  status=200
  def read(self,_):return json.dumps({'model':MODEL,'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':'ok'}}],'usage':{'prompt_tokens':10,'completion_tokens':2,'total_tokens':12}}).encode()
 class Upstream:
  def __init__(self,host,port,**kw):assert (host,port)==('api.anthropic.com',443)
  def request(self,method,path,payload,headers):seen.append(dict(path=path,sha256=hashlib.sha256(payload).hexdigest(),bytes=len(payload),headers=headers))
  def getresponse(self):return Response()
  def close(self):pass
 proxy.http.client.HTTPSConnection=Upstream
 def post(relay,payload):
  conn=agent.UnixHTTP('relay');conn.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);conn.sock.connect(str(relay.server_address));conn.sock.settimeout(10)
  try:
   conn.request('POST','https://api.anthropic.com/v1/chat/completions',payload,{'Content-Type':'application/json'})
  except BrokenPipeError:
   # The bounded relay can reject headers (413) before consuming the body.
   # Read that HTTP response; other failures still propagate.
   pass
  r=conn.getresponse();body=r.read();conn.close();return r.status,json.loads(body)
 records=[]
 with tempfile.TemporaryDirectory() as tmp:
  if handler_only:
   import email.message,types
   relay=object.__new__(proxy.Relay);relay.routes={('api.anthropic.com','/v1/chat/completions'):'model'};relay.keys={'api.anthropic.com':KEY};relay.model=MODEL;relay.turn_limit=20;relay.calls=0;relay.lock=threading.Lock();relay.log=[];relay.context=None;relay.incident=False;relay.limit_hit=False;relay.budgets={};relay.cache_prefix=None
   def post(relay,payload):
    handler=object.__new__(proxy.Handler);handler.server=relay;handler.connection=types.SimpleNamespace(settimeout=lambda _:None);handler.path='https://api.anthropic.com/v1/chat/completions';handler.command='POST';handler.headers=email.message.Message();handler.headers['Content-Length']=str(len(payload));handler.rfile=io.BytesIO(payload);handler.wfile=io.BytesIO();statuses=[];handler.send_response=lambda status:statuses.append(status);handler.send_header=lambda *args:None;handler.end_headers=lambda:None
    handler.do_POST();return statuses[-1],json.loads(handler.wfile.getvalue())
  else:
   relay=proxy.Relay(Path(tmp)/'relay.sock',[{'name':'model','host':'api.anthropic.com','path':'/v1/chat/completions'}],{'api.anthropic.com':KEY},MODEL,20)
   thread=threading.Thread(target=relay.serve_forever,daemon=True);thread.start()
  try:
   request=dict(model=MODEL,messages=[{'role':'system','content':'fixed system'},{'role':'user','content':'fixed brief'}],tools=agent.TOOLS,stream=False,temperature=0,seed=0)
   import copy
   variants=[('initial',request)]
   follow=copy.deepcopy(request);follow['messages'] += [{'role':'assistant','content':None,'tool_calls':[{'id':'t1','type':'function','function':{'name':'shell','arguments':'{"command":"fixture only"}'}}]},{'role':'tool','tool_call_id':'t1','content':'fixture output'}];variants.append(('tool-history',follow))
   unicode=copy.deepcopy(request);unicode['messages'][1]['content']='雪'*180000;variants.append(('utf8-expands-after-normalization',unicode))
   for name,value in variants:
    payload=json.dumps(value,ensure_ascii=False).encode();assert len(payload)<=proxy.MAX_BODY
    before=len(seen);status,body=post(relay,payload);records.append(dict(case=name,status=status,upstream=seen[before:],body=body))
   before=len(seen);status,body=post(relay,b' '* (proxy.MAX_BODY+1));assert status==413 and len(seen)==before
   records.append(dict(case='oversized-input',status=status,upstream=[],body=body))
   for limit in (128,256):
    before=len(seen);reply=relay.review_request([{'role':'system','content':'fixed reviewer'},{'role':'user','content':'fixture image text'}],limit)
    records.append(dict(case='reviewer-'+str(limit),status=200,upstream=seen[before:],body=reply))
  finally:
   if not handler_only:relay.shutdown();relay.server_close();thread.join()
 # Never retain even the synthetic auth value in the receipt.
 for r in records:
  for capture in r['upstream']:capture['headers']={k:('SYNTHETIC' if k.lower() in ('authorization','x-api-key') else v) for k,v in capture['headers'].items()}
 return records
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--worker',type=Path);p.add_argument('--handler-only',action='store_true');p.add_argument('--baseline',default=BASELINE);p.add_argument('--receipt',type=Path);a=p.parse_args()
 if a.worker:print(json.dumps(worker(a.worker,a.handler_only)));return
 if len(a.baseline)!=40 or any(c not in '0123456789abcdef' for c in a.baseline):raise ValueError('baseline must be a full commit')
 with tempfile.TemporaryDirectory() as tmp:
  root=Path(tmp);raw=subprocess.check_output(['git','-C',str(ROOT),'archive',a.baseline,'skills/studio/runner'])
  with tarfile.open(fileobj=io.BytesIO(raw)) as tar:tar.extractall(root,filter='data')
  results=[]
  for source in [root/'skills/studio/runner',HERE.parents[1]]:
   result=subprocess.run([sys.executable,str(HERE),'--worker',str(source)]+(['--handler-only'] if a.handler_only else []),capture_output=True,text=True)
   if result.returncode:raise RuntimeError('compatibility worker failed: '+result.stderr)
   results.append(json.loads(result.stdout))
  if results[0]!=results[1]:raise AssertionError('OFF relay behavior differs from pinned main: '+json.dumps([[(r['case'],r['status']) for r in rows] for rows in results]))
  receipt=dict(baseline=a.baseline,candidate_source='working tree; pin publication commit in PR',off_main_vs_candidate_equal=True,transport='direct Handler only, no socket binding' if a.handler_only else 'Unix socket relay',cases=results[0],real_credentials_used=False,real_provider_calls=0)
  if a.receipt:a.receipt.write_text(json.dumps(receipt,indent=2)+'\n')
  print('6 main/candidate OFF comparisons match; mode='+('direct handler' if a.handler_only else 'Unix relay')+'; synthetic upstream only')
if __name__=='__main__':main()
