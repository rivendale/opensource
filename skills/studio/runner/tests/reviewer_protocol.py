#!/usr/bin/env python3
"""Offline candidate and agent protocol checks, no container or provider claims."""
import io
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import agent
import supervisor
from reviewer import ReviewError


def check():
    with patch.object(supervisor, 'review_snapshot', side_effect=FileNotFoundError), \
            patch.object(supervisor, 'container_views') as convert:
        snapshots = supervisor.candidate_snapshots(['assets/absent.png'])
        assert snapshots == [{'file': 'assets/absent.png', 'error': 'export not present'}]
        convert.assert_not_called()
    for error in (OSError('unsafe file'), ReviewError('invalid PNG')):
        with patch.object(supervisor, 'review_snapshot', side_effect=error):
            assert 'error' in supervisor.candidate_snapshots(['assets/unsafe.png'])[0]
    with patch.object(supervisor, 'review_snapshot', return_value=b'original'), \
            patch.object(supervisor, 'container_views', return_value=[b'grey', b'light']), \
            patch.object(supervisor, 'view_metadata', return_value={'source_dimensions':[16,16],'scale':8,'dimensions':[128,128]}):
        snapshots = supervisor.candidate_snapshots(['assets/render.png'])
        assert 'data' not in snapshots[0] and len(snapshots[0]['views']) == 2
        assert len(snapshots[0]['sha256']) == 64
    with patch.object(supervisor, 'review_snapshot', return_value=b'original'), \
            patch.object(supervisor, 'container_views', return_value=[b'x' * (512 * 1024)] * 2), \
            patch.object(supervisor, 'view_metadata', return_value={'source_dimensions':[16,16],'scale':8,'dimensions':[128,128]}):
        snapshots = supervisor.candidate_snapshots(['assets/a.png', 'assets/b.png'])
        assert len(snapshots) == 2 and all(s['error'] == 'review snapshot frame exceeds limit' for s in snapshots)
        assert len(supervisor.encode({'type': 'review-snapshots', 'snapshots': snapshots})) < 1024

    class Response:
        status = 200
        def read(self, _):
            return json.dumps({'choices': [{'message': {'role': 'assistant',
                'content': 'Which palette should I use?'}}],
                'usage': {'prompt_tokens': 2, 'completion_tokens': 1, 'total_tokens': 3}}).encode()
    class Connection:
        def __init__(self, *_args, **_kwargs): pass
        def request(self, *_args, **_kwargs): pass
        def getresponse(self): return Response()
        def close(self): pass
    events = []
    feedback = io.StringIO(json.dumps({'accepted': False, 'stop': True,
        'feedback': 'No export available; retain the checker verdict.'}) + '\n')
    with patch.object(agent.Path, 'read_text', return_value='synthetic brief or skill'), \
            patch.object(agent, 'UnixHTTP', Connection), \
            patch.object(agent, 'emit', side_effect=lambda kind, **values: events.append({'type': kind, **values})), \
            patch.object(sys, 'stdin', feedback), \
            patch.object(sys, 'argv', ['agent.py', '--model', 'synthetic', '--host', 'api.example.test', '--review-feedback']):
        assert agent.main() == 0
    assert [e['type'] for e in events] == ['identity', 'assistant', 'candidate', 'review-ended', 'finished']
    assert events[-1]['usage']['total_tokens'] == 3 and not any(e['type'] == 'failed' for e in events)
    print('offline missing-export and review-ended agent protocol checks passed')


if __name__ == '__main__': check()
