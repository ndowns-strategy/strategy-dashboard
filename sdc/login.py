"""Interactive sign-in: asks which sign-in method to use, then signs in and caches the session.

Used by `python3 -m sdc login`, and by any other command that finds no usable session while running in a terminal.
Secrets are read with getpass (hidden) and never printed or stored; only the resulting session (token + cookies) is
cached, in ~/.config/sdc/, readable only by you.
"""
import getpass

from .transport import StrategyError, identity_token_snippet

METHODS = [
    ('sso', 'SSO: sign in through your browser (SAML, OIDC or any other Library sign-in page)'),
    ('standard', 'Standard: a Strategy username and password'),
    ('ldap', 'LDAP: your directory username and password'),
]
ALIASES = {'delegate': 'sso', 'password': 'standard', 'sso': 'sso', 'standard': 'standard', 'ldap': 'ldap'}
LOGIN_MODE = {'standard': 1, 'ldap': 16}


def normalize(method, env=None):
    """SDC_AUTH / --method value -> 'sso' | 'standard' | 'ldap' | None. Old values: delegate = sso; password = standard,
    or ldap when SDC_LOGIN_MODE is 16."""
    if not method:
        return None
    m = ALIASES.get(method.strip().lower())
    if m is None:
        raise SystemExit(f'Unknown sign-in method {method!r}: use sso, standard or ldap')
    if method.strip().lower() == 'password' and str((env or {}).get('SDC_LOGIN_MODE')) == '16':
        m = 'ldap'
    return m


def ask_method(default=None):
    print(f'How do you sign in to Strategy Library?')
    for i, (key, label) in enumerate(METHODS, 1):
        print(f'  {i}. {label}' + ('   (default)' if key == default else ''))
    keys = [k for k, _ in METHODS]
    while True:
        ans = input(f'Choose 1-{len(METHODS)}' + (f' [Enter = {default}]' if default else '') + ': ').strip().lower()
        if not ans and default:
            return default
        if ans.isdigit() and 1 <= int(ans) <= len(METHODS):
            return keys[int(ans) - 1]
        if ans in ALIASES:
            return ALIASES[ans]
        print('  Please type a number from the list.')


def sign_in(conn, method, env):
    """Sign conn in with the chosen method and cache the session. Returns the user info."""
    if method == 'sso':
        print(f'\n1. In your browser, sign in to {conn.base}/app as usual.')
        print('2. In that tab, open the developer console (Cmd+Option+J in Chrome; type "allow pasting" first if Chrome'
              ' asks) and run this line:\n')
        print('   ' + identity_token_snippet(conn.base) + '\n')
        print('3. A dialog shows a short-lived identity token, already selected: press Cmd+C, then paste it here'
              ' (input is hidden).')
        tok = getpass.getpass('Identity token: ')
        if not tok.strip():
            raise SystemExit('No token entered.')
        conn.delegate(tok)
    else:
        user_default = env.get('SDC_USERNAME') or ''
        user = input('Username' + (f' [Enter = {user_default}]' if user_default else '') + ': ').strip() or user_default
        if not user:
            raise SystemExit('No username entered.')
        hint = ' (Enter = SDC_PASSWORD from .env)' if env.get('SDC_PASSWORD') else ''
        pw = getpass.getpass(f'Password{hint}: ') or env.get('SDC_PASSWORD') or ''
        if not pw:
            raise SystemExit('No password entered.')
        conn.login(user, pw, LOGIN_MODE[method])
        conn.persist = True
    conn.method = method
    conn.save_session()
    return conn.user()


def interactive_login(conn, env, method=None, ask=True):
    """Ask for the method (defaulting to SDC_AUTH) unless one is given, then sign in."""
    default = normalize(env.get('SDC_AUTH'), env)
    if method is None:
        method = ask_method(default) if ask or not default else default
    u = sign_in(conn, method, env)
    print(f'\nSigned in as {u.get("fullName") or u.get("username")} ({method}). Session cached for later commands.')
    try:
        conn.check_project()
        print(f'Project {conn.project_id}: OK')
    except StrategyError as e:
        print(f'Warning: {e}')
    return u
