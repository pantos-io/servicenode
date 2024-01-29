import unittest.mock

import pytest

from pantos.common.blockchains.enums import Blockchain
from pantos.servicenode.blockchains.bnbchain import BnbChainClient
from pantos.servicenode.blockchains.bnbchain import BnbChainClientError


@pytest.fixture(scope='module')
@unittest.mock.patch.object(BnbChainClient, '__init__', lambda self: None)
def bnb_chain_client():
    return BnbChainClient()


def test_get_blockchain_correct(bnb_chain_client):
    assert bnb_chain_client.get_blockchain() is Blockchain.BNB_CHAIN
    assert BnbChainClient.get_blockchain() is Blockchain.BNB_CHAIN


def test_get_error_class_correct(bnb_chain_client):
    assert bnb_chain_client.get_error_class() is BnbChainClientError
    assert BnbChainClient.get_error_class() is BnbChainClientError
