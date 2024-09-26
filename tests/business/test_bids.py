import dataclasses
import unittest.mock

import pytest

from pantos.servicenode.business import bids as bids_module
from pantos.servicenode.business.bids import BidInteractor
from pantos.servicenode.business.bids import BidInteractorError


@dataclasses.dataclass
class Bid:
    execution_time: int
    valid_until: int
    fee: int


class MockDatabaseAccess:
    def read_bids(self, source_blockchain_id, destination_blockchain_id):
        assert isinstance(source_blockchain_id, int)
        assert isinstance(destination_blockchain_id, int)
        return [Bid(0, 0, 0), Bid(1, 1, 1)]


@pytest.fixture(scope='module')
def bid_interactor():
    return BidInteractor()


@pytest.fixture(autouse=True)
def mock_get_signer_config(monkeypatch):
    config: dict[str, dict[str, str]] = {}
    config['signer'] = {}
    config['signer']['pem'] = 'test.path'
    config['signer']['pem_password'] = '1234'

    def mock_get_signer_config():
        return config['signer']

    monkeypatch.setattr(bids_module, 'get_signer_config',
                        mock_get_signer_config)


@pytest.fixture(autouse=True)
def mock_database_access(monkeypatch):
    mock_database_access = MockDatabaseAccess()
    monkeypatch.setattr(bids_module, 'database_access', mock_database_access)


@unittest.mock.patch('pantos.servicenode.business.bids.get_signer')
def test_get_current_bids_correct(mocked_get_signer, bid_interactor):
    mocked_get_signer.return_value.sign_message.return_value = 'sig'
    bids = bid_interactor.get_current_bids(0, 1)
    assert len(bids) == 2

    assert bids[0]['fee'] == 0
    assert bids[0]['execution_time'] == 0
    assert bids[0]['valid_until'] == 0
    assert bids[0]['signature'] == 'sig'

    assert bids[1]['fee'] == 1
    assert bids[1]['execution_time'] == 1
    assert bids[1]['valid_until'] == 1
    assert bids[1]['signature'] == 'sig'


@unittest.mock.patch(
    'pantos.servicenode.business.bids.database_access.read_bids',
    side_effect=BidInteractorError)
def test_get_current_bids_error(mocked_db_read, bid_interactor):
    with pytest.raises(BidInteractorError):
        bid_interactor.get_current_bids(0, 1)
