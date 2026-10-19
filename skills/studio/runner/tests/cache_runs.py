#!/usr/bin/env python3
"""Actual sealed runner, native mock provider and protected receipts. No paid calls."""
import argparse,json,os,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run,proxy
KEY=b'SYNTHETIC-NATIVE-CACHE-MARKER';MODEL='claude-sonnet-4-5-20250929'

def test(args,mode):
 calls=[];writer=[];reviews=[];model='claude-opus-5-5' if mode=='opus-hit' else MODEL
 class Response:
  status=200
  def read(self,_):
   request=calls[-1];is_writer='tools' in request;u={'input_tokens':10,'output_tokens':5};content=[];reason='end_turn'
   if is_writer:
    writer.append(request)
    if mode!='ignored':u.update(cache_creation_input_tokens=1000 if len(writer)==1 else 0,cache_read_input_tokens=1000 if len(writer)>1 else 0)
    if len(writer)==1:
     content=[{'type':'thinking','thinking':'signed fixture','signature':'fixture-signature'},{'type':'tool_use','id':'draw1','name':'shell','input':{'command':'mkdir -p assets; convert -size 4x4 xc:red PNG32:assets/item.png'}}];reason='tool_use'
    else:
     assert request['messages'][1]['content'][0]['signature']=='fixture-signature'
     assert request['messages'][2]['content'][0]['type']=='tool_result'
     assert 'cache_control' not in json.dumps(request['messages'][1:])
     content=[{'type':'text','text':'Delivery ready.'}]
   else:
    reviews.append(request)
    assert 'writer-only-marker' not in json.dumps(request['system']).lower()
    assert 'cache_control' not in json.dumps(request['messages'])
    content=[{'type':'text','text':'```json\n{"name":"a red square"}\n```' if request['max_tokens']==128 else '{"features":[true]}'}]
   if mode=='bad-role':role='user'
   else:role='assistant'
   if mode=='key-echo':content=[{'type':'thinking','thinking':KEY.decode(),'signature':'s'}]
   return json.dumps({'model':('other-model' if mode=='bad-model' else model),'role':role,'stop_reason':reason,'content':content,'usage':u}).encode()
 class Upstream:
  def __init__(self,host,port,**kw):assert (host,port)==('api.anthropic.com',443)
  def request(self,method,path,body,headers):
   assert path=='/v1/messages' and headers=={'Content-Type':'application/json','x-api-key':KEY.decode(),'anthropic-version':'2023-06-01'}
   request=json.loads(body);assert not any(k in request for k in ('seed','temperature'))
   assert request['system'][-1]['cache_control']=={'type':'ephemeral'}
   calls.append(request)
  def getresponse(self):return Response()
  def close(self):pass
 saved=proxy.http.client.HTTPSConnection;proxy.http.client.HTTPSConnection=Upstream
 try:
  with tempfile.TemporaryDirectory() as temp:
   case=Path(temp);(case/'inputs').mkdir();(case/'brief.md').write_text('Draw a red square at assets/item.png.');(case/'SKILL.md').write_text('Writer-only-marker. Draw and finish.');(case/'expected.json').write_text('{}')
   (case/'check.py').write_text("import json,pathlib,sys\np=pathlib.Path(sys.argv[1]);ok=(p/'assets/item.png').is_file()\nprint(json.dumps({'case':'cache-fixture','rules':[{'id':'export','pass':ok,'measured':ok,'threshold':True}]}));sys.exit(0 if ok else 1)\n")
   (case/'plan.json').write_text('[{"file":"assets/item.png","subject_words":["orb"],"features":["Is there a visible red region?"]}]')
   fd,w=os.pipe();os.write(w,KEY);os.close(w);output=args.output/mode
   sys.argv=['run.py','run','--image',args.image,'--store',str(args.store),'--selftest',str(args.selftest),'--case',str(case),'--case-id','cache-fixture','--skill',str(case/'SKILL.md'),'--output',str(output),'--host','api.anthropic.com','--model',model,'--key-fds',json.dumps({'api.anthropic.com':fd}),'--prompt-cache','--turns','8']
   if mode=='review':sys.argv+=['--review-plan',str(case/'plan.json')]
   try:code=run.main()
   finally:os.close(fd)
   result=json.loads((output/'result.json').read_text())
   if mode=='key-echo':
    assert code==1 and result['key_scan']=='incident' and 'usage' not in result and not (output/'scratch').exists()
   else:
    assert result['key_scan']=='passed'
    usage=json.loads((output/'scratch/.run/usage.json').read_text());assert usage==result['usage']
    assert KEY not in b''.join(p.read_bytes() for p in (output/'scratch/.run').iterdir())
    if mode in ('bad-role','bad-model'):assert code==1 and usage['cache_creation_input_tokens']==1000 and usage['total_tokens']==1015
    else:
     assert code==0 and result['verdict']=='passed',result
     assert len(writer)==2
     assert usage['cache_read_input_tokens']==(0 if mode=='ignored' else 1000)
     assert usage['cache_creation_input_tokens']==(0 if mode=='ignored' else 1000)
     assert usage['uncached_input_tokens']==(40 if mode=='review' else 20)
     assert usage['estimated_cost_usd']==({'hit':.00426,'ignored':.00021,'review':.00447,'opus-hit':.00548}[mode])
     if mode=='review':assert len(reviews)==2 and result['review_accepted'] and any(r['usage'].get('cache_read_input_tokens')==0 for r in result['review_records'])
   return {'scenario':mode,'passed':True,'mock_requests':len(calls),'real_provider_calls':0}
 finally:proxy.http.client.HTTPSConnection=saved

def main():
 p=argparse.ArgumentParser();p.add_argument('--store',type=Path,required=True);p.add_argument('--image',required=True);p.add_argument('--selftest',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();args.output.mkdir()
 results=[test(args,m) for m in ('hit','opus-hit','ignored','review','bad-role','bad-model','key-echo')];(args.output/'receipt.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps({'fixtures_passed':len(results),'real_provider_calls':0}))
if __name__=='__main__':main()
