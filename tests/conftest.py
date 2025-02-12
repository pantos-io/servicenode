import pytest

from pantos.servicenode.protocol import get_supported_protocol_versions

COMMITMENT_WAIT_PERIOD = 10


def pytest_configure(config):
    # Prevent warnings for custom markers
    config.addinivalue_line('markers', 'is_registered')
    config.addinivalue_line('markers', 'to_be_registered')


@pytest.fixture(scope="session")
def config_dict(protocol_version):
    return {'protocol': str(protocol_version)}


@pytest.fixture(scope="session", params=get_supported_protocol_versions())
def protocol_version(request):
    return request.param


@pytest.fixture(scope="session")
def commitment_wait_period():
    return COMMITMENT_WAIT_PERIOD
