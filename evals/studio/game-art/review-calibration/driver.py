#!/usr/bin/env python3
"""Fixed 16x Opus 5.5 calibration batch using the trusted runner reviewer and intake."""
import argparse,copy,hashlib,json,re,sys,subprocess,tempfile
from datetime import datetime,timezone
from decimal import Decimal,InvalidOperation
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
def source_identity(root=ROOT):
 """Refuse changed or untracked importable sources before trusting runner imports."""
 scopes=['evals/studio/game-art/review-calibration','skills/studio/runner']
 commit=subprocess.run(['git','rev-parse','HEAD'],cwd=root,capture_output=True,check=True).stdout.decode().strip()
 if not re.fullmatch(r'[0-9a-f]{40}',commit):raise ValueError('invalid source commit')
 if subprocess.run(['git','diff','--quiet','HEAD','--',*scopes],cwd=root,capture_output=True,check=False).returncode:raise ValueError('modified tracked source')
 untracked=subprocess.run(['git','ls-files','--others','-z','--',*scopes],cwd=root,capture_output=True,check=True).stdout.decode().split('\0')
 if any(Path(name).suffix.lower() in ('.py','.pyc','.pyo','.so','.pyd','.zip','.pth') for name in untracked if name):raise ValueError('untracked importable source')
 return commit
SOURCE_COMMIT=None
if __name__=='__main__' and ('--run' in sys.argv or '--preflight' in sys.argv):
 try:SOURCE_COMMIT=source_identity()
 except (OSError,ValueError,subprocess.SubprocessError) as error:
  print(json.dumps({'status':'partial','reason':type(error).__name__}));sys.exit(2)
sys.path.insert(0,str(ROOT/'skills/studio/runner'))
import reviewer
import cache_api
from proxy import Relay
from common import read_key_fds
SETTINGS={'model':'claude-opus-5-5','host':'api.anthropic.com','path':'/v1/chat/completions','temperature':None,'seed':0,'prompt_cache':False,'scale':16,'requests':116,'hard_stop_usd':'5.00','review_max_tokens':1024}
INPUT_SHA256={'answers.json': '4d4c488142564e85821f1414fde7d8bf67b3c3b5487fe0bb6acf66e2460c349a', 'RUN-LIST-opus55-room.md': 'fd073a14b8d388ac2d358e8e7c0834c782942ee5d688bb2e2911d19de773bc01', 'images/244e9266.png': 'd738a0e7b2ebf8d65ce9b66484f3e236e65fb5c40090886a87b1b80589df20b2', 'images/2fd20bc9.png': 'fec3972c1bc662df2899672ff7fe6ebb58b38b9fb702767de2d4b74ec132d085', 'images/31834029.png': 'ec9ea3b8ef2288ff6c7ee19385e7a1146a73cbef03093af51008ffbcd646babd', 'images/5f70bf18.png': '50b068e07b4bf235705c19b77da49fdbbc7e98ddc0a46f1c6659cca98c963904', 'images/67c058dd.png': 'ecd7cf086f19da6079e24c0f0d8b3b9e017c7a82a4b306354ffc0dca3629bd4f', 'images/729152ee.png': '7d41bc62e328839cd2515040b647c983207aa67f9f5af6dec2a54315700b6551', 'images/87c4c0d8.png': 'b313a54b35964c976f62f8bc61da1d92aefa7217fc8ceeca8543f1a174ef88c7', 'images/955cb439.png': '5db57fc6e55561c5255fe07c0f9391d44a6fa72dba59878ccf966da671598242', 'images/a397f5be.png': '20c0f073ff99756789b51710d47b3d975dd06c099031e4c92e1af9af977ab1b4', 'images/b288076c.png': '2ebff1de8c8c40b4f4bc35741a0127e7adff3f6adb9e350ecaf278d3e43b2764', 'images/b5f7cab6.png': 'e160c5638526fa94b828f14b42f95daead27c30e5b3cbbc226a348794d2d2d94', 'images/bd99ccf4.png': '320c656f26ea17b94c5dee87f07d75040020e2e954ac863c2154feaa551bc70a', 'images/e62f4a63.png': '5c50ae700a920d0ee0ba3b2f08721f1cb5a3e1ca05413a76980d262039d1abfb', 'images/f87d4fa3.png': '33d223eef6729fd155afc852ffafaf302f0aa843d9b2d47a5964b3d644bf5b72', '../review-plans/leg-1-coin-pickup.json': '444efd1a8f1c7905c037c36ecb3d2e6602333b6a4f72cd6206bebc90aa9b0fb8', '../review-plans/leg-1-key-pickup.json': 'f52fc08da11bfd3244f79ac7ea512f44c0dde1802a81b795d76bbe7adae5c434', '../review-plans/leg-1-potion-pickup.json': '2aa8d2381cd18fe13ff054e955512fe4efd675592677502497a4f6d83b134222'}
def estimate_spend(prompt,completion):
 rates=cache_api.RATES[SETTINGS['model']]
 return (Decimal(prompt)*Decimal(str(rates[0]))+Decimal(completion)*Decimal(str(rates[4])))/1000000

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
 text=(here/'RUN-LIST-opus55-room.md').read_text()
 model=re.search(r'^\| reviewer model \| `([^`]+)`',text,re.M)
 if model is None or model[1]!=SETTINGS['model']:raise ValueError('reviewer model differs from run list')
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

def collect_pairs(relay,settings=None,here=HERE,preflight_cost='0'):
 """Internal collection only. No credential entry, files, scoring, retries or gate.

 The caller must still scan and persist outputs and run disk-based consumers.
 """
 settings=copy.deepcopy(SETTINGS if settings is None else settings);validate_settings(settings)
 if type(relay) is not Relay or getattr(relay.review_request,'__func__',None) is not Relay.review_request:raise ValueError('runner-owned Relay method required')
 if (relay.model!=settings['model'] or relay.routes!={(settings['host'],settings['path']):'model'} or getattr(relay,'cache_prefix',None) is not None or relay.calls!=0 or relay.turn_limit!=116 or getattr(relay,'review_max_tokens',256)!=settings['review_max_tokens'] or getattr(relay,'review_temperature',0) is not settings['temperature']):raise ValueError('relay is not a fresh fixed-policy calibration relay')
 preflight_cost=Decimal(preflight_cost)
 if not preflight_cost.is_finite() or not 0<=preflight_cost<Decimal(settings['hard_stop_usd']):raise ValueError('invalid preflight cost')
 stop=None
 pairs=build_plan(here);events=[];views={};requests=0;completed=0;prompt=0;completion=0;spend=Decimal(0);status='collected';reason=None;usage_unverified=False
 try:
  for pair in pairs:
   image=pair['image']
   if image not in views:
    data=(Path(here)/image).read_bytes();metadata=reviewer.view_metadata(data,policy=reviewer.ViewPolicy.CALIBRATION)
    if metadata['scale']!=settings['scale']:raise ValueError('fixed scale differs')
    rendered=reviewer.neutral_views(data,policy=reviewer.ViewPolicy.CALIBRATION)
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
     prompt+=usage['prompt_tokens'];completion+=usage['completion_tokens'];spend=estimate_spend(prompt,completion)
     if spend+preflight_cost>=Decimal(settings['hard_stop_usd']):raise ValueError('hard spend stop reached')
   def transport(messages,max_tokens):
    nonlocal requests,usage_unverified
    if requests>=settings['requests'] or spend+preflight_cost>=Decimal(settings['hard_stop_usd']):raise ValueError('request or spend ceiling')
    requests+=1
    relay.last_http_status=None
    try:result=relay.review_request(messages,settings['review_max_tokens'])
    except Exception:
     usage_unverified=True;raise
    if (not isinstance(result,dict) or not isinstance(result.get('usage'),dict) or set(result['usage'])!={'prompt_tokens','completion_tokens','total_tokens'} or any(type(v) is not int or v<0 for v in result['usage'].values()) or result['usage']['total_tokens']!=result['usage']['prompt_tokens']+result['usage']['completion_tokens']):
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
  stop=stop_error(error,relay)
  status='incident' if relay.incident else 'partial';reason=type(error).__name__
  if not relay.incident:events.append(dict(kind='provider-stop',pair=completed,error=stop))
 try:records,plans=derive_records(events[:completed*6],pairs[:completed])
 except (ValueError,TypeError,KeyError):
  records=[];plans=[];status='partial';reason='RecordMismatch'
 if status=='collected' and (requests!=116 or completed!=58):status='partial';reason='CountMismatch'
 if status=='incident':events=[];records=[];plans=[]
 return dict(status=status,reason=reason,error=stop,preflight_spend_usd=str(preflight_cost),requests_used=requests,pairs_completed=completed,records=records,plan_records=plans,events=events,prompt_tokens=prompt,completion_tokens=completion,spend_usd=str(spend),rates_date=cache_api.RATES_DATE,rates_source=cache_api.RATES_SOURCE,usage_unverified=usage_unverified,spend_is_estimate=True,review_gate=False)

def validate_run_id(run_id):
 if not isinstance(run_id,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,63}',run_id):raise ValueError('invalid run id')

def persist_collection(relay,result,output,here=HERE,reserved=False):
 """Internal artifact stage, not a completed batch or public credential entry.

 The run-id directory and event identities are bound here. finish_receipt
 owns the final receipt; this stage alone never completes a batch.
 """
 report=dict(status='partial',reason='ConsumersPending',artifacts_written=0,disk_records_verified=False,sha256={})
 if type(relay) is not Relay:raise ValueError('runner-owned Relay required')
 if relay.incident or result.get('status')=='incident':
  report.update(status='incident',reason='KeyIncident');return report
 created=[];output=Path(output);run_id=output.name;report['run_id']=run_id
 try:
  validate_run_id(run_id)
  count=result['pairs_completed'];pairs=build_plan(here)
  if type(count) is not int or not 0<=count<=len(pairs):raise ValueError('invalid completed pair count')
  events=result['events'];records,plans=derive_records(events[:count*6],pairs[:count])
  if records!=result['records'] or plans!=result['plan_records']:raise ValueError('records disagree with events')
  payloads={
   'records.json':(json.dumps(records,ensure_ascii=False,indent=2)+'\n').encode(),
   'plan-records.json':(json.dumps(plans,ensure_ascii=False,indent=2)+'\n').encode(),
   'events.jsonl':''.join(json.dumps(dict(e,run_id=run_id),ensure_ascii=False)+'\n' for e in events).encode()}
  # Scan ALL payloads before the first write; use the runner's existing policy.
  for body in payloads.values():
   if relay.output_has_key(body):
    relay.incident=True;raise ValueError('key incident in output')
  if reserved:
   if output.is_symlink() or not output.is_dir() or any(output.iterdir()):raise ValueError('reserved batch directory is not empty')
  else:
   output.mkdir(mode=0o700,exist_ok=False)
  for name,body in payloads.items():
   path=output/name
   with path.open('xb') as stream:
    created.append(path);stream.write(body);stream.flush()
   report['artifacts_written']+=1
  written={name:(output/name).read_bytes() for name in payloads}
  for body in written.values():
   if relay.output_has_key(body):
    relay.incident=True;raise ValueError('key incident in disk output')
  if written!=payloads:raise ValueError('output bytes changed on disk')
  disk_events=[json.loads(line) for line in written['events.jsonl'].splitlines()]
  if any(e.get('run_id')!=run_id for e in disk_events):raise ValueError('mixed batch identity')
  disk_records,disk_plans=derive_records(disk_events[:count*6],pairs[:count])
  if disk_records!=json.loads(written['records.json']) or disk_plans!=json.loads(written['plan-records.json']):raise ValueError('disk records disagree with events')
  report['disk_records_verified']=True
  report['sha256']={name:hashlib.sha256(body).hexdigest() for name,body in written.items()}
 except (OSError,ValueError,TypeError,KeyError) as error:
  report['reason']=type(error).__name__
  if relay.incident:
   # Only paths created by this invocation can be removed. Existing trees are
   # never touched, including an existing directory or symlink at output.
   for path in created:path.unlink(missing_ok=True)
   if created:output.rmdir()
   report.update(status='incident',artifacts_written=0,sha256={},disk_records_verified=False)
 return report

def consume_written(relay,result,stage,output,baseline,here=HERE):
 """Run unchanged disk consumers; never promote a failed score or set a gate.

 Baseline is explicit. Self-comparison is useful only in offline tests, not
 evidence of improvement. finish_receipt still must verify the final files.
 """
 report=dict(status='partial',reason='IncompleteBatch',score_exit=None,compare_exit=None,review_gate=False,sha256={})
 if type(relay) is not Relay:raise ValueError('runner-owned Relay required')
 if relay.incident:report.update(status='incident',reason='KeyIncident');return report
 if result.get('status')!='collected' or result.get('requests_used')!=116 or result.get('pairs_completed')!=58 or not stage.get('disk_records_verified'):return report
 output=Path(output);here=Path(here);created=[]
 try:
  if stage.get('run_id')!=output.name:raise ValueError('batch directory identity differs')
  if (output/'score.stdout.json').exists():raise FileExistsError('scorer output already exists')
  written={name:(output/name).read_bytes() for name in ('records.json','plan-records.json','events.jsonl')}
  if {name:hashlib.sha256(body).hexdigest() for name,body in written.items()}!=stage['sha256']:raise ValueError('staged disk files changed')
  disk_events=[json.loads(line) for line in written['events.jsonl'].splitlines()]
  if any(e.get('run_id')!=output.name for e in disk_events):raise ValueError('mixed batch identity')
  records,plans=derive_records(disk_events,build_plan(here))
  if records!=json.loads(written['records.json']) or plans!=json.loads(written['plan-records.json']):raise ValueError('disk records disagree with events')
  for body in written.values():
   if relay.output_has_key(body):relay.incident=True;raise ValueError('key incident in disk input')
  scored=subprocess.run([sys.executable,str(here/'score.py'),str(output/'records.json')],capture_output=True,timeout=30,check=False)
  report['score_exit']=scored.returncode
  compared=subprocess.run([sys.executable,str(here/'compare_batches.py'),str(Path(baseline)),str(output/'records.json')],capture_output=True,timeout=30,check=False)
  report['compare_exit']=compared.returncode
  for body in (scored.stdout,scored.stderr,compared.stdout,compared.stderr):
   if relay.output_has_key(body):relay.incident=True;raise ValueError('key incident in consumer output')
  if any((output/name).read_bytes()!=body for name,body in written.items()):raise ValueError('inputs changed during consumers')
  with (output/'score.stdout.json').open('xb') as stream:
   created.append(output/'score.stdout.json');stream.write(scored.stdout);stream.flush()
  saved=(output/'score.stdout.json').read_bytes()
  if relay.output_has_key(saved):relay.incident=True;raise ValueError('key incident in saved score')
  if saved!=scored.stdout:raise ValueError('saved score differs')
  report['sha256']={'score.stdout.json':hashlib.sha256(saved).hexdigest()}
  # A floor failure is retained as exit 1. Execution errors or failed batch
  # coverage remain partial. No acceptance interpretation is made here.
  if scored.returncode in (0,1) and compared.returncode==0:report.update(status='consumed',reason='ReceiptPending')
  else:report['reason']='ConsumerExit'
 except (OSError,ValueError,TypeError,KeyError,subprocess.SubprocessError) as error:
  report['reason']=type(error).__name__
  if relay.incident:
   for path in created:path.unlink(missing_ok=True)
   for name in ('records.json','plan-records.json','events.jsonl'):(output/name).unlink(missing_ok=True)
   report.update(status='incident',sha256={})
 return report

ARTIFACT_NAMES=('records.json','plan-records.json','events.jsonl','score.stdout.json')
def validate_recorded_scale(events):
 """Current batch request receipts must match the pinned 16x list policy."""
 for event in events:
  if not event.get('kind','').endswith('-request'):continue
  if event.get('scale')!=SETTINGS['scale'] or type(event.get('scale')) is not int:
   raise ValueError('recorded scale differs from run list')
  source=event.get('source_dimensions')
  if not isinstance(source,list) or len(source)!=2 or any(type(d) is not int or not 1<=d<=reviewer.MAX_DIMENSION for d in source):raise ValueError('invalid recorded source dimensions')
  if event.get('dimensions')!=[d*SETTINGS['scale'] for d in source] or max(event['dimensions'])>reviewer.MAX_DIMENSION:raise ValueError('recorded view dimensions differ')


def verify_receipt(output):
 """Consuming check: directory identity, exact inventory, hashes, event identity."""
 output=Path(output)
 if output.is_symlink() or not output.is_dir() or (output/'receipt.json').is_symlink():raise ValueError('unsafe batch directory')
 receipt=json.loads((output/'receipt.json').read_bytes());validate_run_id(receipt['run_id'])
 validate_settings(receipt['settings'])
 if receipt.get('model')!=SETTINGS['model']:raise ValueError('recorded model differs from run list')
 if receipt['run_id']!=output.name:raise ValueError('receipt directory identity differs')
 if receipt.get('status') not in ('partial','incident','complete') or receipt.get('review_gate') is not False:raise ValueError('invalid receipt status or gate')
 hashes=receipt['sha256']
 if not isinstance(hashes,dict) or not set(hashes)<=set(ARTIFACT_NAMES):raise ValueError('unknown receipt artifact')
 if {p.name for p in output.iterdir()}!=set(hashes)|{'receipt.json'}:raise ValueError('batch inventory differs')
 for name,digest in hashes.items():
  path=output/name
  if path.is_symlink() or not path.is_file():raise ValueError('unsafe artifact')
  if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('receipt hash differs')
 if 'events.jsonl' in hashes:
  events=[json.loads(line) for line in (output/'events.jsonl').read_bytes().splitlines()]
  if receipt['status']=='complete':validate_recorded_scale(events)
  if any(e.get('run_id')!=receipt['run_id'] for e in events):raise ValueError('mixed batch identity')
 if receipt['status']=='complete':
  proof=validate_preflight(receipt.get('preflight'),receipt['source_commit'],require_fresh=False)
  if receipt.get('total_spend_usd')!=str(Decimal(receipt['spend_usd'])+Decimal(proof['spend_usd'])):raise ValueError('combined spend differs')
  if set(hashes)!=set(ARTIFACT_NAMES) or receipt['requests_used']!=116 or receipt['pairs_completed']!=58 or receipt['score_exit'] not in (0,1) or receipt['compare_exit']!=0 or receipt['review_gate'] is not False:raise ValueError('incomplete receipt claims complete')
  records,plans=derive_records(events,build_plan())
  if records!=json.loads((output/'records.json').read_bytes()) or plans!=json.loads((output/'plan-records.json').read_bytes()):raise ValueError('receipt records disagree with events')
 return receipt

def finish_receipt(relay,result,stage,consumed,output,source_commit):
 """Write one scanned receipt after the disk consumers, or record partial/incident.

 sha256 covers every other output. A file cannot contain its own sha256.
 The caller receives the receipt digest separately for external anchoring.
 """
 output=Path(output);validate_run_id(output.name)
 if not re.fullmatch(r'[0-9a-f]{40}',source_commit):raise ValueError('source commit must be a full Git SHA')
 status='complete' if result['status']=='collected' and stage.get('disk_records_verified') and consumed.get('status')=='consumed' else 'partial'
 hashes={};written={}
 for name in ARTIFACT_NAMES:
  path=output/name
  if path.is_symlink():raise ValueError('unsafe artifact')
  if path.exists():
   body=path.read_bytes()
   if relay.output_has_key(body):relay.incident=True
   written[name]=body;hashes[name]=hashlib.sha256(body).hexdigest()
 if {p.name for p in output.iterdir()}!=set(hashes):raise ValueError('unexpected batch file before receipt')
 if status=='complete':
  expected=dict(stage['sha256'],**consumed['sha256'])
  if hashes!=expected:raise ValueError('batch changed before receipt')
  events=[json.loads(line) for line in written['events.jsonl'].splitlines()]
  validate_recorded_scale(events)
  if any(e.get('run_id')!=output.name for e in events):raise ValueError('mixed batch identity')
  usage=[e['usage'] for e in events if e['kind'].endswith('-usage')]
  if len(usage)!=116 or any(set(u)!={'prompt_tokens','completion_tokens','total_tokens'} or any(type(v) is not int or v<0 for v in u.values()) or u['total_tokens']!=u['prompt_tokens']+u['completion_tokens'] for u in usage):raise ValueError('receipt usage differs')
  prompt=sum(u['prompt_tokens'] for u in usage);completion=sum(u['completion_tokens'] for u in usage)
  if prompt!=result['prompt_tokens'] or completion!=result['completion_tokens'] or Decimal(result['spend_usd'])!=estimate_spend(prompt,completion) or result['usage_unverified']:raise ValueError('receipt accounting differs')
 if relay.incident:
  status='incident'
  for name in ARTIFACT_NAMES:(output/name).unlink(missing_ok=True)
  hashes={}
 receipt=dict(run_id=output.name,date=datetime.now(timezone.utc).isoformat(),source_commit=source_commit,
  image_digest=hashlib.sha256(json.dumps({k:v for k,v in INPUT_SHA256.items() if k.startswith('images/')},sort_keys=True).encode()).hexdigest(),
  model=SETTINGS['model'],settings=copy.deepcopy(SETTINGS),status=status,error=result.get('error'),preflight=result.get('preflight'),total_spend_usd=str(Decimal(result['spend_usd'])+Decimal(result.get('preflight_spend_usd','0'))),requests_used=result['requests_used'],pairs_completed=result['pairs_completed'],
  record_counts=dict(records=0 if status=='incident' else len(result['records']),plan_records=0 if status=='incident' else len(result['plan_records'])),
  prompt_tokens=result['prompt_tokens'],completion_tokens=result['completion_tokens'],spend_usd=result['spend_usd'],
  rates=dict(date=result['rates_date'],source=result['rates_source'],input_per_million=str(cache_api.RATES[SETTINGS['model']][0]),output_per_million=str(cache_api.RATES[SETTINGS['model']][4])),
  usage_unverified=result['usage_unverified'],spend_is_estimate=result['spend_is_estimate'],key_scan='incident' if status=='incident' else 'passed',review_gate=False,
  score_exit=consumed.get('score_exit'),compare_exit=consumed.get('compare_exit'),sha256=hashes)
 body=(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n').encode()
 if relay.output_has_key(body):
  relay.incident=True
  for name in ARTIFACT_NAMES:(output/name).unlink(missing_ok=True)
  return dict(status='incident',reason='ReceiptKeyIncident')
 with (output/'receipt.json').open('xb') as stream:stream.write(body);stream.flush()
 try:
  if (output/'receipt.json').read_bytes()!=body:raise ValueError('receipt bytes changed')
  verified=verify_receipt(output)
 except (OSError,ValueError,TypeError,KeyError):
  (output/'receipt.json').unlink(missing_ok=True)
  raise
 return dict(status=verified['status'],receipt_sha256=hashlib.sha256(body).hexdigest(),score_exit=verified['score_exit'],compare_exit=verified['compare_exit'],review_gate=False)

def run_batch(relay,output,baseline,source_commit,here=HERE,preflight=None):
 """Single new batch; no retries, resume, repair, floor changes or gate."""
 output=Path(output)
 try:
  validate_preflight(preflight,source_commit)
  validate_run_id(output.name)
  if not re.fullmatch(r'[0-9a-f]{40}',source_commit):raise ValueError('source commit must be a full Git SHA')
  if not Path(baseline).is_file():raise ValueError('explicit comparison baseline required')
  build_plan(here);output.mkdir(mode=0o700,exist_ok=False)
 except (OSError,ValueError) as error:return dict(status='partial',reason=type(error).__name__)
 result=collect_pairs(relay,here=here,preflight_cost=preflight['spend_usd']);result['preflight']=preflight
 stage=persist_collection(relay,result,output,here,reserved=True)
 consumed=consume_written(relay,result,stage,output,baseline,here)
 try:
  if not output.exists():output.mkdir(mode=0o700,exist_ok=False)
  return finish_receipt(relay,result,stage,consumed,output,source_commit)
 except (OSError,ValueError,TypeError,KeyError) as error:return dict(status='incident' if relay.incident else 'partial',reason=type(error).__name__)

def build_relay(socket_path,key_fds,preflight=False):
 """Operator entry uses exactly the runner's existing inherited-FD helper."""
 validate_settings(SETTINGS)
 if not isinstance(key_fds,dict) or set(key_fds)!={SETTINGS['host']}:raise ValueError('exact calibration host FD required')
 return Relay(socket_path,[dict(name='model',host=SETTINGS['host'],path=SETTINGS['path'])],read_key_fds(key_fds),SETTINGS['model'],2 if preflight else SETTINGS['requests'],review_temperature=SETTINGS['temperature'],review_max_tokens=SETTINGS['review_max_tokens'])

SAFE_STOP_MESSAGES=frozenset({
 'preflight model differs','preflight usage invalid','preflight reply invalid','preflight response identity differs',
 'request or spend ceiling','hard spend stop reached','provider refusal',
 'missing or unpriced usage category','inconsistent recorded usage',
 'review model identity mismatch','review response invalid','review usage invalid',
 'review response incomplete','review response must be tool-free text',
 'review reply must be strict JSON','blind name must be one nonempty line',
 'one boolean per required feature is mandatory','fixed scale differs','view dimensions differ',
})

def stop_error(error,relay):
 status=getattr(relay,'last_http_status',None)
 if type(status) is not int or not 100<=status<=599:status=None
 value=getattr(error,'provider_error',None)
 if not isinstance(value,dict) or set(value)!={'http_status','type','message'}:
  candidate=error.args[0] if len(error.args)==1 and isinstance(error.args[0],str) else None
  message=next((item for item in SAFE_STOP_MESSAGES if item==candidate),'Calibration stopped; local exception text withheld')
  value=dict(http_status=status,type=type(error).__name__,message=message)
 if relay.incident or relay.output_has_key(json.dumps(value,ensure_ascii=False).encode()):
  relay.incident=True
  return dict(http_status=status,type='KeyIncident',message='Provider diagnostic redacted after key incident')
 return value

def validate_preflight(report,source_commit,require_fresh=True):
 if not isinstance(report,dict):raise ValueError('successful preflight required')
 allowed={'mode','status','model','settings','source_commit','run_list_sha256','requests_used','usage','spend_usd','error','events_sha256','response_ids','created_at','pair','events','usage_unverified'}
 if set(report)-allowed or not allowed-{'events_sha256'}<=set(report):raise ValueError('preflight fields differ')
 validate_settings(report['settings'])
 if (report['mode']!='preflight' or report['status']!='compatible' or report['model']!=SETTINGS['model'] or report['source_commit']!=source_commit or report['run_list_sha256']!=INPUT_SHA256['RUN-LIST-opus55-room.md'] or type(report['requests_used']) is not int or report['requests_used']!=2 or report['error'] is not None or report['usage_unverified'] is not False):raise ValueError('preflight identity/status differs')
 ids=report['response_ids']
 if not isinstance(ids,list) or len(ids)!=2 or any(not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,200}',value) for value in ids) or len(set(ids))!=2:raise ValueError('preflight response identity differs')
 if type(report['pair']) is not int or report['pair']!=0:raise ValueError('preflight pair differs')
 try:
  created=datetime.fromisoformat(report['created_at'])
  if created.tzinfo is None or created.utcoffset().total_seconds()!=0:raise ValueError('UTC required')
  age=(datetime.now(timezone.utc)-created).total_seconds()
 except (ValueError,TypeError,AttributeError):raise ValueError('preflight creation time invalid') from None
 if age<0 or (require_fresh and age>86400):raise ValueError('preflight outside 24 hour window')
 events=report['events']
 if not isinstance(events,list):raise ValueError('preflight events differ')
 derive_records(events,build_plan()[:1]);validate_recorded_scale(events)
 metadata=reviewer.view_metadata((HERE/build_plan()[0]['image']).read_bytes(),policy=reviewer.ViewPolicy.CALIBRATION)
 views=reviewer.neutral_views((HERE/build_plan()[0]['image']).read_bytes(),policy=reviewer.ViewPolicy.CALIBRATION)
 expected=json.loads(reviewer.request_record([{'role':'user','content':reviewer.content(views)}]))[0]
 for event in events:
  if not event['kind'].endswith('-request'):continue
  if any(event.get(k)!=v for k,v in metadata.items()):raise ValueError('preflight view identity differs')
  messages=json.loads(event['content'])
  if not isinstance(messages,list) or len(messages)<2 or messages[1]!=expected:raise ValueError('preflight view identity differs')
 usage=report['usage']
 if not isinstance(usage,dict) or set(usage)!={'prompt_tokens','completion_tokens','total_tokens'} or any(type(v) is not int or v<0 for v in usage.values()) or usage['total_tokens']!=usage['prompt_tokens']+usage['completion_tokens']:raise ValueError('preflight usage invalid')
 if usage!={key:sum(event['usage'][key] for event in events if event['kind'].endswith('-usage')) for key in usage}:raise ValueError('preflight usage differs from events')
 if not isinstance(report['spend_usd'],str):raise ValueError('preflight cost invalid')
 try:cost=Decimal(report['spend_usd'])
 except InvalidOperation:raise ValueError('preflight cost invalid') from None
 if not cost.is_finite() or cost!=estimate_spend(usage['prompt_tokens'],usage['completion_tokens']) or cost>=Decimal(SETTINGS['hard_stop_usd']):raise ValueError('preflight cost differs')
 return report

def preflight(relay,source_commit):
 """One real registered pair, using the strict reviewer; operator only, no retry."""
 pairs=build_plan();validate_settings(SETTINGS)
 if (type(relay) is not Relay or getattr(relay.review_request,'__func__',None) is not Relay.review_request or relay.model!=SETTINGS['model'] or relay.routes!={(SETTINGS['host'],SETTINGS['path']):'model'} or getattr(relay,'cache_prefix',None) is not None or relay.calls!=0 or relay.turn_limit!=2 or getattr(relay,'review_max_tokens',256)!=SETTINGS['review_max_tokens'] or getattr(relay,'review_temperature',0) is not SETTINGS['temperature']):raise ValueError('fresh two-request registered relay required')
 report=dict(mode='preflight',status='rejected',model=SETTINGS['model'],settings=copy.deepcopy(SETTINGS),source_commit=source_commit,run_list_sha256=INPUT_SHA256['RUN-LIST-opus55-room.md'],requests_used=0,usage=None,spend_usd=None,error=None,response_ids=[],created_at=datetime.now(timezone.utc).isoformat(),pair=0,events=[],usage_unverified=False)
 pair=pairs[0];events=report['events'];usage={'prompt_tokens':0,'completion_tokens':0,'total_tokens':0}
 relay.last_http_status=None
 try:
  data=(HERE/pair['image']).read_bytes();metadata=reviewer.view_metadata(data,policy=reviewer.ViewPolicy.CALIBRATION)
  views=reviewer.neutral_views(data,policy=reviewer.ViewPolicy.CALIBRATION)
  if metadata['scale']!=SETTINGS['scale'] or any(list(reviewer.png_dimensions(v))!=metadata['dimensions'] for v in views):raise ValueError('view dimensions differ')
  def record(kind,content,tokens):
   event=dict(kind=kind,pair=0,content=content,usage=tokens)
   if kind.endswith('-request'):event.update(metadata)
   if relay.output_has_key(json.dumps(event,ensure_ascii=False).encode()):
    relay.incident=True;raise ValueError('key incident in decoded preflight response')
   events.append(event)
  def transport(messages,max_tokens):
   if report['requests_used']>=2 or (report['spend_usd'] is not None and Decimal(report['spend_usd'])>=Decimal(SETTINGS['hard_stop_usd'])):raise ValueError('request or spend ceiling')
   report['requests_used']+=1;relay.last_http_status=None
   try:value=relay.review_request(messages,SETTINGS['review_max_tokens'])
   except Exception:
    report['usage_unverified']=True;raise
   if relay.output_has_key(json.dumps(value,ensure_ascii=False).encode()):
    relay.incident=True;raise ValueError('key incident in decoded preflight response')
   tokens=value.get('usage') if isinstance(value,dict) else None
   if not isinstance(tokens,dict) or set(tokens)!=set(usage) or any(type(v) is not int or v<0 for v in tokens.values()) or tokens['total_tokens']!=tokens['prompt_tokens']+tokens['completion_tokens']:
    report['usage_unverified']=True;raise ValueError('preflight usage invalid')
   for key in usage:usage[key]+=tokens[key]
   report.update(usage=dict(usage),spend_usd=str(estimate_spend(usage['prompt_tokens'],usage['completion_tokens'])))
   identity=value.get('id')
   if not isinstance(identity,str) or not re.fullmatch(r'[A-Za-z0-9_.:-]{1,200}',identity) or identity in report['response_ids']:raise ValueError('preflight response identity differs')
   report['response_ids'].append(identity)
   if Decimal(report['spend_usd'])>=Decimal(SETTINGS['hard_stop_usd']):raise ValueError('hard spend stop reached')
   choices=value.get('choices')
   if isinstance(choices,list) and len(choices)==1 and isinstance(choices[0],dict) and isinstance(choices[0].get('message'),dict) and choices[0]['message'].get('refusal'):raise ValueError('provider refusal')
   return value
  reviewer.review(views,pair['item'],SETTINGS['model'],transport,record)
  report['status']='compatible';validate_preflight(report,source_commit)
 except Exception as error:
  report['error']=stop_error(error,relay);report['status']='incident' if relay.incident else 'rejected'
  if relay.incident:report['events']=[];report['response_ids']=[]
 return report

def persist_preflight(relay,report,output):
 output=Path(output);validate_run_id(output.name)
 events=report['events']+[dict(kind='preflight-result',status=report['status'],response_ids=report['response_ids'],created_at=report['created_at'],usage=report['usage'],spend_usd=report['spend_usd'],error=report['error'])]
 body=''.join(json.dumps(e,ensure_ascii=True)+'\n' for e in events).encode()
 receipt=dict(report,events_sha256=hashlib.sha256(body).hexdigest());encoded=(json.dumps(receipt,ensure_ascii=True,indent=2)+'\n').encode()
 if relay.output_has_key(body) or relay.output_has_key(encoded):raise ValueError('preflight artifact key incident')
 output.mkdir(mode=0o700,exist_ok=False)
 for name,data in [('events.jsonl',body),('receipt.json',encoded)]:
  with (output/name).open('xb') as stream:stream.write(data);stream.flush()
 if (output/'events.jsonl').read_bytes()!=body or (output/'receipt.json').read_bytes()!=encoded:raise ValueError('preflight readback differs')
 return receipt

def load_preflight(path,source_commit):
 path=Path(path);root=path.parent
 if path.name!='receipt.json' or path.is_symlink() or root.is_symlink() or {p.name for p in root.iterdir()}!={'receipt.json','events.jsonl'} or (root/'events.jsonl').is_symlink():raise ValueError('preflight inventory differs')
 if path.stat().st_size>65536 or (root/'events.jsonl').stat().st_size>65536:raise ValueError('preflight artifact exceeds limit')
 report=json.loads(path.read_bytes());validate_preflight(report,source_commit)
 if report.get('events_sha256')!=hashlib.sha256((root/'events.jsonl').read_bytes()).hexdigest():raise ValueError('preflight events changed')
 return report

def main():
 parser=argparse.ArgumentParser(description='Fixed calibration batch; operator execution only after independent review.')
 mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument('--preflight',action='store_true');mode.add_argument('--dry-run',action='store_true');mode.add_argument('--run',action='store_true');mode.add_argument('--verify',type=Path)
 parser.add_argument('--output',type=Path,help='new directory whose final component is the run id')
 parser.add_argument('--preflight-receipt',type=Path,help='compatible receipt for this source commit and registered settings')
 parser.add_argument('--baseline',type=Path,help='previous records.json for unchanged disk comparison')
 parser.add_argument('--key-fds',help='JSON mapping exact host to inherited FD; never key values')
 args=parser.parse_args()
 try:
  if args.verify:
   receipt=verify_receipt(args.verify);print(json.dumps({'status':receipt['status'],'run_id':receipt['run_id'],'review_gate':False}));return 0
  validate_settings(SETTINGS);pairs=build_plan()
  if args.dry_run:
   if args.key_fds is not None:raise ValueError('dry run cannot take descriptors')
   print(json.dumps({'settings':SETTINGS,'pairs':[{k:v for k,v in pair.items() if k!='item'} for pair in pairs],'requests':2*len(pairs),'provider_calls':0},indent=2));return 0
  if args.output is None or args.key_fds is None:raise ValueError('live mode requires output and inherited descriptors')
  commit=SOURCE_COMMIT or source_identity()
  proof=None
  if not args.preflight:
   if args.baseline is None or args.preflight_receipt is None:raise ValueError('run requires baseline and preflight receipt')
   proof=load_preflight(args.preflight_receipt,commit)
  with tempfile.TemporaryDirectory(prefix='calibration-relay-') as directory:
   relay=build_relay(Path(directory)/'api.sock',json.loads(args.key_fds),preflight=args.preflight)
   try:
    if args.preflight:
     report=preflight(relay,commit);persist_preflight(relay,report,args.output)
    else:report=run_batch(relay,args.output,args.baseline,commit,preflight=proof)
   finally:relay.server_close()
  print(json.dumps(report));return 0 if report['status'] in ('complete','compatible') else 1
 except (OSError,ValueError,TypeError,KeyError,subprocess.SubprocessError) as error:
  print(json.dumps({'status':'partial','reason':type(error).__name__}));return 2
if __name__=='__main__':sys.exit(main())
