import unittest.mock

import pytest
from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.blockchains.fantom import FantomClient
from pantos.servicenode.blockchains.fantom import FantomClientError


@pytest.fixture(scope='module')
@unittest.mock.patch.object(FantomClient, '__init__', lambda self: None)
def fantom_client():
    return FantomClient()


def test_get_blockchain_correct(fantom_client):
    assert fantom_client.get_blockchain() is Blockchain.FANTOM
    assert FantomClient.get_blockchain() is Blockchain.FANTOM


def test_get_error_class_correct(fantom_client):
    assert fantom_client.get_error_class() is FantomClientError
    assert FantomClient.get_error_class() is FantomClientError
