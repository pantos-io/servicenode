#!/usr/bin/env python3
"""Start the service node server."""

import subprocess
import sys
from importlib import resources

from pantos.servicenode.configuration import config
from pantos.servicenode.configuration import load_config

print('Loading the configuration...')
load_config()
print('Configuration loaded')

USER_NAME = 'pantos-service-node'
APP_DIRECTORY = '/opt/pantos/pantos-service-node'
WSGI_FILE = str(resources.path('pantos.servicenode', 'wsgi.py'))
NON_ROOT_DEFAULT_HTTPS_PORT = 8443
NON_ROOT_DEFAULT_HTTP_PORT = 8080
application_config = config['application']
host = application_config['host']
port = application_config['port']

ssl_certificate = application_config.get('ssl_certificate')
if ssl_certificate:
    ssl_private_key = application_config['ssl_private_key']
    print('SSL certificate found')

# Check if we got the --status argument
if '--status' in sys.argv:
    print('Checking the status of the server...')
    import requests
    protocol = 'https' if ssl_certificate else 'http'
    response = requests.get(f"{protocol}://{host}:{port}/health/live")
    response.raise_for_status()
    print('Server is running')
    sys.exit(0)
else:
    print('Starting the server...')

print(f'Starting the server on {host}:{port}...')
# the server should not run on a priviledged port (<1024)
if port < 1024:
    if ssl_certificate:
        default_port = NON_ROOT_DEFAULT_HTTPS_PORT
    else:
        default_port = NON_ROOT_DEFAULT_HTTP_PORT
    port_redirect_command = (
        'nft add table ip nat && nft -- add chain ip nat prerouting '
        '{ type nat hook prerouting priority -100 \\; } '
        f'&& nft add rule ip nat prerouting tcp dport {port} '
        f'redirect to :{default_port}')  # noqa E203
    print(
        f'Port {port} is a privileged port, redirecting to {default_port}...')
    try:
        completed_process = subprocess.run(port_redirect_command, text=True,
                                           shell=True,
                                           check=True)  # nosec B602
        print(completed_process.stdout)
    except subprocess.CalledProcessError as error:
        if 'command not found' in error.stderr:
            print(
                'nft is not installed, unable to redirect the '
                f'port to {port}; please reinstall the package '
                f'with the recommended dependencies. {error}', file=sys.stderr)
        else:
            print(f'unable to redirect the port to {port}: {error}',
                  file=sys.stderr)
    port = default_port

# build the port command (along with the ssl certificate info if requested)
gunicorn_command = (f"python -m gunicorn --bind {host}:{port} --workers 1 "
                    "pantos.servicenode.application:create_application()")
if ssl_certificate:
    gunicorn_command += (
        f" --certfile {ssl_certificate} --keyfile {ssl_private_key} ")
else:
    port_command = f'--port {port}'

server_run_command = ['runuser', '-u', USER_NAME, '--'
                      ] + gunicorn_command.split()

print(f'Starting the server with the command: {server_run_command}...')
subprocess.run(server_run_command, check=True, text=True)
