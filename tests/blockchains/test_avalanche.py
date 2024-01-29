import unittest.mock

import pytest

from pantos.common.blockchains.enums import Blockchain
from pantos.servicenode.blockchains.avalanche import AvalancheClient
from pantos.servicenode.blockchains.avalanche import AvalancheClientError


@pytest.fixture(scope='module')
@unittest.mock.patch.object(AvalancheClient, '__init__', lambda self: None)
def avalanche_client():
    return AvalancheClient()


def test_get_blockchain_correct(avalanche_client):
    assert avalanche_client.get_blockchain() is Blockchain.AVALANCHE
    assert AvalancheClient.get_blockchain() is Blockchain.AVALANCHE


def test_get_error_class_correct(avalanche_client):
    assert avalanche_client.get_error_class() is AvalancheClientError
    assert AvalancheClient.get_error_class() is AvalancheClientError
