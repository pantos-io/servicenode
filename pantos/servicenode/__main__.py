"""Entry point for running the Pantos service node application in
Flask's built-in web server.

"""
from pantos.servicenode.application import create_application
from pantos.servicenode.configuration import config

if __name__ == '__main__':
    application = create_application()
    host = config['application']['host']
    port = config['application']['port']
    ssl_certificate = config['application'].get('ssl_certificate')
    ssl_private_key = config['application'].get('ssl_private_key')
    ssl_context = (None if ssl_certificate is None else
                   (ssl_certificate, ssl_private_key))
    debug = config['application']['debug']
    application.run(host=host, port=port, ssl_context=ssl_context, debug=debug,
                    use_reloader=False)
