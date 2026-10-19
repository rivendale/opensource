#!/usr/bin/env python3
"""Native cache accounting and authority failure cases; no provider calls."""
import copy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cache_api

def check():
 u=cache_api.native_usage({'input_tokens':20,'output_tokens':10,'cache_creation_input_tokens':1000,'cache_read_input_tokens':2000})
 assert u['prompt_tokens']==3020 and u['total_tokens']==3030
 assert cache_api.estimate_cost(u,'claude-sonnet-4-5-20250929')==0.00456
 assert cache_api.estimate_cost(u,'claude-opus-5-5')==0.00568
 assert cache_api.native_usage({'input_tokens':20,'output_tokens':10})['cache_read_input_tokens']==0
 for key in ('input_tokens','output_tokens','cache_creation_input_tokens','cache_read_input_tokens'):
  for bad in (-1,True,1.5,'1',None):
   value={'input_tokens':20,'output_tokens':10,'cache_creation_input_tokens':100,'cache_read_input_tokens':200};value[key]=bad
   try:cache_api.native_usage(value)
   except ValueError:pass
   else:raise AssertionError((key,bad))
 for value in [{'input_tokens':1}, {'output_tokens':1}, {'input_tokens':1,'output_tokens':1,'cache_creation':None}, {'input_tokens':1,'output_tokens':1,'cache_creation_input_tokens':10,'cache_creation':{'ephemeral_5m_input_tokens':9}}, {'input_tokens':1,'output_tokens':1,'cache_creation':{'ephemeral_5m_input_tokens':True}}]:
  try:cache_api.native_usage(value)
  except ValueError:pass
  else:raise AssertionError('malformed native usage accepted')
 for value in [{'prompt_tokens':1,'completion_tokens':2,'total_tokens':2}, {'prompt_tokens':1,'completion_tokens':1,'total_tokens':2,'cache_read_input_tokens':2}, {'prompt_tokens':True,'completion_tokens':1,'total_tokens':2}]:
  try:cache_api.usage(value)
  except ValueError:pass
  else:raise AssertionError('malformed normalized usage accepted')
 req={'model':'pinned','messages':[{'role':'system','content':'owned'},{'role':'user','content':'brief'},{'role':'assistant','content':'writer text'},{'role':'user','content':'untrusted turn'}],'tools':[]}
 native=cache_api.native_request(req,{'system':'owned','brief':'brief'})
 assert native['system'][0]['cache_control']=={'type':'ephemeral'}
 assert native['messages'][0]['content'][0]['cache_control']=={'type':'ephemeral'}
 assert 'cache_control' not in json.dumps(native['messages'][1:])
 assert 'cache_control' not in native and 'temperature' not in native and 'seed' not in native
 bad=copy.deepcopy(req);bad['messages'][0]['content']='writer changed prefix'
 try:cache_api.native_request(bad,{'system':'owned','brief':'brief'})
 except ValueError:pass
 else:raise AssertionError('writer prefix cached')
 raw={'model':'pinned','role':'assistant','stop_reason':'tool_use','content':[{'type':'thinking','thinking':'signed','signature':'sig'},{'type':'tool_use','id':'t1','name':'shell','input':{'command':'true'}}],'usage':{'input_tokens':20,'output_tokens':10,'cache_read_input_tokens':1000}}
 normalized=cache_api.native_response(raw,'pinned');message=normalized['choices'][0]['message'];assert message['_native_content']==raw['content']
 req['messages']=[req['messages'][0],req['messages'][1],message,{'role':'tool','tool_call_id':'t1','content':'done'}]
 native=cache_api.native_request(req,{'system':'owned','brief':'brief'})
 assert native['messages'][1]['content']==raw['content'] and native['messages'][2]['content'][0]['type']=='tool_result'
 injected=copy.deepcopy(req);injected['messages'][2]['_native_content'][0]['cache_control']={'type':'ephemeral'}
 try:cache_api.native_request(injected,{'system':'owned','brief':'brief'})
 except ValueError:pass
 else:raise AssertionError('writer native marker forwarded')
 print('native usage, pricing, ignored-cache, owned-prefix, malformed counters and signed-tool history passed')
if __name__=='__main__':check()
