#!/usr/bin/env python3
"""Exercise legacy and native usage through actual consumers; no socket/provider."""
import io,json,subprocess,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import agent,cache_api,common,reviewer,run,selftest
MODEL='claude-sonnet-4-5-20250929'
def check():
 legacy={'prompt_tokens':10,'completion_tokens':2,'total_tokens':12}
 extended=cache_api.receipt(legacy,MODEL);assert set(legacy)<set(extended)
 assert cache_api.usage(extended)==cache_api.usage(legacy)
 counters=[];packets=[]
 class Response:
  status=200
  def read(self,_):
   return json.dumps({'model':MODEL,'choices':[{'finish_reason':'stop','message':{'role':'assistant','content':'fixture only','_native_content':[{'type':'text','text':'fixture only'}]}}],'usage':extended}).encode()
 class Connection:
  def __init__(self,*args,**kwargs):pass
  def request(self,*args,**kwargs):packets.append(args[2])
  def getresponse(self):return Response()
  def close(self):pass
 with patch.object(agent.Path,'read_text',return_value='fixed synthetic brief'),patch.object(agent,'UnixHTTP',Connection),patch.object(agent,'emit',side_effect=lambda kind,**v:counters.append({'type':kind,**v})),patch.object(sys,'argv',['agent.py','--model',MODEL,'--host','api.example.test']):assert agent.main()==0
 assert counters[-1]['usage']['total_tokens']==12 and counters[1]['usage']['uncached_input_tokens']==10
 # The same codec is used for protected supervisor event/capture transport.
 assert common.read_frame(io.BytesIO(common.encode({'type':'event','event':counters[1]})))['event']['usage']==cache_api.usage(extended)
 assert reviewer.response(json.loads(Response().read(1)),MODEL)[1]==cache_api.usage(extended)
 assert run.checked_usage(extended)==cache_api.usage(extended)
 with tempfile.TemporaryDirectory() as directory:
  root=Path(directory);output=root/'output';output.mkdir()
  result={'status':'failed','reason':'synthetic 413 or later protocol failure','usage':extended}
  run.failed_capture(root,output,result,counters,['synthetic transcript'],[],[])
  captured=output/'scratch/.run'
  assert json.loads((captured/'usage.json').read_text())==extended
  assert json.loads((captured/'run.json').read_text())['usage']==extended
  assert result['key_scan']=='passed'
  # Actual self-test checker is schema-agnostic for usage; it requires the file.
  (captured/'proxy.log').write_text('{"status":"DENIED"}\n');expected=root/'expected.json';expected.write_text('{"phase":"after-drain"}')
  script=root/'check.py';script.write_text(selftest.CHECKER)
  got=json.loads(subprocess.check_output([sys.executable,str(script),str(output/'scratch'),str(expected)]));assert all(r['pass'] for r in got['rules'])
 # Calibration's exact three-key contract and writer OFF validation both matter.
 assert reviewer.reported_usage({'usage':legacy})==legacy
 assert run.event_usage(legacy,False)==legacy
 assert run.result_usage(legacy,MODEL,False)==legacy
 inconsistent=dict(legacy,total_tokens=99)
 assert run.event_usage(inconsistent,False)==inconsistent
 for malformed in ({},dict(legacy,prompt_tokens=True),dict(legacy,prompt_tokens=-1)):
  try:run.event_usage(malformed,False)
  except ValueError:pass
  else:raise AssertionError('invalid OFF usage accepted')
 try:run.event_usage(inconsistent,True)
 except ValueError:pass
 else:raise AssertionError('native totals were not checked')
 # Run the actual agent against a compatibility response, including legacy totals.
 class LegacyResponse(Response):
  def read(self,_):return json.dumps({'choices':[{'message':{'content':'fixture only'}}],'usage':inconsistent}).encode()
 with patch.object(agent.Path,'read_text',return_value='fixed synthetic brief'),patch.object(agent,'UnixHTTP',Connection),patch.object(Connection,'getresponse',return_value=LegacyResponse()),patch.object(agent,'emit',side_effect=lambda kind,**v:counters.append({'type':kind,**v})),patch.object(sys,'argv',['agent.py','--model',MODEL,'--host','api.example.test']):assert agent.main()==0
 assert counters[-1]['usage']==inconsistent and counters[-2]['usage']==inconsistent
 return {'legacy_agent_and_host_schema':'pass','calibration_reviewer_three_keys':'pass','agent_native_response_with_additive_usage' :'pass','reviewer_usage':'pass','host_usage_parser':'pass','supervisor_frame_codec':'pass','failed_capture_usage_and_run_roundtrip':'pass','selftest_checker':'pass','external_operator_tally_scripts':'not in repository; not verified','real_provider_calls':0,'real_credentials_used':False}
if __name__=='__main__':print(json.dumps(check(),indent=2))
