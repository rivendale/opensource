#!/usr/bin/env python3
"""Actual container review-loop fixtures; synthetic HTTPS responses, no paid calls."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run
import proxy

KEY = b'SYNTHETIC-NOT-A-CREDENTIAL'
MODEL = 'synthetic-pinned-reviewer'


def test(args, mode):
    calls, writer_calls, feature_calls = [], [], []
    class Response:
        status = 200
        def read(self, _):
            payload = calls[-1]
            message = {'role': 'assistant', 'content': 'Provisional delivery.'}
            if 'tools' in payload:
                writer_calls.append(payload)
                if mode == 'text-only': message['content'] = 'Which palette should I use? Waiting for answers.'
                if len(writer_calls) % 2 and mode != 'text-only':
                    color = 'red' if len(writer_calls) == 1 else 'blue'
                    command = 'mkdir -p assets; convert -size 4x4 xc:' + color + ' PNG32:assets/coin.png'
                    if mode == 'symlink':
                        command += '; mv assets/coin.png assets/source.png; ln -s source.png assets/coin.png'
                    if mode == 'tamper':
                        command += '; (sleep 1; convert -size 4x4 xc:blue PNG32:assets/coin.png) >/dev/null 2>&1 &'
                    if mode == 'oversized-frame':
                        command += "; python3 -c \"from PIL import Image; import random; r=random.Random(0); [Image.frombytes('RGB',(320,320),r.randbytes(320*320*3)).save('assets/'+n+'.png') for n in ('a','b','c')]\""
                    message['tool_calls'] = [{'id': 'draw-' + str(len(writer_calls)), 'type': 'function',
                        'function': {'name': 'shell', 'arguments': json.dumps({'command': command})}}]
            elif payload['max_tokens'] == 128:
                if mode == 'tamper': time.sleep(2)
                serialized = json.dumps(payload['messages']).lower()
                assert 'coin' not in serialized and 'writer-only-marker' not in serialized
                assert 'dark edge' not in serialized and 'assets/' not in serialized
                assert len(payload['messages']) == 2
                assert len(payload['messages'][1]['content']) == 2
                message['content'] = '{"name":"a colored square"}'
                if mode == 'malformed': message['content'] = 'not JSON'
                if mode in ('fenced-name', 'fenced-both'): message['content'] = '```json\n' + message['content'] + '\n```'
                if mode == 'key-echo': message['content'] = KEY.decode()
            else:
                feature_calls.append(payload)
                assert payload['max_tokens'] == 256 and 'tools' not in payload
                assert payload['messages'][2]['content'] == ('```json\n{"name":"a colored square"}\n```' if mode in ('fenced-name', 'fenced-both') else '{"name":"a colored square"}')
                assert 'dark edge' in json.dumps(payload['messages'])
                accepted = mode != 'miss' and (mode != 'redraw' or len(feature_calls) > 1)
                message['content'] = json.dumps({'features': [accepted]})
                if mode in ('fenced-features', 'fenced-both'): message['content'] = '```\n' + message['content'] + '\n```'
            return json.dumps({'model': MODEL, 'choices': [{'finish_reason': 'stop', 'message': message}],
                'usage': {'prompt_tokens': 2, 'completion_tokens': 1, 'total_tokens': 3}}).encode()
    class Upstream:
        def __init__(self, host, port, **kwargs): assert host == 'api.example.test'
        def request(self, method, path, payload, headers):
            assert headers['Authorization'] == 'Bearer ' + KEY.decode()
            calls.append(json.loads(payload))
        def getresponse(self):
            if mode == 'http-error' and 'tools' not in calls[-1]:
                raise proxy.http.client.HTTPException('synthetic reviewer protocol error')
            return Response()
        def close(self): pass
    saved = proxy.http.client.HTTPSConnection
    saved_run = subprocess.run
    saved_next = run.Frames.next
    def next_frame(frames):
        frame = saved_next(frames)
        if mode == 'wrong-scale' and frame.get('type') == 'review-snapshots':
            frame['snapshots'][0]['scale'] = 4
        return frame
    run.Frames.next = next_frame
    def host_process(command, *positional, **keywords):
        if isinstance(command, (list, tuple)) and Path(str(command[0])).name in ('convert', 'magick'):
            raise AssertionError('host must not decode agent-written artwork')
        return saved_run(command, *positional, **keywords)
    proxy.http.client.HTTPSConnection = Upstream
    subprocess.run = host_process
    try:
        with tempfile.TemporaryDirectory(prefix='studio-review-case-') as temp:
            case = Path(temp)
            (case / 'inputs').mkdir()
            (case / 'brief.md').write_text('Writer-only-marker. Draw a coin in assets/coin.png.\n')
            (case / 'SKILL.md').write_text('Draw the requested image and return a provisional delivery.\n')
            (case / 'expected.json').write_text('{}')
            condition = ("not (p/'assets/coin.png').exists() and 'Waiting for answers' in (p/'.run/transcript.md').read_text()"
                         if mode == 'text-only' else "(p/'assets/coin.png').is_file()")
            (case / 'check.py').write_text("import json,pathlib,sys\np=pathlib.Path(sys.argv[1])\npassed=" + condition + "\nprint(json.dumps({'case':'synthetic-review','rules':[{'id':'fixture-artifacts','pass':passed,'measured':'fixture path','threshold':'expected state'}]}))\nsys.exit(0 if passed else 1)\n")
            plan = case / 'operator-plan.json'
            plan.write_text(json.dumps([{'file': 'assets/coin.png', 'subject_words': ['coin'],
                'features': ['Is there a dark edge?']}]))
            if mode == 'oversized-frame':
                plan.write_text(json.dumps([{'file': 'assets/' + n + '.png', 'subject_words': ['orb'],
                    'features': ['Is there a dark edge?']} for n in ('a', 'b', 'c')]))
            fd, writer = os.pipe()
            os.write(writer, KEY); os.close(writer)
            output = args.output / mode
            sys.argv = ['run.py', 'run', '--store', str(args.store), '--image', args.image,
                '--selftest', str(args.selftest), '--case', str(case), '--case-id', 'synthetic-review',
                '--skill', str(case / 'SKILL.md'), '--output', str(output), '--model', MODEL,
                '--host', 'api.example.test', '--key-fds', json.dumps({'api.example.test': fd}),
                '--review-plan', str(plan), '--review-rounds', '2', '--turns', '8']
            if mode == 'budget': sys.argv[-1] = '4'
            if mode == 'oversized-frame': sys.argv[-1] = '16'
            try: code = run.main()
            finally: os.close(fd)
            result = json.loads((output / 'result.json').read_text())
            if mode == 'key-echo':
                assert code == 1 and result['incident'] and result['key_scan'] == 'incident', result
                assert 'review_records' not in result and 'usage' not in result
                assert not (output / 'scratch').exists()
            else:
                assert result['key_scan'] == 'passed', result
                capture = json.loads((output / 'scratch/.run/run.json').read_text())
                assert KEY not in b''.join(p.read_bytes() for p in (output / 'scratch/.run').iterdir())
                if mode in ('accept', 'redraw', 'fenced-name', 'fenced-features', 'fenced-both'):
                    assert code == 0 and result['verdict'] == 'passed' and result['review_accepted'], result
                    expected_calls = 8 if mode == 'redraw' else 4
                    assert len(calls) == expected_calls and result['usage']['total_tokens'] == expected_calls * 3
                    assert len(feature_calls) == (2 if mode == 'redraw' else 1)
                    assert capture['review_records'] == result['review_records']
                    assert all(r['scale'] == 8 and r['source_dimensions'] == [4,4] and r['dimensions'] == [32,32] for r in result['review_records'])
                    if mode.startswith('fenced'):
                        names = [r['text'] for r in result['review_records'] if r['phase'] == 'blind-name']
                        features = [r['text'] for r in result['review_records'] if r['phase'] == 'features']
                        assert names and features
                        assert names[0].startswith('```') == (mode in ('fenced-name', 'fenced-both'))
                        assert features[0].startswith('```') == (mode in ('fenced-features', 'fenced-both'))
                    if mode == 'redraw':
                        assert 'Fresh-context model review' in json.dumps(writer_calls[2]['messages'])
                        hashes = {r['sha256'] for r in result['review_records']}
                        assert len(hashes) == 2
                else:
                    if mode in ('budget', 'symlink'):
                        assert code == 1 and result['status'] == 'failed' and 'verdict' not in result, result
                    else:
                        assert code == 0 and result['status'] == 'completed' and result['verdict'] == 'passed', result
                        assert result['review_accepted'] is False and result['review_gate'] is False
                    expected_calls = {'miss': 8, 'malformed': 3, 'symlink': 2, 'budget': 0, 'tamper': 4, 'text-only': 1, 'http-error': 3, 'oversized-frame': 2, 'wrong-scale': 2}[mode]
                    assert len(calls) == expected_calls, (mode, len(calls), result)
                    if calls: assert result['usage']['total_tokens'] == (6 if mode == 'http-error' else expected_calls * 3), result
                    if mode == 'wrong-scale': assert result['review_error']['message'] == 'invalid supervisor view scale or dimensions'
                    if mode == 'http-error': assert result['review_error']['type'] == 'HTTPException'
                    if mode == 'oversized-frame': assert result['review_error']['message'] == 'review snapshot frame exceeds limit'
                    if mode == 'tamper':
                        assert result['agent_exit'] == 0 and not result['review_accepted']
            return {'scenario': mode, 'passed': True, 'mock_requests': len(calls),
                'real_provider_calls': 0, 'key_scan': result['key_scan'], 'host_decoder_guard': True}
    finally:
        proxy.http.client.HTTPSConnection = saved
        subprocess.run = saved_run
        run.Frames.next = saved_next


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--store', type=Path, required=True); p.add_argument('--image', required=True)
    p.add_argument('--selftest', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = p.parse_args(); args.output.mkdir()
    results = [test(args, mode) for mode in ['accept', 'fenced-name', 'fenced-features', 'fenced-both', 'redraw', 'miss', 'malformed', 'symlink', 'budget', 'tamper', 'text-only', 'http-error', 'oversized-frame', 'wrong-scale', 'key-echo']]
    (args.output / 'receipt.json').write_text(json.dumps({'fixtures': results, 'real_provider_calls': 0}, indent=2) + '\n')
    print(json.dumps({'fixtures_passed': len(results), 'real_provider_calls': 0}))


if __name__ == '__main__': main()
