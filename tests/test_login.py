"""The sign-in question and each method's flow, with input and the server faked."""
import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

from sdc import login, transport
from sdc.transport import Connection


class FakeConn:
    base, project_id = 'https://lib.example/MicroStrategyLibrary', 'P'

    def __init__(self):
        self.done = []
        self.persist, self.method = False, None

    def delegate(self, tok):
        self.done.append(('delegate', tok))

    def login(self, user, pw, mode):
        self.done.append(('login', user, pw, mode))

    def save_session(self):
        self.done.append(('save', self.method))

    def user(self):
        return {'fullName': 'Test User'}

    def check_project(self):
        pass


def run(inputs, secret, fn):
    with mock.patch('builtins.input', side_effect=inputs), mock.patch('getpass.getpass', return_value=secret), \
            redirect_stdout(io.StringIO()) as out:
        return fn(), out.getvalue()


class AskMethod(unittest.TestCase):
    def test_number_choice(self):
        self.assertEqual(run(['2'], '', lambda: login.ask_method())[0], 'standard')

    def test_enter_takes_default(self):
        self.assertEqual(run([''], '', lambda: login.ask_method('ldap'))[0], 'ldap')

    def test_retries_bad_answer(self):
        self.assertEqual(run(['9', 'x', '1'], '', lambda: login.ask_method())[0], 'sso')

    def test_menu_lists_all_methods(self):
        _, out = run(['1'], '', lambda: login.ask_method())
        for word in ('SSO', 'Standard', 'LDAP'):
            self.assertIn(word, out)

    def test_aliases(self):
        self.assertEqual(login.normalize('delegate'), 'sso')
        self.assertEqual(login.normalize('password'), 'standard')
        self.assertEqual(login.normalize('password', {'SDC_LOGIN_MODE': '16'}), 'ldap')
        with self.assertRaises(SystemExit):
            login.normalize('kerberos')


class Flows(unittest.TestCase):
    def test_login_always_asks_first(self):
        c = FakeConn()
        run(['3', 'jdoe'], 'pw', lambda: login.interactive_login(c, {'SDC_AUTH': 'sso'}))
        self.assertEqual(c.done[0], ('login', 'jdoe', 'pw', 16))
        self.assertEqual(c.done[-1], ('save', 'ldap'))

    def test_sso(self):
        c = FakeConn()
        _, out = run(['1'], 'IDTOKEN', lambda: login.interactive_login(c, {}))
        self.assertEqual(c.done[0], ('delegate', 'IDTOKEN'))
        self.assertIn('/api/auth/identityToken', out)
        self.assertNotIn('IDTOKEN', out)

    def test_standard_uses_env_defaults(self):
        c = FakeConn()
        _, out = run(['2', ''], '', lambda: login.interactive_login(c, {'SDC_USERNAME': 'me', 'SDC_PASSWORD': 's3cret'}))
        self.assertEqual(c.done[0], ('login', 'me', 's3cret', 1))
        self.assertTrue(c.persist)
        self.assertNotIn('s3cret', out)

    def test_method_flag_skips_question(self):
        c = FakeConn()
        run(['u'], 'p', lambda: login.interactive_login(c, {}, method='standard'))
        self.assertEqual(c.done[0], ('login', 'u', 'p', 1))


class FromEnv(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = mock.patch.object(transport, 'SESSION_DIR', transport.Path(self.tmp.name))
        self.dir.start()
        self.env = {'SDC_BASE_URL': 'https://lib.example/MicroStrategyLibrary', 'SDC_PROJECT_ID': 'P'}

    def tearDown(self):
        self.dir.stop()
        self.tmp.cleanup()

    def _env(self, **extra):
        return mock.patch.object(transport, 'load_env', return_value={**self.env, **extra})

    def test_no_session_no_terminal_says_run_login(self):
        with self._env(), self.assertRaises(SystemExit) as e:
            Connection.from_env(interactive=False)
        self.assertIn('sdc login', str(e.exception))

    def test_no_session_in_terminal_asks(self):
        with self._env(), mock.patch('sdc.login.interactive_login') as il, \
                mock.patch.object(Connection, 'check_project'), redirect_stdout(io.StringIO()):
            Connection.from_env(interactive=True)
        il.assert_called_once()

    def test_script_with_configured_password(self):
        with self._env(SDC_AUTH='ldap', SDC_USERNAME='u', SDC_PASSWORD='p'), \
                mock.patch.object(Connection, 'login') as lg, mock.patch.object(Connection, 'check_project'):
            Connection.from_env(interactive=False)
        lg.assert_called_once_with('u', 'p', 16)

    def test_cached_session_needs_no_question(self):
        with self._env(), mock.patch.object(Connection, 'resume', return_value=True), \
                mock.patch('sdc.login.interactive_login') as il, mock.patch.object(Connection, 'check_project'):
            Connection.from_env(interactive=True)
        il.assert_not_called()


if __name__ == '__main__':
    unittest.main()
