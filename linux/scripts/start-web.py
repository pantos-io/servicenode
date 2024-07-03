#!/usr/bin/env python3

import re
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

# apache2 should stop if already running
completed_process = subprocess.run('systemctl list-units --type=service',
                                   check=True, text=True, shell=True,
                                   capture_output=True)  # nosec B602
if 'apache2' in completed_process.stdout:
    print('Stopping apache2...')
    subprocess.run('systemctl stop apache2', check=True, text=True, shell=True,
                   capture_output=True)  # nosec B602
else:
    print('apache2 is not running')

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
    port = default_port
    try:
        completed_process = subprocess.run(port_redirect_command, text=True,
                                           shell=True, check=True,
                                           capture_output=True)  # nosec B602
        print(completed_process.stdout)
    except subprocess.CalledProcessError as error:
        if 'command not found' in error.stderr:
            print(
                'nft is not installed, unable to redirect the '
                'port; please reinstall the package with the recommended '
                'dependencies', file=sys.stderr)
        else:
            print('unable to redirect the port', file=sys.stderr)
        sys.exit(1)

# build the port command (along with the ssl certificate info if requested)
if ssl_certificate:
    server_name = re.sub(r'http.*?//|/.*', '', application_config['url'])
    port_command = (
        f'--https-port {port} --https-only --ssl-certificate-file '
        f'{ssl_certificate} --ssl-certificate-key-file {ssl_private_key} '
        f'--server-name {server_name}')
else:
    port_command = f'--port {port}'

server_run_command = (
    f'runuser -u {USER_NAME} -- bash -c "source {APP_DIRECTORY}/bin/activate; '
    f'nohup mod_wsgi-express start-server --host {host} {port_command} '
    f'{WSGI_FILE} --log-to-terminal &"')
print('Starting the server...')
subprocess.run(server_run_command, check=True, text=True,
               shell=True)  # nosec B602
