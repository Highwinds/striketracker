striketracker
=============

Python client and command line interface to the Highwinds CDN

[![Build Status](https://travis-ci.org/Highwinds/striketracker.svg?branch=master)](https://travis-ci.org/Highwinds/striketracker)

## Installation instructions

striketracker is available via PyPI. To install, run

    pip install striketracker

## Usage

    striketracker [command] [options]

Run `striketracker --help` to get a list of current commands.

## Example

To purge from the command line, simply run the purge command with your account hash and provide urls newline-delimited
on stdin:

    $ echo //www.example.com/style.css | striketracker purge x1x2x3x4 --poll
    Reading urls from stdin
    Sending purge.................Done!

The same is also possible via the Python library bundled with the application:

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

### Integrating with alternative environments

In order to integrate against alternative environments, simply populate the STRIKETRACKER_BASE_URL environment
variable without a trailing slash.