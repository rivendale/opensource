#!/usr/bin/env python3
"""Offline blind-context and fail-closed parsing checks; never a model call."""
import copy,json,sys,subprocess,tempfile,struct,zlib,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import reviewer
MODEL='synthetic-pinned-reviewer'
ITEM={'file':'assets/neutral.png','subject_words':['orb'], 'features':['Is there a visible dark edge?', 'Is a bright spot visible?']}

def reply(text,**changes):
 r={'model':MODEL,'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':text}}],
    'usage':{'prompt_tokens':10,'completion_tokens':5,'total_tokens':15}}
 r.update(changes);return r


def check():
 data=subprocess.check_output(['convert','-size','4x4','xc:none','-fill','#ffffff','-draw','point 1,1','PNG32:-'])
 views=reviewer.neutral_views(data);assert all(reviewer.png_dimensions(v)==(32,32) for v in views)
 assert views[0]!=views[1]
 calls=[];records=[]
 def transport(messages,limit):
  calls.append(copy.deepcopy(messages))
  if len(calls)==1:
   text=json.dumps(messages)
   assert 'orb' not in text and 'assets/' not in text and 'dark edge' not in text
   assert len(messages)==2 and isinstance(messages[1]['content'],list)
   return reply('{"name":"a pale spot"}')
  assert any(r[0]=='blind-name' for r in records) and records[-1][0]=='features-request'
  assert messages[2]['content']=='{"name":"a pale spot"}'
  assert 'dark edge' in messages[3]['content']
  return reply('{"features":[true,false]}')
 r=reviewer.review(views,ITEM,MODEL,transport,lambda *x:records.append(x))
 assert r['accepted'] is False and len(calls)==2
 assert sum(x[2].get('total_tokens',0) for x in records)==30
 assert all('data:image' not in r[1] for r in records if r[0].endswith('-request'))
 assert 'sha256' in records[0][1] and 'bytes' in records[0][1]
 # Invalid answers never become acceptance; any valid paid usage stays recorded.
 mutations=[reply('not JSON'),reply('{"name":""}'),reply('{"name":"two\\nlines"}'),
   reply('{"name":"x"}',model='other'),reply('{"name":"x"}',choices=[{'finish_reason':'length','message':{'role':'assistant','content':'x'}}]),
   reply('{"name":"x"}',choices=[{'finish_reason':'stop','message':{'role':'assistant','content':'x','tool_calls':[{}]}}])]
 for bad in mutations:
  records=[]
  try:reviewer.review(views,ITEM,MODEL,lambda *_:bad,lambda *x:records.append(x))
  except reviewer.ReviewError:pass
  else:raise AssertionError('invalid name accepted')
  assert sum(r[2].get('total_tokens',0) for r in records)==15
 for text in ['{"features":[1,0]}','{"features":[true]}','{"features":[true,true],"extra":1}','garbage']:
  responses=iter([reply('{"name":"a pale spot"}'),reply(text)])
  try:reviewer.review(views,ITEM,MODEL,lambda *_:next(responses),lambda *_:None)
  except reviewer.ReviewError:pass
  else:raise AssertionError('invalid feature answers accepted')
 for item in [dict(ITEM,file='../x'),dict(ITEM,file='assets//x'),dict(ITEM,features=['Is the orb visible?']),dict(ITEM,features=[]),dict(ITEM,subject_words=[])]:
  try:reviewer.validate_plan([item])
  except reviewer.ReviewError:pass
  else:raise AssertionError('bad plan accepted')
 for text in ['Are orbs visible?', 'Is it orblike?', 'Is an оrb present?']:
  try:reviewer.validate_plan([dict(ITEM,features=[text])])
  except reviewer.ReviewError:pass
  else:raise AssertionError('priming stem or lookalike accepted')
 corrupted=bytearray(data);corrupted[29]^=1
 unknown=b'\x00\x00\x00\x00'+b'zzZZ'+struct.pack('>I',zlib.crc32(b'zzZZ'))
 for bad in [bytes(corrupted),data[:-12],data+b'trailing',data[:-12]+unknown+data[-12:]]:
  try:reviewer.png_dimensions(bad)
  except reviewer.ReviewError:pass
  else:raise AssertionError('invalid PNG accepted')
 # Large, poorly compressible artwork remains small in protected request records.
 rng=random.Random(0);pixels=bytes(rng.randrange(256) for _ in range(256*256*4))
 large=subprocess.check_output(['convert','-size','256x256','-depth','8','rgba:-','PNG32:-'],input=pixels)
 large_views=reviewer.neutral_views(large)
 encoded=reviewer.content(large_views)
 record=reviewer.request_record([{'role':'user','content':encoded}])
 assert len(record)<1024 and 'data:image' not in record
 for usage in [{},{'prompt_tokens':True,'completion_tokens':1,'total_tokens':2},{'prompt_tokens':10,'completion_tokens':5,'total_tokens':0}]:
  try:reviewer.response(reply('x',usage=usage),MODEL)
  except reviewer.ReviewError:pass
  else:raise AssertionError('bad usage accepted')
 print('offline reviewer context, ordering, strictness and usage checks passed')
if __name__=='__main__':check()
