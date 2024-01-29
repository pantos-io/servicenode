import unittest.mock

import pytest

from pantos.common.blockchains.enums import Blockchain
from pantos.servicenode.blockchains.cronos import CronosClient
from pantos.servicenode.blockchains.cronos import CronosClientError


@pytest.fixture(scope='module')
@unittest.mock.patch.object(CronosClient, '__init__', lambda self: None)
def cronos_client():
    return CronosClient()


def test_get_blockchain_correct(cronos_client):
    assert cronos_client.get_blockchain() is Blockchain.CRONOS
    assert CronosClient.get_blockchain() is Blockchain.CRONOS


def test_get_error_class_correct(cronos_client):
    assert cronos_client.get_error_class() is CronosClientError
    assert CronosClient.get_error_class() is CronosClientError
