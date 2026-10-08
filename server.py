"""Local-only review UI. This server never invokes cloud providers."""
import json
import math
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from core import evaluate
from compare import compare, measurements

ROOT = Path(__file__).parent
WEB = ROOT / 'web'


def review(trace):
    if not isinstance(trace, dict) or not isinstance(trace.get('events'), list):
        raise ValueError('Expected a trace object with an events list')
    if not trace['events'] or len(trace['events']) > 1000:
        raise ValueError('Trace must contain 1–1000 events')
    if not all(isinstance(trace.get(k), str) for k in ['id', 'source']):
        raise ValueError('Trace ID and source must be strings')
    policy = trace.get('expectations', {})
    if not isinstance(policy, dict):
        raise ValueError('Expectations must be an object')
    budget = policy.get('interrupt_stop_budget_ms')
    limits = policy.get('max_tool_calls')
    if (not isinstance(budget, (int, float)) or isinstance(budget, bool)
            or not math.isfinite(budget) or budget < 0):
        raise ValueError('Stop budget must be a finite nonnegative number')
    if not isinstance(limits, dict) or any(not isinstance(v, int) or isinstance(v, bool) or v < 0
                                          for v in limits.values()):
        raise ValueError('Tool call limits must be nonnegative integers')
    for event in trace['events']:
        if not isinstance(event, dict) or not isinstance(event.get('id'), str):
            raise ValueError('Every event needs a string ID')
        if (not isinstance(event.get('time_ms'), (int, float))
                or isinstance(event['time_ms'], bool) or not math.isfinite(event['time_ms'])):
            raise ValueError('Every event needs a numeric timestamp')
        if not isinstance(event.get('type'), str):
            raise ValueError('Every event needs a string type')
        if event['type'] == 'tool_call' and not isinstance(event.get('name'), str):
            raise ValueError('Tool call name must be a string')
    return {**evaluate(trace), **measurements(trace), 'events': trace['events']}


def demo():
    traces = [json.loads((ROOT / 'fixtures' / f'{name}-interruption.json').read_text())
              for name in ['slow', 'normal']]
    cloud = []
    for name in ['slow', 'normal']:
        reports = ROOT / '.runtime/reports'
        dated = sorted(reports.glob(f'{name}-interruption-nebius-20*.json'))
        path = dated[-1] if dated else reports / f'{name}-interruption-nebius.json'
        if not path.exists():
            path = ROOT / 'assets/recorded' / f'{name}-interruption-nebius.json'
        if path.exists():
            cloud.append({'fixture': name, 'recorded_on': '2026-10-08', **json.loads(path.read_text())})
    for name in ['cancel-none', 'cancel-ignore_cancel', 'change-date-wrong_date']:
        extra = ROOT / '.runtime/audio-suite' / (name+'-nebius.json')
        if not extra.exists():
            extra = ROOT / 'assets/recorded' / (name+'-nebius.json')
        if extra.exists():
            cloud.append({'fixture': name, 'recorded_on': '2026-10-09', **json.loads(extra.read_text())})
    suite = ROOT / '.runtime/audio-suite/suite.json'
    if not suite.exists():
        suite = ROOT / 'assets/recorded/suite.json'
    audio_replays = json.loads(suite.read_text()) if suite.exists() else []
    return {'traces': traces, 'reports': [review(t) for t in traces],
            'comparison': compare(*traces), 'cloud_history': cloud, 'audio_replays': audio_replays}


class Handler(BaseHTTPRequestHandler):
    def reply(self, value, status=200):
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path in ('/api/demo', '/data/demo.json'):
            return self.reply(demo())
        resources = {'/': (WEB / 'index.html', 'text/html'),
                     '/app.js': (WEB / 'app.js', 'text/javascript'),
                     '/engine.mjs': (WEB / 'engine.mjs', 'text/javascript'),
                     '/style.css': (WEB / 'style.css', 'text/css'),
                     '/audio/change-date.wav': (ROOT / 'assets/audio/change-date.wav', 'audio/wav'),
                     '/audio/cancel.wav': (ROOT / 'assets/audio/cancel.wav', 'audio/wav')}
        for name in ['change-date-none', 'change-date-wrong_date', 'cancel-none', 'cancel-ignore_cancel']:
            resources['/audio/'+name+'-response.wav'] = (ROOT / 'assets/audio' / (name+'-response.wav'), 'audio/wav')
        if self.path not in resources or not resources[self.path][0].exists():
            return self.reply({'error': 'Not found'}, 404)
        path, mime = resources[self.path]
        data = path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != '/api/review':
            return self.reply({'error': 'Not found'}, 404)
        if self.headers.get('Origin') not in (None, 'http://127.0.0.1:4187', 'http://localhost:4187'):
            return self.reply({'error': 'Local workspace only'}, 403)
        try:
            length = int(self.headers.get('Content-Length', 0))
            if not 0 < length <= 131072:
                raise ValueError('Trace size limit is 128 KB')
            self.reply(review(json.loads(self.rfile.read(length))))
        except (ValueError, TypeError, KeyError) as exc:
            self.reply({'error': str(exc)}, 400)

    def log_message(self, *args):
        pass


if __name__ == '__main__':
    print('TurnProof local workspace: http://127.0.0.1:4187/', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 4187), Handler).serve_forever()
