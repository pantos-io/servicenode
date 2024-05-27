import unittest.mock

import pytest
from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.blockchains.polygon import PolygonClient
from pantos.servicenode.blockchains.polygon import PolygonClientError


@pytest.fixture(scope='module')
@unittest.mock.patch.object(PolygonClient, '__init__', lambda self: None)
def polygon_client():
    return PolygonClient()


def test_get_blockchain_correct(polygon_client):
    assert polygon_client.get_blockchain() is Blockchain.POLYGON
    assert PolygonClient.get_blockchain() is Blockchain.POLYGON


def test_get_error_class_correct(polygon_client):
    assert polygon_client.get_error_class() is PolygonClientError
    assert PolygonClient.get_error_class() is PolygonClientError
