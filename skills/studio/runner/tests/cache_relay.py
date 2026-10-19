#!/usr/bin/env python3
"""Exercise the real Unix relay boundary with a fake upstream; no provider I/O."""
import copy,http.client,json,socket,sys,tempfile,threading,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import proxy
from agent import TOOLS,UnixHTTP
KEY=b'SYNTHETIC-CACHE-MARKER'
MODEL='claude-sonnet-4-5-20250929'

def check():
 saved=proxy.http.client.HTTPSConnection;seen=[];responses=[]
 class Response:
  status=200
  def read(self,_):return json.dumps(responses.pop(0)).encode()
 class Upstream:
  def __init__(self,host,port,**kw):assert (host,port)==('api.anthropic.com',443)
  def request(self,method,path,payload,headers):seen.append((path,payload,headers))
  def getresponse(self):return Response()
  def close(self):pass
 proxy.http.client.HTTPSConnection=Upstream
 request={'model':MODEL,'messages':[{'role':'system','content':'owned'},{'role':'user','content':'brief'}], 'tools':TOOLS,'stream':False,'temperature':0,'seed':0}
 try:
  with tempfile.TemporaryDirectory() as tmp:
   def post(relay,path,request):
    connection=UnixHTTP('relay');connection.connect=lambda:None
    connection.sock=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);connection.sock.connect(str(relay.server_address));connection.sock.settimeout(10)
    connection.request('POST','https://api.anthropic.com'+path,json.dumps(request),{'Content-Type':'application/json'})
    response=connection.getresponse();body=response.read();connection.close();return response.status,json.loads(body)
   def start(path,prefix):
    relay=proxy.Relay(Path(tmp)/('off.sock' if prefix is None else 'on.sock'),[{'name':'model','host':'api.anthropic.com','path':path}],{'api.anthropic.com':KEY},MODEL,10,cache_prefix=prefix)
    thread=threading.Thread(target=relay.serve_forever,daemon=True);thread.start();return relay,thread
   off,thread=start('/v1/chat/completions',None)
   try:
    responses.append({'model':MODEL,'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':'ok'}}],'usage':{'prompt_tokens':10,'completion_tokens':2,'total_tokens':12}})
    status,body=post(off,'/v1/chat/completions',request);assert status==200
    assert seen[-1][1]==json.dumps(request,allow_nan=False).encode(),'cache OFF request bytes changed'
    assert hashlib.sha256(seen[-1][1]).hexdigest()=='a4580870e45bbb8d62f83cb026b0ff165d70f8b54ac89b03d7a2eaa829ade8e1'
    assert seen[-1][2]=={'Content-Type':'application/json','Authorization':'Bearer '+KEY.decode()}
   finally:off.shutdown();off.server_close();thread.join()
   on,thread=start('/v1/messages',{'system':'owned','brief':'brief'})
   try:
    for n in range(2):
     responses.append({'model':MODEL,'role':'assistant','stop_reason':'end_turn','content':[{'type':'text','text':'ok'}], 'usage':{'input_tokens':10,'output_tokens':2,'cache_creation_input_tokens':1000 if n==0 else 0,'cache_read_input_tokens':1000 if n else 0}})
     status,body=post(on,'/v1/messages',request);assert status==200
     assert body['usage']['cache_read_input_tokens']==(1000 if n else 0)
     wire=json.loads(seen[-1][1]);assert wire['system'][0]['cache_control']=={'type':'ephemeral'}
     assert seen[-1][0]=='/v1/messages' and seen[-1][2]=={'Content-Type':'application/json','x-api-key':KEY.decode(),'anthropic-version':'2023-06-01'}
    # Cache-control is not caller-controlled, and credentials never come from caller headers.
    mutated=copy.deepcopy(request);mutated['cache_control']={'type':'ephemeral'};before=len(seen)
    assert post(on,'/v1/messages',mutated)[0]==403 and len(seen)==before
    mutated=copy.deepcopy(request);mutated['messages'][0]['content']='writer';assert post(on,'/v1/messages',mutated)[0]==400
    assert post(on,'/v1/chat/completions',request)[0]==403
    responses.append({'model':MODEL,'role':'assistant','stop_reason':'end_turn','content':[{'type':'thinking','thinking':KEY.decode(),'signature':'s'}],'usage':{'input_tokens':1,'output_tokens':1}})
    status,body=post(on,'/v1/messages',request);assert status==502 and on.incident
   finally:on.shutdown();on.server_close();thread.join()
 finally:proxy.http.client.HTTPSConnection=saved
 print('real relay cached-second-turn, OFF bytes, headers, caller-prefix/route refusal and raw thinking key-scan passed')
if __name__=='__main__':check()
