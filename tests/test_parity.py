"""The Python port sends exactly what the JS client sends.

tests/golden.json is written by `node tests/harness.js` from tests/cases.json. This test runs the same cases through
sdc.Session against the same stubbed server and compares every call (actions, partialRetrieval nodes, /api bodies).
Run: python3 -m unittest discover tests
"""
import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlencode

from sdc.session import Session

HERE = Path(__file__).parent
SERVER = (HERE / 'fixtures' / 'server.json').read_text()
CASES = json.loads((HERE / 'cases.json').read_text())
GOLDEN = json.loads((HERE / 'golden.json').read_text())
NOW = 1763800000000


def snake(name):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


class FakeTransport:
    def __init__(self):
        self.log = []

    def task(self, params):
        # Round-trip through form encoding, as the real request does.
        p = dict(x.split('=', 1) for x in urlencode(params).split('&'))
        from urllib.parse import unquote_plus
        p = {k: unquote_plus(v) for k, v in p.items()}
        if p['taskId'] == 'mojoRWManipulation':
            params_json = json.loads(p['params'])
            self.log.append({'edit': {'actions': params_json['actions'], 'nodes': params_json['partialRetrieval']['nodes'],
                                      'rwb': p['rwb']}})
            return '{"bs":"BS1"}'
        self.log.append({'task': p['taskId'], 'excludeData': p.get('excludeData')})
        return SERVER

    def api(self, method, path, body=None):
        self.log.append({'api': method, 'path': path, 'body': json.loads(json.dumps(body)) if body is not None else None})
        return {'id': 'NEW', 'mid': 'MID'}


def key_gen():
    n = [0]

    def k():
        b = bytes(((n[0] * 16 + i) & 255) for i in range(16))
        n[0] += 1
        return b.hex().upper()
    return k


class Parity(unittest.TestCase):
    pass


def make_test(case):
    def test(self):
        t = FakeTransport()
        s = Session(t, 'DASH', 'MID', now=lambda: NOW, key32=key_gen())
        t.log = []
        method = getattr(s, case.get('py') or snake(case['js']))
        kwargs = {snake(k): v for k, v in (case.get('opts') or {}).items()}
        try:
            result = method(*case.get('args', []), **kwargs)
        except Exception as e:  # noqa: BLE001
            result = {'error': str(e)}
        want = GOLDEN[case['name']]
        self.assertEqual(len(t.log), len(want['calls']), 'number of calls')
        for i, (got, exp) in enumerate(zip(t.log, want['calls'])):
            self.assertEqual(got, exp, f'call {i}')
        if not isinstance(result, str):
            self.assertEqual(json.loads(json.dumps(result)), want['result'])
    return test


for _c in CASES:
    setattr(Parity, 'test_' + _c['name'], make_test(_c))


if __name__ == '__main__':
    unittest.main()
