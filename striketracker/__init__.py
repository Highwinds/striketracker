import argparse
import getpass
import os
from os.path import expanduser
import requests
import sys
import time
import yaml
from yaml import SafeDumper
import logging



class ConfigurationCache():
    def __init__(self, filename=None):
        self.cache = None
        self.filename = filename if filename is not None else os.path.join(expanduser('~'), '.highwinds')

    def read(self):
        with os.fdopen(os.open(self.filename, os.O_RDONLY | os.O_CREAT, 0600), 'r') as f:
            self.cache = yaml.load(f)
            if self.cache is None:
                self.cache = {}
        return self.cache

    def set(self, key, value):
        if self.cache is None:
            self.read()
        self.cache[key] = value
        with os.fdopen(os.open(self.filename, os.O_WRONLY | os.O_CREAT, 0600), 'w') as f:
            return yaml.dump(self.cache, f, Dumper=SafeDumper, default_flow_style=False)

    def get(self, key, default=None):
        if self.cache is None:
            self.read()
        return self.cache.get(key, default)



class APIError(Exception):
    def __init__(self, message, context):
        super(APIError, self).__init__(message)
        self.context = context


class APIClient:
    def __init__(self, base_url='https://striketracker.highwinds.com', token=None):
        self.base_url = base_url
        self.token = token

    def version(self):
        response = requests.get(self.base_url + '/version')
        return response.headers['X-Cdnws-Version']

    def me(self):
        user_response = requests.get(
            self.base_url + '/api/v1/users/me', headers={'Authorization': 'Bearer %s' % self.token})
        if user_response.status_code == 200:
            return user_response.json()
        else:
            raise APIError('Could not fetch user details', user_response)

    def create_token(self, username, password, application=None):
        if application is None:
            application = 'Highwinds Python client'

        # Grab an access token to use to fetch user
        response = requests.post(self.base_url + '/auth/token', data={
            "username": username, "password": password, "grant_type": "password"
        }, headers={
            'User-Agent': application
        })
        auth = response.json()
        if 'access_token' not in auth:
            raise APIError('Could not fetch access token', response)
        access_token = auth['access_token']

        # Grab user's id and root account hash
        user_response = requests.get(self.base_url + '/api/v1/users/me', headers={'Authorization': 'Bearer %s' % access_token})
        user = user_response.json()
        if 'accountHash' not in user or 'id' not in user:
            raise APIError('Could not fetch user\'s root account hash', user_response)
        account_hash = user['accountHash']
        user_id = user['id']

        # Generate a new API token
        token_response = requests.post(self.base_url + ('/api/v1/accounts/{account_hash}/users/{user_id}/tokens'.format(
            account_hash=account_hash, user_id=user_id
        )), json={
            "password": password, "application": application
        }, headers={
            'Authorization': 'Bearer %s' % access_token,
            'Content-Type': 'application/json'
        })
        if 'token' not in token_response.json():
            raise APIError('Could not generate API token', token_response)
        self.token = token_response.json()['token']
        return self.token

    def purge(self, account_hash, urls):
        purge_response = requests.post(self.base_url + ('/api/v1/accounts/%s/purge' % account_hash), json={
            "list": urls
        }, headers={
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % self.token
        })
        if 'id' not in purge_response.json():
            raise APIError('Could not send purge batch', purge_response)
        return purge_response.json()['id']

    def purge_status(self, account_hash, job_id):
        status_response = requests.get(self.base_url + ('/api/v1/accounts/%s/purge/%s' % (account_hash, job_id,)), headers={
            'Authorization': 'Bearer %s' % self.token,
            })
        if 'progress' not in status_response.json():
            raise APIError('Could not fetch purge status', status_response)
        return float(status_response.json()['progress'])



def command(arguments=()):
    def apply_args(fn):
        def wrapper(self, *args, **kwargs):
            # Apply arguments
            for arg in arguments:
                name = arg['name']
                arg_copy = arg.copy()
                del arg_copy['name']
                self.parser.add_argument(name, **arg_copy)
            self.args = self.parser.parse_args()

            # Optionally turn on verbose logging
            if self.args.verbose:
                try:
                    import http.client as http_client
                except ImportError:
                    import httplib as http_client
                    http_client.HTTPConnection.debuglevel = 1

                # You must initialize logging, otherwise you'll not see debug output.
                logging.basicConfig()
                logging.getLogger().setLevel(logging.DEBUG)
                requests_log = logging.getLogger("requests.packages.urllib3")
                requests_log.setLevel(logging.DEBUG)
                requests_log.propagate = True

            # Load token store
            if not self.args.token:
                self.client.token = self.cache.get('token')
            else:
                self.client.token = self.args.token

            # Call original function
            fn(self, *args, **kwargs)
        return wrapper
    return apply_args


def authenticated(fn):
    def wrapper(self, *args, **kwargs):
        if self.client.token is None:
            sys.stderr.write(
                "This command requires authentication. Either run `highwinds init` to cache credentials locally, or "
                "supply the --token parameter on the command line.\n")
            exit(1)
        fn(self, *args, **kwargs)
    return wrapper


class Command:
    def __init__(self, cache=None):
        # Instantiate library
        base_url = os.environ.get('HIGHWINDS_BASE_URL', 'https://striketracker.highwinds.com')
        self.client = APIClient(base_url)
        self.cache = ConfigurationCache(cache)

        # Read in command line arguments
        self.parser = argparse.ArgumentParser(description='Interface to the Highwinds CDN Web Services')
        methodList = [method for method in dir(self) if callable(getattr(self, method)) and '_' not in method]
        methodList.sort()
        self.parser.add_argument('action', help=",".join(methodList))
        self.parser.add_argument('--token', help='Token to use for this action')
        self.parser.add_argument('-v', '--verbose', help='Turn on verbose logging', action='store_true')

        # Call command
        command = sys.argv[1] if len(sys.argv) > 1 else None
        if len(sys.argv) == 1:
            self.parser.print_help(file=sys.stdout)
        elif hasattr(self, sys.argv[1]):
            getattr(self, sys.argv[1])()
        else:
            sys.stderr.write("Unknown command: %s\n" % command)

    def _print(self, obj):
        yaml.dump(obj, sys.stdout, Dumper=SafeDumper, default_flow_style=False)

    @command([
        {'name': '--application', 'help': 'Name of application with which to register this token'}
    ])
    def init(self):
        sys.stdout.write("Initializing configuration...\n")
        if self.args.token:
            token = self.args.token
        else:
            token = self.client.create_token(
                username=raw_input('Username: '),
                password=getpass.getpass(),
                application=self.args.application if hasattr(self.args, 'application') else None
            )
        self.cache.set('token', token)
        sys.stdout.write('Successfully saved token\n')

    @command()
    def version(self):
        sys.stdout.write(self.client.version())
        sys.stdout.write("\n")

    @command()
    @authenticated
    def me(self):
        user = self.client.me()
        self._print(user)

    @command([
        {'name': 'account', 'help': 'Account from which to purge assets'},
        {'name': '--poll', 'help': 'Poll for purge status to be complete instead of returning id',
            'action': 'store_true'},
        {'name': '--invalidate-only', 'help': 'Force revalidation on assets instead of removing them',
            'action': 'store_true'},
        {'name': '--purge-all-dynamic', 'help': 'Purge all dynamic version of asset',
            'action': 'store_true'},
        {'name': '--recursive', 'help': 'Purge all assets at this path recursively',
            'action': 'store_true'},
        ])
    @authenticated
    def purge(self):
        sys.stderr.write('Reading urls from stdin\n')
        urls = []
        for url in sys.stdin:
            urls.append({
                "url": url.strip(),
                "purgeAllDynamic": self.args.purge_all_dynamic,
                "recursive": self.args.recursive,
                "invalidateOnly": self.args.invalidate_only
            })

        # Send batch to CDN
        try:
            job_id = self.client.purge(self.args.account, urls)
        except APIError as e:
            exit(1)

        # Optionally poll for progress
        if self.args.poll:
            progress = 0.0
            sys.stderr.write('Sending purge...')
            while progress < 1.0:
                progress = self.client.purge_status(self.args.account, job_id)
                sys.stderr.write('.')
                time.sleep(0.1)
            sys.stderr.write('Done!\n')
        else:
            sys.stdout.write(job_id)
            sys.stdout.write("\n")

    @command([
        {'name': 'account', 'help': 'Account from which to purge assets'},
        {'name': 'job_id', 'help': 'Job id for which to fetch status'},
    ])
    @authenticated
    def purge_status(self):
        sys.stdout.write(self.client.purge_status(self.args.account, self.args.job_id))
        sys.stdout.write("\n")