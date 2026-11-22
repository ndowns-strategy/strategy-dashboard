"""Connection to Strategy Library: sign-in, /api calls and the editor's taskProc servlet.

Sign-in: every command asks which method to use when it has no session yet (`python3 -m sdc login` always asks):

  sso       Sign in to Library in a browser as usual (SAML, OIDC, anything). The login prints a one-line snippet to run
            in that tab's developer console: it reads the tab's session token (GET /api/auth/token), asks for a
            short-lived identity token (POST /api/auth/identityToken) and shows it in a dialog to copy. Paste it at the
            prompt; Python exchanges it (POST /api/auth/delegate, loginMode -1) for its own REST session.
  standard  Strategy username and password (loginMode 1). Proven by spike/auth_spike.py.
  ldap      Directory username and password (loginMode 16).

The resulting session (token + cookies) is cached in ~/.config/sdc/, readable only by you, and reused until it expires.
`sdc logout` ends it. Either way the session's token and cookies (JSESSIONID etc.) are what /servlet/taskProc needs.

Settings come from the environment or a .env file in the repo root (gitignored):
  SDC_BASE_URL     e.g. https://studio.strategy.com/MicroStrategyLibrary
  SDC_PROJECT_ID
  SDC_AUTH         sso | standard | ldap: the default answer to the sign-in question
  SDC_USERNAME, SDC_PASSWORD   optional defaults for standard / ldap. With SDC_AUTH standard or ldap and both set, a
                   command that is not run in a terminal (a script, CI) signs in with them without asking.
"""
import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

from .constants import APP_ID

ENV_KEYS = ('SDC_BASE_URL', 'SDC_USERNAME', 'SDC_PASSWORD', 'SDC_LOGIN_MODE', 'SDC_PROJECT_ID', 'SDC_AUTH')
SESSION_DIR = Path(os.environ.get('SDC_SESSION_DIR') or Path.home() / '.config' / 'sdc')


class StrategyError(RuntimeError):
    """A failed call. For taskProc, code is the x-mstr-taskerrorcode header and actions the batch that was sent."""

    def __init__(self, message, status=None, code=None, actions=None):
        super().__init__(message)
        self.status, self.code, self.actions = status, code, actions


def load_env(path=None):
    env = {}
    p = Path(path) if path else Path(__file__).resolve().parent.parent / '.env'
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    for k in ENV_KEYS:
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


def identity_token_snippet(base_url):
    """The developer-console line `sdc login` asks you to run in a signed-in Library tab."""
    # Cookies alone are not enough for identityToken (401 "Access token not provided"), so it first reads the tab's own
    # session token from GET /api/auth/token (what the Embedding SDK does). Verified on studio.strategy.com 2026-11-22.
    path = urlparse(base_url).path.rstrip('/') or '/MicroStrategyLibrary'
    h = "{'X-Requested-With':'XMLHttpRequest'}"
    return ("(async()=>{const a=await fetch('" + path + "/api/auth/token',{credentials:'include',headers:" + h + "});"
            "const r=await fetch('" + path + "/api/auth/identityToken',{method:'POST',credentials:'include',"
            "headers:{'X-Requested-With':'XMLHttpRequest','X-MSTR-AuthToken':a.headers.get('X-MSTR-AuthToken')}});"
            "const t=r.headers.get('X-MSTR-IdentityToken');"
            "if(!t)throw new Error('HTTP '+a.status+'/'+r.status+' (are you signed in to Library in this tab?)');"
            # DevTools' copy() is gone after an await, and navigator.clipboard needs the page focused, so a prompt
            # dialog shows the token selected: press Cmd+C there.
            "window.prompt('Identity token: press Cmd+C to copy it, then paste it into the terminal',t)})()")


class Connection:
    """A signed-in Library session. Use as a context manager:

        with Connection.from_env() as conn:
            s = conn.new_dashboard([{'id': ds_id, 'name': ds_name}])

    A cached session stays open on exit for the next command; a non-interactive password sign-in logs out.
    """

    def __init__(self, base_url, project_id, timeout=120):
        self.base = base_url.rstrip('/')
        self.project_id = project_id
        self.timeout = timeout
        self.http = requests.Session()
        self.http.headers.update({'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest'})
        self.token = None
        self.persist = False   # True: keep the session open on exit (cached sessions)
        self.method = None     # sso | standard | ldap, once signed in
        self.calls = 0         # taskProc + /api calls made, for timing reports

    @classmethod
    def from_env(cls, env_path=None, interactive=None):
        """Connect with the cached session; if there is none, ask how to sign in (in a terminal), or sign in with
        SDC_USERNAME / SDC_PASSWORD when SDC_AUTH is standard or ldap and nobody is there to ask."""
        import sys
        from .login import LOGIN_MODE, interactive_login, normalize
        env = load_env(env_path)
        missing = [k for k in ('SDC_BASE_URL', 'SDC_PROJECT_ID') if not env.get(k)]
        if missing:
            raise SystemExit(f'Missing settings: {", ".join(missing)} (set them in .env; see .env.example)')
        c = cls(env['SDC_BASE_URL'], env['SDC_PROJECT_ID'])
        if not c.resume():
            method = normalize(env.get('SDC_AUTH'), env)
            if interactive is None:
                interactive = sys.stdin.isatty()
            if interactive:
                print('No Library session yet.')
                interactive_login(c, env)
            elif method in ('standard', 'ldap') and env.get('SDC_USERNAME') and env.get('SDC_PASSWORD'):
                c.login(env['SDC_USERNAME'], env['SDC_PASSWORD'], LOGIN_MODE[method])
            else:
                raise SystemExit('Not signed in, or the session expired: run  python3 -m sdc login')
        try:
            c.check_project()
        except Exception:
            c.logout()
            raise
        return c

    def projects(self):
        r = self.http.get(f'{self.base}/api/projects', timeout=self.timeout)
        return r.json() if r.ok else []

    def check_project(self):
        """Fail early when this login can't see SDC_PROJECT_ID (Library otherwise answers 404 on every object)."""
        ps = self.projects()
        if not any(p.get('id') == self.project_id for p in ps):
            names = ', '.join(f'{p.get("name")} ({p.get("id")})' for p in ps) or 'none'
            raise StrategyError(f'this login cannot see project {self.project_id}. Projects it can see: {names}')

    # ---- auth ----
    def _use_token(self, token):
        self.token = token
        self.http.headers.update({'X-MSTR-AuthToken': token, 'X-MSTR-ProjectID': self.project_id})

    def login(self, username, password, login_mode=1):
        r = self.http.post(f'{self.base}/api/auth/login', timeout=self.timeout, json={
            'username': username, 'password': password, 'loginMode': login_mode, 'applicationType': 35})
        if r.status_code != 204 or not r.headers.get('X-MSTR-AuthToken'):
            raise StrategyError(f'login failed: {r.status_code} {r.text[:300]}', status=r.status_code)
        self._use_token(r.headers['X-MSTR-AuthToken'])

    def delegate(self, identity_token):
        """Exchange an identity token from a signed-in browser session for this client's own REST session."""
        r = self.http.post(f'{self.base}/api/auth/delegate', timeout=self.timeout,
                           json={'loginMode': -1, 'identityToken': identity_token.strip()})
        if r.status_code not in (200, 204) or not r.headers.get('X-MSTR-AuthToken'):
            raise StrategyError(f'delegate failed: {r.status_code} {r.text[:300]}', status=r.status_code)
        self._use_token(r.headers['X-MSTR-AuthToken'])
        self.persist = True
        self.save_session()

    # Cached delegate session: one file per Library host, mode 0600, outside the repo.
    def _session_file(self):
        return SESSION_DIR / f'session-{urlparse(self.base).netloc}.json'

    def save_session(self):
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        os.chmod(SESSION_DIR, 0o700)
        f = self._session_file()
        data = {'base': self.base, 'method': self.method, 'token': self.token, 'saved': int(time.time()),
                'cookies': [{'name': c.name, 'value': c.value, 'domain': c.domain, 'path': c.path}
                            for c in self.http.cookies]}
        fd = os.open(f, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as fh:
            json.dump(data, fh)

    def resume(self):
        """Load the cached session and check it still works. Returns False if there is none or it expired."""
        f = self._session_file()
        if not f.exists():
            return False
        data = json.loads(f.read_text())
        for c in data.get('cookies', []):
            self.http.cookies.set(c['name'], c['value'], domain=c['domain'], path=c['path'])
        self._use_token(data['token'])
        self.method = data.get('method') or 'sso'
        self.persist = True
        r = self.http.get(f'{self.base}/api/sessions/userInfo', timeout=self.timeout)
        if r.status_code == 200:
            self.http.put(f'{self.base}/api/sessions', timeout=self.timeout)  # extend it
            return True
        if r.status_code in (401, 403):   # expired or ended: drop it. Anything else may be transient: keep it.
            self.forget()
            return False
        raise StrategyError(f'checking the cached session: {r.status_code} {r.text[:200]}', status=r.status_code)

    def forget(self):
        f = self._session_file()
        if f.exists():
            f.unlink()
        self.token = None

    def logout(self, force=False):
        """End the session. A cached session is kept unless force=True (`sdc logout`)."""
        if not self.token or (self.persist and not force):
            return
        try:
            self.http.post(f'{self.base}/api/auth/logout', timeout=self.timeout)
        finally:
            self.token = None
            if self.persist:
                self.forget()

    def user(self):
        return self.api('GET', '/sessions/userInfo')

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.logout()

    # ---- raw calls ----
    def api(self, method, path, body=None):
        self.calls += 1
        r = self.http.request(method, f'{self.base}/api{path}', json=body, timeout=self.timeout)
        if not r.ok:
            raise StrategyError(f'{method} {path} -> {r.status_code} {r.text[:400]}', status=r.status_code)
        return r.json() if r.text else None

    def task(self, params):
        self.calls += 1
        data = {'taskEnv': 'xhr', 'taskContentType': 'json', 'jsonMode': 'true',
                'xts': str(int(time.time() * 1000)), 'mstrWeb': 'random', **params}
        r = self.http.post(f'{self.base}/servlet/taskProc', data=data, timeout=self.timeout,
                           headers={'Content-type': 'application/x-www-form-urlencoded'})
        if not r.ok:
            raise StrategyError(f'taskProc {params.get("taskId")} -> {r.status_code} '
                                f'code={r.headers.get("x-mstr-taskerrorcode")}', status=r.status_code,
                                code=r.headers.get('x-mstr-taskerrorcode'))
        return r.text

    # ---- dashboards ----
    def my_folder(self, name='My Reports'):
        return next(f['id'] for f in self.api('GET', '/folders/myPersonalObjects') if f['name'] == name)

    def definition(self, dashboard_id):
        return self.api('GET', f'/v2/dossiers/{dashboard_id}/definition')

    def cube(self, dataset_id):
        return self.api('GET', f'/v2/cubes/{dataset_id}')

    def search(self, name, object_type=None):
        """Find objects by exact name (type 3 = report/cube, 55 = dashboard; None = any). Returns the result list."""
        q = f'/searches/results?name={requests.utils.quote(name)}&pattern=2&getAncestors=false&limit=50'
        r = self.api('GET', q + (f'&type={object_type}' if object_type else ''))
        return (r or {}).get('result', [])

    def new_dashboard(self, datasets=(), **session_opts):
        from .constants import BLANK_TEMPLATE
        from .session import Session
        r = self.api('POST', '/dossiers/draft/instances', {'filters': None, 'persistViewState': False,
                                                           'resolveOnly': False, 'applicationId': APP_ID,
                                                           'datasets': list(datasets)})
        return Session(self, BLANK_TEMPLATE, r['mid'], **session_opts)

    def open(self, dashboard_id, **session_opts):
        from .session import Session
        r = self.api('POST', f'/dossiers/{dashboard_id}/instances',
                     {'persistViewState': False, 'resolveOnly': False, 'applicationId': APP_ID})
        return Session(self, dashboard_id, r['mid'], **session_opts)

    def delete_dashboard(self, dashboard_id):
        self.calls += 1
        r = self.http.delete(f'{self.base}/api/objects/{dashboard_id}', params={'type': 55}, timeout=self.timeout)
        if not r.ok:
            raise StrategyError(f'delete {dashboard_id} -> {r.status_code} {r.text[:200]}', status=r.status_code)
