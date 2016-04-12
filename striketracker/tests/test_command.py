from StringIO import StringIO
import os
from tempfile import mkstemp
import unittest
from mock import patch, mock_open, MagicMock, Mock
import sys
from requests import Response
from striketracker import Command, APIError


class TestStrikeTrackerCommand(unittest.TestCase):

    def setUp(self):
        self.fd, self.cache = mkstemp()
        self._stdout = sys.stdout
        sys.stdout = StringIO()
        self._stderr = sys.stderr
        sys.stderr = StringIO()
        self._stdin = sys.stdin
        sys.stdin = StringIO()

    def tearDown(self):
        os.close(self.fd)
        os.unlink(self.cache)
        sys.stdout = self._stdout
        sys.stderr = self._stderr
        sys.stdin = self._stdin

    def test_print_help(self):
        sys.argv = ['striketracker']
        command = Command()
        self.assertIn(
            'usage: striketracker [-h] [--token TOKEN] [-v] action\n\nCommand line interface to the Highwinds CDN',
            sys.stdout.getvalue())

    def test_print_unknown_command(self):
        sys.argv = ['striketracker', 'nuke']
        command = Command()
        self.assertIn(
            'Unknown command: nuke\n',
            sys.stderr.getvalue())

    @patch('getpass.getpass')
    @patch('__builtin__.raw_input')
    @patch('striketracker.APIClient.create_token')
    def test_init(self, create_token, raw_input, getpw):
        sys.argv = ['striketracker', 'init']
        create_token.return_value = 'rikkitikkitavi'
        raw_input.return_value = 'bob'
        getpw.return_value = 'password1'
        command = Command(cache=self.cache)
        self.assertTrue(create_token.called)
        create_token.assert_called_with(username='bob', password='password1', application=None)
        self.assertEqual(command.cache.get('token'), 'rikkitikkitavi')
        self.assertEqual('Initializing configuration...\nSuccessfully saved token\n',
                         sys.stdout.getvalue())

    @patch('striketracker.APIClient.create_token')
    def test_init_token_supplied(self, create_token):
        sys.argv = ['striketracker', 'init', '--token', 'foobar']
        command = Command(cache=self.cache)
        self.assertFalse(create_token.called)
        self.assertEqual(command.cache.get('token'), 'foobar')
        self.assertEqual('Initializing configuration...\nSuccessfully saved token\n',
                         sys.stdout.getvalue())

    @patch('striketracker.APIClient.version')
    def test_version(self, version):
        sys.argv = ['striketracker', 'version']
        version.return_value = '3.0.4-1600'
        Command()
        self.assertTrue(version.called)
        self.assertEqual('3.0.4-1600\n', sys.stdout.getvalue())

    @patch('striketracker.APIClient.version')
    @patch('logging.getLogger')
    def test_version_verbose(self, getLogger, version):
        sys.argv = ['striketracker', 'version', '--verbose']
        version.return_value = '3.0.4-1600'
        Command()
        getLogger.assert_called_with('requests.packages.urllib3')
        self.assertTrue(version.called)
        self.assertEqual('3.0.4-1600\n', sys.stdout.getvalue())

    @patch('striketracker.APIClient.me')
    @patch('striketracker.ConfigurationCache.get')
    def test_me(self, get, me):
        sys.argv = ['striketracker', 'me']
        get.return_value = 'cachedtoken'
        me.return_value = {
            'firstName': 'Bob',
            'lastName': 'Saget'
        }
        command = Command()
        self.assertTrue(me.called)
        self.assertEqual('cachedtoken', command.client.token)
        self.assertEqual("""firstName: Bob
lastName: Saget
""", sys.stdout.getvalue())

    @patch('striketracker.APIClient.me')
    @patch('striketracker.ConfigurationCache.get')
    def test_me_token(self, get, me):
        sys.argv = ['striketracker', 'me', '--token', 'foobarwinniethefoobar']
        get.return_value = 'cachedtoken'
        me.return_value = {
            'firstName': 'Bob',
            'lastName': 'Saget'
        }
        command = Command()
        self.assertTrue(me.called)
        self.assertEqual('foobarwinniethefoobar', command.client.token)
        self.assertEqual("""firstName: Bob
lastName: Saget
""", sys.stdout.getvalue())

    @patch('striketracker.APIClient.get_host')
    @patch('striketracker.ConfigurationCache.get')
    def test_get_host(self, get, get_host):
        sys.argv = ['striketracker', 'get_host', 'y1y2y3y4', 'x1x2x3x4']
        get.return_value = 'cachedtoken'
        get_host.return_value = {
            "name": "test host",
            "hashCode": "x1x2x3x4",
            "type": "HOST",
            "createdDate": "2016-04-12 11:22:03",
            "updatedDate": "2016-04-12 11:22:18",
            "services": [],
            "scopes": [
                {
                    "id": 2746294,
                    "platform": "CDS",
                    "path": "/",
                    "createdDate": "2016-04-12 11:22:03",
                    "updatedDate": "2016-04-12 11:22:03"
                },
                {
                    "id": 2746295,
                    "platform": "ALL",
                    "path": "/",
                    "createdDate": "2016-04-12 11:22:03",
                    "updatedDate": "2016-04-12 11:22:03"
                }
            ]
        }
        command = Command()
        self.assertTrue(get_host.called)
        self.assertEqual('cachedtoken', command.client.token)
        self.assertEqual("""createdDate: '2016-04-12 11:22:03'
hashCode: x1x2x3x4
name: test host
scopes:
- createdDate: '2016-04-12 11:22:03'
  id: 2746294
  path: /
  platform: CDS
  updatedDate: '2016-04-12 11:22:03'
- createdDate: '2016-04-12 11:22:03'
  id: 2746295
  path: /
  platform: ALL
  updatedDate: '2016-04-12 11:22:03'
services: []
type: HOST
updatedDate: '2016-04-12 11:22:18'
""", sys.stdout.getvalue())

    @patch('striketracker.APIClient.get_host')
    @patch('striketracker.ConfigurationCache.get')
    def test_get_host_fails(self, get, get_host):
        sys.argv = ['striketracker', 'get_host', 'y1y2y3y4', 'x1x2x3x4']
        get.return_value = 'cachedtoken'
        response = Mock()
        response.json = Mock(return_value={
            "error": "This endpoint requires authentication"
        })
        get_host.side_effect = APIError('Could not fetch host', response)
        with self.assertRaises(SystemExit) as e:
            command = Command()
        self.assertTrue(get_host.called)
        self.assertEqual("""Could not fetch host
This endpoint requires authentication
""", sys.stderr.getvalue())

    @patch('striketracker.APIClient.get_host')
    @patch('striketracker.ConfigurationCache.get')
    def test_get_host_token(self, get, get_host):
        sys.argv = ['striketracker', 'get_host', 'y1y2y3y4', 'x1x2x3x4', '--token', 'foobarwinniethefoobar']
        get.return_value = 'cachedtoken'
        get_host.return_value = {
            "name": "test host",
            "hashCode": "x1x2x3x4",
            "type": "HOST",
            "createdDate": "2016-04-12 11:22:03",
            "updatedDate": "2016-04-12 11:22:18",
            "services": [],
            "scopes": [
                {
                    "id": 2746294,
                    "platform": "CDS",
                    "path": "/",
                    "createdDate": "2016-04-12 11:22:03",
                    "updatedDate": "2016-04-12 11:22:03"
                },
                {
                    "id": 2746295,
                    "platform": "ALL",
                    "path": "/",
                    "createdDate": "2016-04-12 11:22:03",
                    "updatedDate": "2016-04-12 11:22:03"
                }
            ]
        }
        command = Command()
        self.assertTrue(get_host.called)
        self.assertEqual('foobarwinniethefoobar', command.client.token)
        self.assertEqual("""createdDate: '2016-04-12 11:22:03'
hashCode: x1x2x3x4
name: test host
scopes:
- createdDate: '2016-04-12 11:22:03'
  id: 2746294
  path: /
  platform: CDS
  updatedDate: '2016-04-12 11:22:03'
- createdDate: '2016-04-12 11:22:03'
  id: 2746295
  path: /
  platform: ALL
  updatedDate: '2016-04-12 11:22:03'
services: []
type: HOST
updatedDate: '2016-04-12 11:22:18'
""", sys.stdout.getvalue())

    def test_purge_no_hash(self):
        sys.argv = ['striketracker', 'purge', '--token', 'foobarwinniethefoobar']
        with self.assertRaises(SystemExit) as e:
            command = Command()
        self.assertIn('too few arguments', sys.stderr.getvalue())

    def test_purge_no_token(self):
        sys.argv = ['striketracker', 'purge', 'x1x2x3x4']
        with self.assertRaises(SystemExit) as e:
            command = Command(cache=self.cache)
        self.assertIn('This command requires authentication', sys.stderr.getvalue())

    @patch('striketracker.APIClient.purge')
    def test_purge(self, purge):
        sys.argv = ['striketracker', 'purge', 'x1x2x3x4', '--token', 'foobarwinniethefoobar']
        sys.stdin.write('//cdn.foo.com/main.js\n//cdn.foo.com/main.css')
        sys.stdin.seek(0)
        command = Command()
        purge.assert_called_with('x1x2x3x4', [
            {
                "url": "//cdn.foo.com/main.js",
                "purgeAllDynamic": False,
                "recursive": False,
                "invalidateOnly": False
            },
            {
                "url": "//cdn.foo.com/main.css",
                "purgeAllDynamic": False,
                "recursive": False,
                "invalidateOnly": False
            }
        ])

    @patch('striketracker.APIClient.purge_status')
    @patch('striketracker.APIClient.purge')
    def test_purge_poll(self, purge, purge_status):
        sys.argv = ['striketracker', 'purge', 'x1x2x3x4', '--token', 'foobarwinniethefoobar', '--poll']
        sys.stdin.write('//cdn.foo.com/main.js\n//cdn.foo.com/main.css')
        sys.stdin.seek(0)
        purge.return_value = 'cmu34ctmy3408xmy'
        purge_status.side_effect = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        command = Command()
        purge_status.assert_called_with('x1x2x3x4', 'cmu34ctmy3408xmy')
        self.assertEqual('Reading urls from stdin\nSending purge.........Done!\n', sys.stderr.getvalue())

    @patch('striketracker.APIClient.purge')
    def test_purge_fails(self, purge):
        sys.argv = ['striketracker', 'purge', 'x1x2x3x4', '--token', 'foobarwinniethefoobar']
        sys.stdin.write('//cdn.foo.com/main.js\n//cdn.foo.com/main.css')
        sys.stdin.seek(0)
        purge.side_effect = APIError('Could not send purge to the CDN', None)
        with self.assertRaises(SystemExit):
            command = Command()

    @patch('striketracker.APIClient.purge')
    def test_purge_options(self, purge):
        sys.stdin.write('//cdn.foo.com/main.js\n//cdn.foo.com/main.css')
        os.write(self.fd, 'token: foobar')
        for option in ['--purge-all-dynamic', '--recursive', '--invalidate-only']:
            sys.argv = ['striketracker', 'purge', 'x1x2x3x4', option]
            sys.stdin.seek(0)
            command = Command(cache=self.cache)
            purge.assert_called_with('x1x2x3x4', [
                {
                    "url": "//cdn.foo.com/main.js",
                    "purgeAllDynamic": option == '--purge-all-dynamic',
                    "recursive": option == '--recursive',
                    "invalidateOnly": option == '--invalidate-only'
                },
                {
                    "url": "//cdn.foo.com/main.css",
                    "purgeAllDynamic": option == '--purge-all-dynamic',
                    "recursive": option == '--recursive',
                    "invalidateOnly": option == '--invalidate-only'
                }
            ])

    @patch('striketracker.APIClient.purge_status')
    def test_purge_status(self, purge_status):
        sys.argv = ['striketracker', 'purge_status', 'x1x2x3x4', 'cmu34ctmy3408xmy']
        os.write(self.fd, 'token: foobar')
        purge_status.return_value = 0.75
        command = Command(cache=self.cache)
        purge_status.assert_called_with('x1x2x3x4', 'cmu34ctmy3408xmy')
        self.assertEqual('0.75\n', sys.stdout.getvalue())

    @patch('striketracker.APIClient.update_configuration')
    @patch('striketracker.APIClient.get_configuration')
    @patch('striketracker.APIClient.create_scope')
    @patch('striketracker.APIClient.create_host')
    @patch('striketracker.APIClient.get_host')
    @patch('striketracker.ConfigurationCache.get')
    def test_clone_host(self, get, get_host, create_host, create_scope, get_configuration, update_configuration):
        sys.argv = ['striketracker', 'clone_host', 'y1y2y3y4', 'x1x2x3x4']
        get.return_value = 'cachedtoken'
        get_host.return_value = {
            "name": "test host",
            "hashCode": "x1x2x3x4",
            "type": "HOST",
            "createdDate": "2016-04-12 11:22:03",
            "updatedDate": "2016-04-12 11:22:18",
            "services": [],
            "scopes": [
                {
                    "id": 2746294,
                    "platform": "CDS",
                    "path": "/",
                    "createdDate": "2016-04-12 11:22:03",
                    "updatedDate": "2016-04-12 11:22:03"
                },
                {
                    "id": 2746295,
                    "platform": "ALL",
                    "path": "/",
                    "createdDate": "2016-04-12 11:22:03",
                    "updatedDate": "2016-04-12 11:22:03"
                }
            ]
        }
        create_host.return_value = {
            "name": "test host (copy)",
            "hashCode": "c1c2c3c4",
            "type": "HOST",
            "createdDate": "2016-04-12 11:22:03",
            "updatedDate": "2016-04-12 11:22:18",
            "services": [],
            "scopes": [
                {
                    "id": 2746296,
                    "platform": "CDS",
                    "path": "/",
                    "createdDate": "2016-04-12 11:22:03",
                    "updatedDate": "2016-04-12 11:22:03"
                },
                {
                    "id": 2746297,
                    "platform": "ALL",
                    "path": "/",
                    "createdDate": "2016-04-12 11:22:03",
                    "updatedDate": "2016-04-12 11:22:03"
                }
            ]
        }
        create_scope.side_effect = [{
            "id": 2746296,
            "platform": "CDS",
            "path": "/",
            "createdDate": "2016-04-12 11:22:03",
            "updatedDate": "2016-04-12 11:22:03"
        },{
            "id": 2746297,
            "platform": "ALL",
            "path": "/",
            "createdDate": "2016-04-12 11:22:03",
            "updatedDate": "2016-04-12 11:22:03"
        }]
        get_configuration.side_effect = [{
            "scope": {
                "id": 2746296,
                "platform": "CDS",
                "path": "/",
                "createdDate": "2016-04-12 11:22:03",
                "updatedDate": "2016-04-12 11:22:03"
            },
            "originPullHost": {
                "id": 92846,
                "primary": 1234
            },
            "cacheControl": [
                {"id": 2846, "statusCodeMatch": "200", "maxAge": 600},
                {"id": 26461947, "statusCodeMatch": "4*,5*", "maxAge": 1}
            ],
            "hostname": [
                {"domain": "www.foo.com"}
            ]
        }, {
            "scope": {
                "id": 2746297,
                "platform": "ALL",
                "path": "/",
                "createdDate": "2016-04-12 11:22:03",
                "updatedDate": "2016-04-12 11:22:03"
            }
        }]
        update_configuration.side_effect = [{
            "scope": {
                "id": 2746296,
                "platform": "CDS",
                "path": "/",
                "createdDate": "2016-04-12 11:22:03",
                "updatedDate": "2016-04-12 11:22:03"
            },
            "originPullHost": {
                "id": 12345,
                "primary": 1234
            }
        }, {
            "scope": {
                "id": 2746297,
                "platform": "ALL",
                "path": "/",
                "createdDate": "2016-04-12 11:22:03",
                "updatedDate": "2016-04-12 11:22:03"
            }
        }]

        command = Command()
        self.assertTrue(get_host.called)
        self.assertTrue(create_host.called)

    @patch('striketracker.APIClient.update_configuration')
    @patch('striketracker.APIClient.get_configuration')
    @patch('striketracker.APIClient.create_scope')
    @patch('striketracker.APIClient.create_host')
    @patch('striketracker.APIClient.get_host')
    @patch('striketracker.ConfigurationCache.get')
    def test_clone_host_get_fails(self, get, get_host, create_host, create_scope, get_configuration, update_configuration):
        sys.argv = ['striketracker', 'clone_host', 'y1y2y3y4', 'x1x2x3x4']
        get.return_value = 'cachedtoken'
        get_host.side_effect = APIError('Could not fetch host', {})

        with self.assertRaises(SystemExit) as e:
            command = Command()

    @patch('striketracker.APIClient.update_configuration')
    @patch('striketracker.APIClient.get_configuration')
    @patch('striketracker.APIClient.create_scope')
    @patch('striketracker.APIClient.create_host')
    @patch('striketracker.APIClient.get_host')
    @patch('striketracker.ConfigurationCache.get')
    def test_clone_host_get_configuration_fails(self, get, get_host, create_host, create_scope, get_configuration, update_configuration):
        sys.argv = ['striketracker', 'clone_host', 'y1y2y3y4', 'x1x2x3x4']
        get.return_value = 'cachedtoken'
        get_host.return_value = {
            "name": "test host",
            "hashCode": "x1x2x3x4",
            "type": "HOST",
            "createdDate": "2016-04-12 11:22:03",
            "updatedDate": "2016-04-12 11:22:18",
            "services": [],
            "scopes": [
                {
                    "id": 2746294,
                    "platform": "CDS",
                    "path": "/",
                    "createdDate": "2016-04-12 11:22:03",
                    "updatedDate": "2016-04-12 11:22:03"
                },
                {
                    "id": 2746295,
                    "platform": "ALL",
                    "path": "/",
                    "createdDate": "2016-04-12 11:22:03",
                    "updatedDate": "2016-04-12 11:22:03"
                }
            ]
        }
        create_host.return_value = {
            "name": "test host (copy)",
            "hashCode": "c1c2c3c4",
            "type": "HOST",
            "createdDate": "2016-04-12 11:22:03",
            "updatedDate": "2016-04-12 11:22:18",
            "services": [],
            "scopes": [
                {
                    "id": 2746296,
                    "platform": "CDS",
                    "path": "/",
                    "createdDate": "2016-04-12 11:22:03",
                    "updatedDate": "2016-04-12 11:22:03"
                },
                {
                    "id": 2746297,
                    "platform": "ALL",
                    "path": "/",
                    "createdDate": "2016-04-12 11:22:03",
                    "updatedDate": "2016-04-12 11:22:03"
                }
            ]
        }
        get_configuration.side_effect = APIError('Could not fetch host', {})

        with self.assertRaises(SystemExit) as e:
            command = Command()