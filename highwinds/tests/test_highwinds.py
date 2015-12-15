import json
import unittest
import responses
from highwinds import HighwindsClient, APIError


class TestHighwindsClient(unittest.TestCase):

    def setUp(self):
        self.client = HighwindsClient('http://127.0.0.1', 'testtoken')

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
        responses.add(responses.GET, 'http://127.0.0.1/api/v1/users/me', json=user)
        self.assertEqual(self.client.me(), user)

    @responses.activate
    def test_me(self):
        responses.add(responses.GET, 'http://127.0.0.1/api/v1/users/me', status=401)
        with self.assertRaises(APIError):
            self.client.me()