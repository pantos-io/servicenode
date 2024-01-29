"""Provides the Pantos service node application for deployments on
WSGI-compliant web servers.

"""
from pantos.servicenode.application import create_application

application = create_application()
