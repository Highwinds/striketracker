import unittest
import responses
from striketracker import APIClient, APIError


class TestStrikeTrackerAPIClient(unittest.TestCase):

    def setUp(self):
        self.client = APIClient('http://127.0.0.1', 'testtoken')

    @responses.activate
    def test_version(self):
        responses.add(responses.GET, 'http://127.0.0.1/version', adding_headers={'X-CDNWS-VERSION': '3.0.4-1600'})
        self.assertEqual(self.client.version(), '3.0.4-1600')

    @responses.activate
    def test_me(self):
        user = {
            "id": 8675309,
            "username": "support@highwinds.com",
            "status": "ACTIVATED",
            "roles": {
                "userAccount": {
                    "report": "EDIT",
                    "account": "EDIT",
                    "content": "EDIT",
                    "configuration": "EDIT"
                },
                "subaccounts": {
                    "report": "EDIT",
                    "account": "EDIT",
                    "content": "EDIT",
                    "configuration": "EDIT"
                }
            },
            "preferences": {},
            "createdDate": None,
            "updatedDate": "2015-01-01 12:18:20",
            "lastLogin": "2015-01-05 19:00:40",
            "authorizedSupportContact": True,
            "firstName": "Highwinds",
            "lastName": "Support",
            "email": "support@highwinds.com",
            "phone": "1",
            "fax": "1",
            "userType": "Normal",
            "accountHash": "x1x2x3x4",
            "accountName": "Highwinds"
        }
        responses.add(responses.GET, 'http://127.0.0.1/api/v1/users/me', json=user, status=200)
        self.assertEqual(self.client.me(), user)


    @responses.activate
    def test_me_fails(self):
        responses.add(responses.GET, 'http://127.0.0.1/api/v1/users/me', status=401)
        with self.assertRaises(APIError):
            self.client.me()


    @responses.activate
    def test_create_token(self):
        responses.add(responses.POST, 'http://127.0.0.1/auth/token', status=201, json={
            "access_token": 'flargyblarg'
        })
        responses.add(responses.GET, 'http://127.0.0.1/api/v1/users/me', status=200, json={
            "id": 12345,
            "accountHash": "x1x2x3x4"
        })
        responses.add(responses.POST, 'http://127.0.0.1/api/v1/accounts/x1x2x3x4/users/12345/tokens',
                      status=200, json={
                "token": 'foo'
            })
        token = self.client.create_token('bob', 'password1')
        self.assertEqual('foo', token)

    @responses.activate
    def test_create_token_fails_login(self):
        responses.add(responses.POST, 'http://127.0.0.1/auth/token', status=401, json={
            "error": 'This endpoint requires authentication'
        })
        with self.assertRaises(APIError) as e:
            self.client.create_token('bob', 'password1')
        self.assertEqual('Could not fetch access token', e.exception.message)

    @responses.activate
    def test_create_token_fails_me(self):
        responses.add(responses.POST, 'http://127.0.0.1/auth/token', status=201, json={
            "access_token": 'flargyblarg'
        })
        responses.add(responses.GET, 'http://127.0.0.1/api/v1/users/me', status=404, json={
            'error': 'User not found'
        })
        with self.assertRaises(APIError) as e:
            self.client.create_token('bob', 'password1')
        self.assertEqual('Could not fetch user\'s root account hash', e.exception.message)

    @responses.activate
    def test_create_token_fails_token(self):
        responses.add(responses.POST, 'http://127.0.0.1/auth/token', status=201, json={
            "access_token": 'flargyblarg'
        })
        responses.add(responses.GET, 'http://127.0.0.1/api/v1/users/me', status=200, json={
            "id": 12345,
            "accountHash": "x1x2x3x4"
        })
        responses.add(responses.POST, 'http://127.0.0.1/api/v1/accounts/x1x2x3x4/users/12345/tokens',
                      status=500, json={"error": "Could not write token to database"})
        with self.assertRaises(APIError) as e:
            self.client.create_token('bob', 'password1')
        self.assertEqual('Could not generate API token', e.exception.message)

    @responses.activate
    def test_purge(self):
        responses.add(responses.POST, 'http://127.0.0.1/api/v1/accounts/x1x2x3x4/purge', status=200,
                      json={
                          'id': 'mwx9034mtc049myx2'
                      })
        id = self.client.purge('x1x2x3x4', [{"url": '//cdn.foo.com/main.js'}])
        self.assertEqual('mwx9034mtc049myx2', id)

    @responses.activate
    def test_purge_fails(self):
        responses.add(responses.POST, 'http://127.0.0.1/api/v1/accounts/x1x2x3x4/purge', status=500,
                      json={
                          'error': 'Could not send purge to the CDN'
                      })
        with self.assertRaises(APIError):
            self.client.purge('x1x2x3x4', [{"url": '//cdn.foo.com/main.js'}])

    @responses.activate
    def test_purge_status(self):
        responses.add(responses.GET, 'http://127.0.0.1/api/v1/accounts/x1x2x3x4/purge/mwx9034mtc049myx2',
                      status=200, json={
                'progress': 1
            })
        status = self.client.purge_status('x1x2x3x4', 'mwx9034mtc049myx2')
        self.assertEqual(1.0, status)

    @responses.activate
    def test_purge_status_fails(self):
        responses.add(responses.GET, 'http://127.0.0.1/api/v1/accounts/x1x2x3x4/purge/mwx9034mtc049myx2',
                      status=500, json={
                'error': 'Could not fetch purge status from the CDN'
            })
        with self.assertRaises(APIError):
            self.client.purge_status('x1x2x3x4', 'mwx9034mtc049myx2')
