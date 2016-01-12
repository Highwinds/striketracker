striketracker
=============

Python client and command line interface to the Highwinds CDN

[![Build Status](https://travis-ci.org/Highwinds/striketracker.svg?branch=master)](https://travis-ci.org/Highwinds/striketracker)

## Installation instructions

striketracker is available via [pip](https://pip.pypa.io/en/stable/installing/). To install, run

    pip install striketracker

## Usage

    striketracker [command] [options]

Run `striketracker --help` to get a list of current commands.

## Authenticating

There are two ways to authenticate calls to the API from the command line client. If you wish
to securely store your token locally so you don't have to enter it each time,
you can simply run `striketracker init` and enter your username and password.

If you wish to enter your token when issuing a command, simply use the `--token` parameter to
specify the token you wish to use to perform the operation, for example:

    striketracker me --token 3mux90t8mu4890t39xtw93mytmw3yc0t93u90rxxt33ijk

To authenticate from the Python library, log into StrikeTracker and obtain an API token from the Edit Profile link
under the user menu on the top right of the application. This is a revocable API token that you can use to integrate
applications with the StrikeTracker API. Store this token in a secure place, generally an environment variable on the
production server that will be running your application. Then pass this as the token parameter to the APIClient.

## Example

To purge from the command line, simply run the purge command with your account hash and provide newline-delimited URLs
on stdin. You can use the `--poll` parameter in order to wait for the purge to complete before exiting. For example:

    $ echo //www.example.com/style.css | striketracker purge x1x2x3x4 --poll
    Reading urls from stdin
    Sending purge.................Done!

Here is an example of the same purge issued via the Python library bundled with the application:

    from striketracker import APIClient
    import sys
    import time

    # Initialize client
    client = APIClient(token='your token here')

    # Send purge request
    sys.stdout.write('Sending purge...')
    sys.stdout.flush()
    job_id = client.purge('x1x2x3x4', [
        {"url": "//www.example.com/style.css"}
    ])

    # Poll for purge completion
    while client.purge_status('x1x2x3x4', job_id) < 1.0:
        sys.stdout.write('.')
        sys.stdout.flush()
        time.sleep(0.5)
    sys.stdout.write('Done!\n')

### Integrating with testing environments

In order to integrate against testing environments, simply populate the STRIKETRACKER_BASE_URL environment
variable without a trailing slash.

    export STRIKETRACKER_BASE_URL=https://striketracker.highwinds.com
