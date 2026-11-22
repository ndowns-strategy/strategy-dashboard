"""Auth spike: can plain Python (requests) drive the dashboard editor without a browser?

Checks, in order, stopping at the first failure:
  1. POST /api/auth/login with credentials from .env  -> X-MSTR-AuthToken + session cookies
  2. GET  /api/sessions/userInfo                        -> the session is real
  3. POST /api/dossiers/draft/instances                 -> a new unsaved dashboard (REST)
  4. taskProc getServerJSONResults                      -> the servlet accepts a REST-login session
  5. taskProc mojoRWManipulation (add one text box)     -> an editor action works
  6. POST /api/documents/{id}/instances/{mid}/saveAs    -> saved into My Reports
  7. GET  /api/v2/dossiers/{id}/definition              -> the saved dashboard reads back
  8. DELETE the spike dashboard (skip with --keep), then log out

Credentials come from strategy-dashboard/.env (gitignored); see .env.example. Run:
  python3 spike/auth_spike.py [--keep]
"""
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
APP_ID = 'C2B2023642F6753A2EF159A75E0CFF29'  # applicationId the Library app sends on this server
PAGE_KEY = 'K53'                              # page key on the blank template


def load_env():
    env = {}
    p = ROOT / '.env'
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    for k in list(env) + ['SDC_BASE_URL', 'SDC_USERNAME', 'SDC_PASSWORD', 'SDC_LOGIN_MODE', 'SDC_PROJECT_ID']:
        if os.environ.get(k):
            env[k] = os.environ[k]
    missing = [k for k in ('SDC_BASE_URL', 'SDC_USERNAME', 'SDC_PASSWORD', 'SDC_PROJECT_ID') if not env.get(k)]
    if missing:
        sys.exit(f'Missing in .env: {", ".join(missing)} (copy .env.example to .env and fill it in)')
    return env


def step(n, name):
    print(f'[{n}] {name} ... ', end='', flush=True)


def ok(detail=''):
    print('PASS' + (f'  {detail}' if detail else ''))


def fail(detail):
    print('FAIL')
    print('    ' + str(detail)[:600])
    sys.exit(1)


def main():
    keep = '--keep' in sys.argv
    env = load_env()
    base = env['SDC_BASE_URL'].rstrip('/')       # e.g. https://studio.strategy.com/MicroStrategyLibrary
    project = env['SDC_PROJECT_ID']
    s = requests.Session()
    s.headers.update({'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'})

    def api(method, path, body=None, expect_json=True):
        r = s.request(method, f'{base}/api{path}', json=body)
        if not r.ok:
            raise RuntimeError(f'{method} {path} -> {r.status_code} {r.text[:400]}')
        return r.json() if expect_json and r.text else r

    def task(params):
        data = {'taskEnv': 'xhr', 'taskContentType': 'json', 'jsonMode': 'true',
                'xts': str(int(time.time() * 1000)), 'mstrWeb': 'random', **params}
        r = s.post(f'{base}/servlet/taskProc', data=data,
                   headers={'Content-type': 'application/x-www-form-urlencoded'})
        if not r.ok or not r.text:
            raise RuntimeError(f'taskProc {params["taskId"]} -> {r.status_code} '
                               f'code={r.headers.get("x-mstr-taskerrorcode")} body={r.text[:300]}')
        return r.text

    # 1. Login
    step(1, f'login (loginMode {env.get("SDC_LOGIN_MODE", "1")})')
    try:
        r = s.post(f'{base}/api/auth/login', json={
            'username': env['SDC_USERNAME'], 'password': env['SDC_PASSWORD'],
            'loginMode': int(env.get('SDC_LOGIN_MODE', '1')), 'applicationType': 35})
        if r.status_code != 204:
            fail(f'{r.status_code} {r.text}')
        token = r.headers.get('X-MSTR-AuthToken')
        if not token:
            fail('no X-MSTR-AuthToken header')
        s.headers.update({'X-MSTR-AuthToken': token, 'X-MSTR-ProjectID': project})
        ok(f'cookies: {", ".join(sorted(s.cookies.keys())) or "none"}')
    except requests.RequestException as e:
        fail(e)

    dashboard_id = None
    try:
        # 2. Session check
        step(2, 'userInfo')
        u = api('GET', '/sessions/userInfo')
        ok(f'signed in as {u.get("fullName") or u.get("username")}')

        # 3. Draft dashboard (no dataset needed for this test)
        step(3, 'new draft dashboard')
        d = api('POST', '/dossiers/draft/instances', {'filters': None, 'persistViewState': False,
                                                       'resolveOnly': False, 'applicationId': APP_ID, 'datasets': []})
        draft_id, mid = d.get('id'), d['mid']
        ok(f'mid {mid[:12]}...')

        # 4. Load the instance into the web bean
        step(4, 'taskProc getServerJSONResults')
        g = task({'taskId': 'getServerJSONResults', 'messageID': mid, 'styleName': 'ServerJsonRWDStyle',
                  'resFlags': '0', 'excludeData': 'false', 'supportsUndo': 'true', 'compress': '1',
                  'innerHeight': '857', 'innerWidth': '1920'})
        m = re.search(r'"bs":"([^"]+)"', g)
        if not m:
            fail(f'no bs in response: {g[:300]}')
        bs = m.group(1)
        ok(f'{len(g):,} bytes')

        # 5. One editor action: add a plain text box
        step(5, 'taskProc mojoRWManipulation (add text box)')
        node, field, text = 'W90', 'W91', 'Auth spike: built from Python'
        actions = [
            {'act': 'addField', 'createNode': True, 'nodeKeyParent': PAGE_KEY, 'fieldKey': field, 'fieldType': 3,
             'nodeKey': node, 'treeType': 1, 'fieldName': field},
            {'act': 'editField', 'fieldValue': text, 'fieldKey': field, 'fieldType': 3, 'nodeKey': node,
             'treeType': 1, 'fieldName': field},
        ]
        t = task({'taskId': 'mojoRWManipulation', 'messageID': mid, 'rwb': bs, 'stateID': '-1',
                  'styleName': 'RWIVEMojoStyle', 'zoomFactor': '1',
                  'params': json.dumps({'actions': actions, 'partialRetrieval': {'nodes': [PAGE_KEY]},
                                        'style': {'params': {'treesToRender': 2}, 'name': 'RWIVEMojoStyle'}})})
        ok(f'{len(t):,} bytes, new bs: {"yes" if re.search(r"\"bs\":\"", t) else "no"}')

        # 6. Save As into My Reports
        step(6, 'saveAs into My Reports')
        folder = next(f['id'] for f in api('GET', '/folders/myPersonalObjects') if f['name'] == 'My Reports')
        name = f'SDC auth spike {time.strftime("%Y-%m-%d %H%M%S")}'
        saved = api('POST', f'/documents/{draft_id}/instances/{mid}/saveAs',
                    {'name': name, 'folderId': folder, 'saveAsTemplate': False})
        dashboard_id = saved['id']
        ok(f'"{name}" id {dashboard_id}')

        # 7. Read it back
        step(7, 'read definition back')
        defn = api('GET', f'/v2/dossiers/{dashboard_id}/definition')
        r = s.post(f'{base}/api/dossiers/{dashboard_id}/instances',
                   json={'persistViewState': False, 'resolveOnly': False, 'applicationId': APP_ID})
        found = False
        if r.ok:
            g2 = task({'taskId': 'getServerJSONResults', 'messageID': r.json()['mid'], 'styleName': 'ServerJsonRWDStyle',
                       'resFlags': '0', 'excludeData': 'false', 'supportsUndo': 'true', 'compress': '1',
                       'innerHeight': '857', 'innerWidth': '1920'})
            found = text in g2
        ok(f'{len(defn.get("chapters", []))} chapter(s); text box present: {"yes" if found else "NO"}')
    except Exception as e:  # noqa: BLE001
        fail(e)
    finally:
        if dashboard_id and not keep:
            step(8, 'delete spike dashboard')
            r = s.delete(f'{base}/api/objects/{dashboard_id}', params={'type': 55})
            ok() if r.ok else print(f'FAIL {r.status_code} {r.text[:200]}')
        elif dashboard_id:
            print(f'[8] kept dashboard {dashboard_id}')
        s.post(f'{base}/api/auth/logout')

    print('\nAll steps passed: Python + REST login can build and save a dashboard.')


if __name__ == '__main__':
    main()
