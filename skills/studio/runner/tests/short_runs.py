#!/usr/bin/env python3
"""One-response and failure-capture regressions in the actual isolated runner.

Uses a synthetic in-process HTTPS mock, never an external provider or real key.
Requires a freshly passed selftest for the selected image and this host run.py.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run
import proxy

KEY = b'SYNTHETIC-NOT-A-CREDENTIAL'
CHECKER = '''import json,pathlib,sys
p=pathlib.Path(sys.argv[1])
rules=[{'id':'questions-reach-checker','pass':'Waiting for answers' in (p/'.run/transcript.md').read_text(),
'measured':'one response, zero tool calls','threshold':'question transcript captured'},
{'id':'no-exports-required','pass':not (p/'assets').exists(), 'measured':'no exports','threshold':'none'}]
print(json.dumps({'case':'synthetic-one-response','rules':rules}))
'''


def test(args, mode):
    calls = []
    class Response:
        status = 200
        def read(self, _):
            return json.dumps({'choices':[{'message':{'role':'assistant',
                'content':'Which size and palette should I use? Waiting for answers.'}}],
                'usage':{'prompt_tokens':2,'completion_tokens':1,'total_tokens':3}}).encode()
    class Upstream:
        def __init__(self, host, port, **kwargs):
            assert host == 'api.example.test'
        def request(self, method, path, payload, headers):
            assert headers['Authorization'] == 'Bearer ' + KEY.decode()
            calls.append(True)
        def getresponse(self): return Response()
        def close(self): pass
    saved_upstream = proxy.http.client.HTTPSConnection
    saved_capture, saved_checker, saved_runtime = run.capture, run.checker_result, run.Runtime
    proxy.http.client.HTTPSConnection = Upstream
    if mode == 'preflight-error':
        def refused(*_): raise RuntimeError('synthetic preflight failure')
        run.Runtime = refused
    if mode == 'capture-error':
        def refused(*_): raise RuntimeError('synthetic capture transport failure')
        run.capture = refused
    if mode == 'checker-error':
        def refused(*_): raise ValueError('synthetic checker result failure')
        run.checker_result = refused
    try:
        with tempfile.TemporaryDirectory(prefix='studio-short-case-') as temp:
            case = Path(temp)
            (case/'inputs').mkdir()
            (case/'brief.md').write_text('Synthetic question-ending runner transport fixture.\n')
            (case/'SKILL.md').write_text('Ask which size and palette, then wait for answers.\n')
            (case/'expected.json').write_text('{}')
            (case/'check.py').write_text(CHECKER)
            fd, writer = os.pipe()
            os.write(writer, KEY); os.close(writer)
            output = args.output / mode
            sys.argv = ['run.py','run','--store',str(args.store),'--image',args.image,
                '--selftest',str(args.selftest),'--case',str(case),'--case-id','synthetic-one-response',
                '--skill',str(case/'SKILL.md'),'--output',str(output),
                '--model','synthetic-pinned-one-response','--host','api.example.test',
                '--key-fds',json.dumps({'api.example.test':fd})]
            try: code = run.main()
            finally: os.close(fd)
            result = json.loads((output/'result.json').read_text())
            capture = json.loads((output/'scratch/.run/run.json').read_text())
            if mode == 'preflight-error':
                assert code == 1 and not calls and result['key_scan'] == 'passed'
                assert result['exception']['message'] == 'synthetic preflight failure'
                assert result['capture_scope'] == 'host-received-events-only' and capture['events'] == []
                return {'scenario':mode,'passed':True,'mock_requests':0,'real_requests':0,'key_scan':'passed','capture_scope':result['capture_scope']}
            assert len(calls) == 1 and result['usage']['total_tokens'] == 3
            assert result['agent_exit'] == 0 and result['key_scan'] == 'passed'
            assert len([e for e in capture['events'] if e['type']=='assistant']) == 1
            assert not any(e['type']=='tool' for e in capture['events'])
            assert all((output/'scratch/.run'/name).is_file() for name in
                       ['transcript.md','run.json','usage.json','proxy.log'])
            assert KEY not in b''.join(p.read_bytes() for p in (output/'scratch/.run').iterdir())
            if mode == 'questions':
                assert code == 0 and result['status'] == 'passed' and all(r['pass'] for r in result['checker']['rules'])
            else:
                assert code == 1 and result['status'] == 'failed'
                assert result['exception']['type'] == ('RuntimeError' if mode=='capture-error' else 'ValueError')
                assert 'synthetic' in result['exception']['message']
                assert capture['exception'] == result['exception']
                assert result['capture_scope'] == ('host-received-events-only' if mode=='capture-error' else 'drained-scratch-snapshot')
            return {'scenario':mode,'passed':True,'mock_requests':len(calls),'real_requests':0,
                    'key_scan':result['key_scan'],'capture_scope':result.get('capture_scope','final-scratch-snapshot')}
    finally:
        proxy.http.client.HTTPSConnection = saved_upstream
        run.capture, run.checker_result, run.Runtime = saved_capture, saved_checker, saved_runtime


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--store',type=Path,required=True);p.add_argument('--image',required=True)
    p.add_argument('--selftest',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(); args.output.mkdir()
    # Redaction occurs before truncation, including embedded exact and pattern values.
    diagnostic=run.exception_receipt(ValueError('prefix '+KEY.decode()+' '+'sk-'+'x'*20),[KEY])
    assert KEY.decode() not in diagnostic['message'] and 'sk-' not in diagnostic['message']
    with tempfile.TemporaryDirectory(prefix='studio-scan-fixture-') as temp:
        root=Path(temp);out=root/'out';out.mkdir()
        result={'status':'failed','reason':'synthetic','usage':{'total_tokens':3}}
        run.failed_capture(root,out,result,[],['sk-'+'x'*20],[],[])
        assert result['incident'] and result['key_scan']=='incident' and not (out/'scratch').exists()
    results=[test(args,mode) for mode in ['questions','capture-error','checker-error','preflight-error']]
    (args.output/'receipt.json').write_text(json.dumps({'fixtures':results,'diagnostic_redaction':'passed',
        'pattern_scan_suppression':'passed','real_provider_calls':0},indent=2)+'\n')
    print(json.dumps({'fixtures_passed':len(results),'real_provider_calls':0}))

if __name__=='__main__':main()
