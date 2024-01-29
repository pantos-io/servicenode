from unittest.mock import patch

with patch('pantos.servicenode.configuration.config'):
    import pantos.servicenode.celery  # noqa: F401
