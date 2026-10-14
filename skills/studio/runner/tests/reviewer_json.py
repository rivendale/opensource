#!/usr/bin/env python3
"""Offline reply boundary fixtures specified before the parser change."""
import copy,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import reviewer
MODEL='synthetic-pinned-reviewer'
ITEM={'file':'assets/neutral.png','subject_words':['orb'],'features':['Is there a dark edge?']}
# Parsing needs only valid PNG headers and framing, never a decoder or a model.
import struct,zlib
chunk=lambda kind,data:struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))
PNG=reviewer.PNG+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b'\x00\xff\x00\x00\xff'))+chunk(b'IEND',b'')

def envelope(text):
 return {'model':MODEL,'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':text}}], 'usage':{'prompt_tokens':10,'completion_tokens':5,'total_tokens':15}}

def run(first,second):
 calls=[];events=[]
 def transport(messages,limit):
  calls.append(copy.deepcopy(messages));return envelope(first if len(calls)==1 else second)
 try:
  result=reviewer.review([PNG,PNG],ITEM,MODEL,transport,lambda *x:events.append(x))
 except reviewer.ReviewError as e:return False,calls,events,str(e)
 return True,calls,events,result


def check():
 name='{"name":"a red dot"}';features='{"features":[true]}'
 wrappers=[lambda t:t,lambda t:'```json\n'+t+'\n```',lambda t:'```\n'+t+'\n```',lambda t:' \t\r\n```json\r\n'+t+'\r\n```\r\n \t',lambda t:'``` \t\n'+t+'\n```\n']
 count=0
 for wrap in wrappers:
  for stage in ('name','features','both'):
   first=wrap(name) if stage!='features' else name;second=wrap(features) if stage!='name' else features
   ok,calls,events,result=run(first,second);assert ok and result['accepted'],(stage,first,second,result)
   assert calls[1][2]['content']==first
   assert next(e[1] for e in events if e[0]=='blind-name')==first
   assert next(e[1] for e in events if e[0]=='features')==second
   assert sum(e[2].get('total_tokens',0) for e in events)==30
   assert [e[0] for e in events].index('blind-name-usage')<[e[0] for e in events].index('blind-name')
   assert [e[0] for e in events].index('features-usage')<[e[0] for e in events].index('features')
   count+=1
 rejected=[lambda t:'prose\n```json\n'+t+'\n```',lambda t:'```json\n'+t+'\n```\nprose',lambda t:'```json\n'+t+'\n```\n```json\n'+t+'\n```',lambda t:'```json\n```\n'+t+'\n```\n```',lambda t:'```json\n'+t,lambda t:'~~~json\n'+t+'\n~~~',lambda t:'```python\n'+t+'\n```',lambda t:'```""\n'+t+'\n```',lambda t:"```''\n"+t+'\n```',lambda t:'```json\n\n```',lambda t:'```json\ninvalid\n```',lambda t:'\ufeff'+t,lambda t:'\u200b'+t,lambda t:'```json'+t+'```',lambda t:' '*8192+t]
 for wrap in rejected:
  for stage in ('name','features'):
   ok,calls,events,_=run(wrap(name) if stage=='name' else name,wrap(features) if stage=='features' else features)
   assert not ok,(stage,wrap(name))
   assert len(calls)==(1 if stage=='name' else 2)
   assert sum(e[2].get('total_tokens',0) for e in events)==len(calls)*15
   count+=1
 bad_names=['{"name":"```"}',r'{"name":"\u0060\u0060\u0060"}','{"name":"a","name":"b"}','{"name":"a","extra":1}','{"name":1}','{"name":"a\\nb"}','{"name":"a","extra":NaN}']
 bad_features=['{"features":[true],"features":[false]}','{"features":[true],"extra":1}','{"features":[1]}','{"features":[]}','{"features":[true,true]}','{"features":"```"}']
 for texts,stage in [(bad_names,'name'),(bad_features,'features')]:
  for text in texts:
   for wrap in wrappers[:3]:
    ok,_,_,_=run(wrap(text) if stage=='name' else name,wrap(text) if stage=='features' else features);assert not ok,(stage,text);count+=1
 # This control must fail at the parser, before any reply schema is checked.
 try:reviewer.reply_json('{"a":["```"]}')
 except reviewer.ReviewError:pass
 else:raise AssertionError('inner fence in array accepted')
 count+=1
 # Use the standard-library Python scanner to make deep recursion portable:
 # the optimized scanner's depth boundary differs across Python releases.
 scanner=json.scanner.make_scanner
 json.scanner.make_scanner=json.scanner.py_make_scanner
 try:
  deep='['*1500+'0'+']'*1500
  assert len(deep)<=8192
  try:reviewer.reply_json(deep)
  except reviewer.ReviewError:pass
  else:raise AssertionError('deep-array recursion accepted')
 finally:json.scanner.make_scanner=scanner
 count+=1
 print(json.dumps({'fixtures_passed':count,'real_provider_calls':0}))
if __name__=='__main__':check()
