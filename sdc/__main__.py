"""Command line: python3 -m sdc <command>

  login [--method sso|standard|ldap]            choose how to sign in (asked up front), then sign in
  logout                                        end the cached session
  whoami                                        show who the cached session belongs to and the project check
  profile <dataset name or id> [-o file.json]   list the dataset's attributes and metrics (for writing a spec)
  check <spec.json>                             validate the spec against the dataset; builds nothing
  build <spec.json> [--no-verify]               build and save the dashboard, then check every item

Settings: .env in the repo root (see .env.example). Tokens and passwords are never printed.
"""
import argparse
import json
import sys
from pathlib import Path

from .build import Builder, BuildError, resolve_dataset
from .spec import SpecError, check_structure
from .transport import Connection, StrategyError, load_env


def _bare_connection():
    env = load_env()
    missing = [k for k in ('SDC_BASE_URL', 'SDC_PROJECT_ID') if not env.get(k)]
    if missing:
        raise SystemExit(f'Missing settings: {", ".join(missing)} (set them in .env; see .env.example)')
    return Connection(env['SDC_BASE_URL'], env['SDC_PROJECT_ID'])


def cmd_login(args):
    """Always asks which sign-in method to use (Enter keeps SDC_AUTH), unless --method is given."""
    from .login import interactive_login, normalize
    conn = _bare_connection()
    env = load_env()
    interactive_login(conn, env, method=normalize(args.method, env))


def cmd_logout(args):
    conn = _bare_connection()
    if conn.resume():
        conn.logout(force=True)
        print('Signed out; cached session removed.')
    else:
        print('No active session.')


def cmd_whoami(args):
    conn = _bare_connection()
    if not conn.resume():
        raise SystemExit('Not signed in, or the session expired: run  python3 -m sdc login')
    u = conn.user()
    print(f'Signed in as {u.get("fullName") or u.get("username")} ({conn.method})')
    try:
        conn.check_project()
        print(f'Project {conn.project_id}: OK')
    except StrategyError as e:
        print(str(e))


def cmd_profile(args):
    with Connection.from_env() as conn:
        ds = {'id': args.dataset} if len(args.dataset) == 32 and args.dataset.isalnum() else {'name': args.dataset}
        ds_id, ds_name = resolve_dataset(conn, ds)
        ao = conn.cube(ds_id)['definition']['availableObjects']
        prof = {'dataset': {'id': ds_id, 'name': ds_name},
                'attributes': [{'name': a['name'], 'id': a['id'],
                                'forms': [f.get('name') for f in a.get('forms', [])]} for a in ao.get('attributes', [])],
                'metrics': [{'name': m['name'], 'id': m['id']} for m in ao.get('metrics', [])]}
    out = json.dumps(prof, indent=1)
    if args.output:
        Path(args.output).write_text(out + '\n')
        print(f'{len(prof["attributes"])} attributes, {len(prof["metrics"])} metrics -> {args.output}')
    else:
        print(out)


def _load(path):
    """Load a spec. A spec's "project_id" overrides SDC_PROJECT_ID for this run."""
    import os
    spec = json.loads(Path(path).read_text())
    if spec.get('project_id'):
        os.environ['SDC_PROJECT_ID'] = spec['project_id']
    return spec


def cmd_check(args):
    spec = _load(args.spec)
    problems = check_structure(spec)
    if problems:
        _fail(problems)
    with Connection.from_env() as conn:
        b = Builder(conn, spec, log=lambda *_: None)
        try:
            b.prepare()
        except SpecError as e:
            _fail(e.problems)
    n = sum(len(p['items']) for p in spec['pages'])
    print(f'OK: {len(spec["pages"])} page(s), {n} item(s); every name resolves against {b.ds_name!r}')


def cmd_build(args):
    spec = _load(args.spec)
    problems = check_structure(spec)
    if problems:
        _fail(problems)
    with Connection.from_env() as conn:
        b = Builder(conn, spec)
        print(f'Building {spec["name"]!r}')
        try:
            r = b.run(verify=not args.no_verify)
        except SpecError as e:
            _fail(e.problems)
        except BuildError as e:
            print(f'\nFAILED at {e}\nNothing was saved (the draft was never saved, so there is nothing to delete).')
            sys.exit(1)
    bad = [x for x in r['report'] if not x[2]]
    print(f'\nSaved {r["name"]!r}  id {r["id"]}')
    print(f'{r["seconds"]}s, {r["edits"]} edit calls, {r["calls"]} requests')
    for name, secs in r['timings']:
        print(f'  {secs:6.1f}s  {name}')
    if r['report']:
        print('\nCheck of the saved dashboard:')
        for iid, key, ok, detail in r['report']:
            print(f'  [{"OK" if ok else "MISS"}] {iid} ({key}): {detail}')
        print(f'\n{len(r["report"]) - len(bad)} of {len(r["report"])} items OK')
    sys.exit(1 if bad else 0)


def _fail(problems):
    print('Spec problems:')
    for p in problems:
        print('  - ' + p)
    sys.exit(2)


def main():
    ap = argparse.ArgumentParser(prog='python3 -m sdc', description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('login', help='choose a sign-in method and sign in')
    p.add_argument('--method', choices=['sso', 'standard', 'ldap'], help='skip the question')
    p.set_defaults(fn=cmd_login)
    for name, fn in (('logout', cmd_logout), ('whoami', cmd_whoami)):
        sub.add_parser(name).set_defaults(fn=fn)
    p = sub.add_parser('profile')
    p.add_argument('dataset')
    p.add_argument('-o', '--output')
    p.set_defaults(fn=cmd_profile)
    p = sub.add_parser('check')
    p.add_argument('spec')
    p.set_defaults(fn=cmd_check)
    p = sub.add_parser('build')
    p.add_argument('spec')
    p.add_argument('--no-verify', action='store_true')
    p.set_defaults(fn=cmd_build)
    args = ap.parse_args()
    try:
        args.fn(args)
    except StrategyError as e:
        print(f'Error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
