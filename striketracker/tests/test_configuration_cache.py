import os
from tempfile import mkstemp
import unittest
from striketracker import ConfigurationCache


class TestStrikeTrackerAPIClient(unittest.TestCase):
    def setUp(self):
        self.fd, self.filename = mkstemp()
        self.cache = ConfigurationCache(filename=self.filename)

    def tearDown(self):
        os.close(self.fd)
        os.unlink(self.filename)

    def test_lazy_get(self):
        token = self.cache.get('token')
        self.assertIsNone(token)
        with open(self.filename, 'w') as f:
            f.write('token: foo')
        self.assertIsNone(self.cache.get('token'))
        self.assertEqual('bar', self.cache.get('token', 'bar'))
        self.cache.cache = None
        token = self.cache.get('token')
        self.assertEqual('foo', self.cache.get('token'))

    def test_set(self):
        self.cache.set('token', 'bar')
        with open(self.filename, 'r') as f:
            self.assertEqual('token: bar\n', f.read())