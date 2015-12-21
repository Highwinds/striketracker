from StringIO import StringIO
import os
from tempfile import mkstemp
import unittest
from mock import patch, mock_open
import sys
from striketracker import Command
import getpass


class TestStrikeTrackerCommand(unittest.TestCase):

    def setUp(self):
        self.fd, self.cache = mkstemp()

    def tearDown(self):
        os.close(self.fd)
        os.unlink(self.cache)

    @patch('getpass.getpass')
    @patch('__builtin__.raw_input')
    @patch('striketracker.APIClient.create_token')
    def test_init(self, create_token, raw_input, getpw):
        sys.argv = ['striketracker', 'init']
        stdout = StringIO()
        create_token.return_value = 'rikkitikkitavi'
        raw_input.return_value = 'bob'
        getpw.return_value = 'password1'
        command = Command(stdout=stdout, cache=self.cache)
        self.assertTrue(create_token.called)
        create_token.assert_called_with(username='bob', password='password1', application=None)
        self.assertEqual(command.cache.get('token'), 'rikkitikkitavi')
        self.assertEqual('Initializing configuration...\nSuccessfully saved token\n',
                         stdout.getvalue())

    def test_init_token_supplied(self):
        sys.argv = ['striketracker', 'init', '--token', 'foobar']
        stdout = StringIO()
        create_token = mock_open()
        with patch('striketracker.APIClient.create_token', create_token):
            command = Command(stdout=stdout, cache=self.cache)
        self.assertFalse(create_token.called)
        self.assertEqual(command.cache.get('token'), 'foobar')
        self.assertEqual('Initializing configuration...\nSuccessfully saved token\n',
                         stdout.getvalue())

    def test_version(self):
        sys.argv = ['striketracker', 'version']
        stdout = StringIO()
        version = mock_open()
        with patch('striketracker.APIClient.version', version):
            version.return_value = '3.0.4-1600'
            Command(stdout=stdout)
        self.assertTrue(version.called)
        self.assertEqual('3.0.4-1600\n', stdout.getvalue())

    @patch('logging.getLogger')
    def test_version_verbose(self, getLogger):
        sys.argv = ['striketracker', 'version', '--verbose']
        stdout = StringIO()
        version = mock_open()
        with patch('striketracker.APIClient.version', version):
            version.return_value = '3.0.4-1600'
            Command(stdout=stdout)
        getLogger.assert_called_with('requests.packages.urllib3')
        self.assertTrue(version.called)
        self.assertEqual('3.0.4-1600\n', stdout.getvalue())

    def test_me(self):
        sys.argv = ['striketracker', 'me']
        stdout = StringIO()
        me = mock_open()
        with patch('striketracker.APIClient.me', me):
            get = mock_open()
            with patch('striketracker.ConfigurationCache.get', get):
                get.return_value = 'cachedtoken'
                me.return_value = {
                    'firstName': 'Bob',
                    'lastName': 'Saget'
                }
                command = Command(stdout=stdout)
        self.assertTrue(me.called)
        self.assertEqual('cachedtoken', command.client.token)
        self.assertEqual("""firstName: Bob
lastName: Saget
""", stdout.getvalue())

    def test_me_token(self):
        sys.argv = ['striketracker', 'me', '--token', 'foobarwinniethefoobar']
        stdout = StringIO()
        me = mock_open()
        with patch('striketracker.APIClient.me', me):
            get = mock_open()
            with patch('striketracker.ConfigurationCache.get', get):
                get.return_value = 'cachedtoken'
                me.return_value = {
                    'firstName': 'Bob',
                    'lastName': 'Saget'
                }
                command = Command(stdout=stdout)
        self.assertTrue(me.called)
        self.assertEqual('foobarwinniethefoobar', command.client.token)
        self.assertEqual("""firstName: Bob
lastName: Saget
""", stdout.getvalue())
