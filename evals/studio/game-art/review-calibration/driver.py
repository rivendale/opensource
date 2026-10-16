#!/usr/bin/env python3
"""Frozen 8x calibration plan. Offline planning; batch execution added separately."""
import argparse,copy,hashlib,json,re,sys
from decimal import Decimal
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'skills/studio/runner'))
import reviewer
from proxy import Relay
SETTINGS={'model':'claude-sonnet-4-5-20250929','host':'api.anthropic.com','path':'/v1/chat/completions','temperature':0,'seed':0,'prompt_cache':False,'scale':8,'requests':116,'hard_stop_usd':'1.00'}
INPUT_SHA256={'answers.json': '4d4c488142564e85821f1414fde7d8bf67b3c3b5487fe0bb6acf66e2460c349a', 'RUN-LIST-8x.md': 'b358b326a02bef9f57e8bc601d2e13941ce454982e53c40dae6b7619d1cfbda3', 'images/244e9266.png': 'd738a0e7b2ebf8d65ce9b66484f3e236e65fb5c40090886a87b1b80589df20b2', 'images/2fd20bc9.png': 'fec3972c1bc662df2899672ff7fe6ebb58b38b9fb702767de2d4b74ec132d085', 'images/31834029.png': 'ec9ea3b8ef2288ff6c7ee19385e7a1146a73cbef03093af51008ffbcd646babd', 'images/5f70bf18.png': '50b068e07b4bf235705c19b77da49fdbbc7e98ddc0a46f1c6659cca98c963904', 'images/67c058dd.png': 'ecd7cf086f19da6079e24c0f0d8b3b9e017c7a82a4b306354ffc0dca3629bd4f', 'images/729152ee.png': '7d41bc62e328839cd2515040b647c983207aa67f9f5af6dec2a54315700b6551', 'images/87c4c0d8.png': 'b313a54b35964c976f62f8bc61da1d92aefa7217fc8ceeca8543f1a174ef88c7', 'images/955cb439.png': '5db57fc6e55561c5255fe07c0f9391d44a6fa72dba59878ccf966da671598242', 'images/a397f5be.png': '20c0f073ff99756789b51710d47b3d975dd06c099031e4c92e1af9af977ab1b4', 'images/b288076c.png': '2ebff1de8c8c40b4f4bc35741a0127e7adff3f6adb9e350ecaf278d3e43b2764', 'images/b5f7cab6.png': 'e160c5638526fa94b828f14b42f95daead27c30e5b3cbbc226a348794d2d2d94', 'images/bd99ccf4.png': '320c656f26ea17b94c5dee87f07d75040020e2e954ac863c2154feaa551bc70a', 'images/e62f4a63.png': '5c50ae700a920d0ee0ba3b2f08721f1cb5a3e1ca05413a76980d262039d1abfb', 'images/f87d4fa3.png': '33d223eef6729fd155afc852ffafaf302f0aa843d9b2d47a5964b3d644bf5b72', '../review-plans/leg-1-coin-pickup.json': '444efd1a8f1c7905c037c36ecb3d2e6602333b6a4f72cd6206bebc90aa9b0fb8', '../review-plans/leg-1-key-pickup.json': 'f52fc08da11bfd3244f79ac7ea512f44c0dde1802a81b795d76bbe7adae5c434', '../review-plans/leg-1-potion-pickup.json': '2aa8d2381cd18fe13ff054e955512fe4efd675592677502497a4f6d83b134222'}
def validate_settings(settings):
 if settings!=SETTINGS or any(type(settings[k]) is not type(v) for k,v in SETTINGS.items()):raise ValueError('fixed calibration settings differ')
def build_plan(here=HERE):
 here=Path(here)
 for path,digest in INPUT_SHA256.items():
  if hashlib.sha256((here/path).read_bytes()).hexdigest()!=digest:raise ValueError('fixed input differs: '+path)
 key=json.loads((here/'answers.json').read_text());images=key['images'];questions=key['questions']
 if len(images)!=14 or len(questions)!=6:raise ValueError('scoring set shape differs')
 pairs=[]
 for repeat in range(3):
  for image in images:
   item={'file':image['file'],'subject_words':list(key['words']),'features':copy.deepcopy(questions)}
   reviewer.validate_plan([item]);pairs.append(dict(pair=len(pairs),image=image['file'],repeat=repeat,plan=None,item=item))
 text=(here/'RUN-LIST-8x.md').read_text()
 for match in re.finditer(r'^\| (\d+) \| `([^`]+\.json)` \| `([^`]+\.png)`',text,re.M):
  number=int(match[1]);plan=match[2];image=match[3]
  if number!=len(pairs) or number<42:raise ValueError('plan pair order differs')
  value=json.loads((here.parent/'review-plans'/plan).read_text())
  if len(value)!=1:raise ValueError('plan requires one asset')
  item=value[0];item['file']=image;reviewer.validate_plan([item]);pairs.append(dict(pair=number,image=image,repeat=0,plan=plan,item=item))
 if len(pairs)!=58:raise ValueError('pair count differs')
 return pairs
EVENT_KINDS=('blind-name-request','blind-name-usage','blind-name','features-request','features-usage','features')
def derive_records(events,pairs):
 if len(events)!=len(pairs)*6:raise ValueError('incomplete event set is not a completed batch')
 records=[];plans=[]
 for pair in pairs:
  group=events[pair['pair']*6:pair['pair']*6+6]
  if [e.get('kind') for e in group]!=list(EVENT_KINDS) or any(e.get('pair')!=pair['pair'] for e in group):raise ValueError('mixed or reordered events')
  name=reviewer.reply_json(group[2]['content']);features=reviewer.reply_json(group[5]['content'])
  if (not isinstance(name,dict) or set(name)!={'name'} or not isinstance(name['name'],str) or not name['name'].strip() or len(name['name'])>240 or '\n' in name['name']):raise ValueError('invalid recorded name')
  if (not isinstance(features,dict) or set(features)!={'features'} or not isinstance(features['features'],list) or len(features['features'])!=len(pair['item']['features']) or any(type(v) is not bool for v in features['features'])):raise ValueError('invalid recorded features')
  record=dict(image=pair['image'],repeat=pair['repeat'],name=name['name'],features=features['features'])
  if pair['plan'] is None:records.append(record)
  else:plans.append(dict(record,plan=pair['plan'],review_accepted=all(features['features'])))
 return records,plans

def collect_pairs(relay,settings=None,here=HERE):
 """Internal collection only. No credential entry, files, scoring, retries or gate.

 The caller must still scan and persist outputs and run disk-based consumers.
 """
 settings=copy.deepcopy(SETTINGS if settings is None else settings);validate_settings(settings)
 if type(relay) is not Relay or getattr(relay.review_request,'__func__',None) is not Relay.review_request:raise ValueError('runner-owned Relay method required')
 if (relay.model!=settings['model'] or relay.routes!={(settings['host'],settings['path']):'model'} or getattr(relay,'cache_prefix',None) is not None or relay.calls!=0 or relay.turn_limit!=116):raise ValueError('relay is not a fresh fixed-policy calibration relay')
 pairs=build_plan(here);events=[];views={};requests=0;completed=0;prompt=0;completion=0;spend=Decimal(0);status='completed';reason=None;usage_unverified=False
 try:
  for pair in pairs:
   image=pair['image']
   if image not in views:
    data=(Path(here)/image).read_bytes();metadata=reviewer.view_metadata(data)
    if metadata['scale']!=8:raise ValueError('fixed scale differs')
    rendered=reviewer.neutral_views(data)
    if any(list(reviewer.png_dimensions(v))!=metadata['dimensions'] for v in rendered):raise ValueError('view dimensions differ')
    views[image]=(rendered,metadata)
   rendered,metadata=views[image]
   def record(kind,content,usage):
    nonlocal prompt,completion,spend
    event=dict(kind=kind,pair=pair['pair'],content=content,usage=usage)
    if kind.endswith('-request'):event.update(metadata)
    if relay.output_has_key(json.dumps(event,ensure_ascii=True).encode()):
     relay.incident=True;raise ValueError('key incident in decoded output')
    events.append(event)
    if kind.endswith('-usage'):
     if (set(usage)!={'prompt_tokens','completion_tokens','total_tokens'} or any(type(v) is not int or v<0 for v in usage.values()) or usage['total_tokens']!=usage['prompt_tokens']+usage['completion_tokens']):raise ValueError('inconsistent recorded usage')
     prompt+=usage['prompt_tokens'];completion+=usage['completion_tokens'];spend=(Decimal(prompt)*3+Decimal(completion)*15)/1000000
     if spend>=Decimal(settings['hard_stop_usd']):raise ValueError('hard spend stop reached')
   def transport(messages,max_tokens):
    nonlocal requests,usage_unverified
    if requests>=settings['requests'] or spend>=Decimal(settings['hard_stop_usd']):raise ValueError('request or spend ceiling')
    requests+=1
    result=relay.review_request(messages,max_tokens)
    if not isinstance(result,dict) or not isinstance(result.get('usage'),dict) or set(result['usage'])!={'prompt_tokens','completion_tokens','total_tokens'}:
     usage_unverified=True;raise ValueError('missing or unpriced usage category')
    if result.get('model')!=settings['model']:usage_unverified=True
    choices=result.get('choices')
    if isinstance(choices,list) and len(choices)==1 and isinstance(choices[0],dict) and isinstance(choices[0].get('message'),dict) and choices[0]['message'].get('refusal'):
     record('blind-name-usage' if requests%2 else 'features-usage',None,reviewer.reported_usage(result))
     record('blind-name' if requests%2 else 'features',choices[0]['message'].get('content'),{})
     raise ValueError('provider refusal')
    return result
   reviewer.review(rendered,pair['item'],settings['model'],transport,record)
   completed+=1
 except Exception as error:
  # Retain only a static exception class, never remote text or headers.
  status='incident' if relay.incident else 'partial';reason=type(error).__name__
 try:records,plans=derive_records(events[:completed*6],pairs[:completed])
 except (ValueError,TypeError,KeyError):
  records=[];plans=[];status='partial';reason='RecordMismatch'
 if status=='completed' and (requests!=116 or completed!=58):status='partial';reason='CountMismatch'
 if status=='incident':events=[];records=[];plans=[]
 return dict(status=status,reason=reason,requests_used=requests,pairs_completed=completed,records=records,plan_records=plans,events=events,prompt_tokens=prompt,completion_tokens=completion,spend_usd=str(spend),rates_date='2026-10-16',rates_source='https://platform.claude.com/docs/en/about-claude/pricing',usage_unverified=usage_unverified,spend_is_estimate=True,review_gate=False)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dry-run',action='store_true',required=True);a=p.parse_args();validate_settings(SETTINGS);pairs=build_plan()
 print(json.dumps({'settings':SETTINGS,'pairs':[{k:v for k,v in pair.items() if k!='item'} for pair in pairs],'requests':2*len(pairs),'provider_calls':0},indent=2))
if __name__=='__main__':main()
