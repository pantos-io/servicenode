"""Unit tests for the pantos.servicenode.business.bids module.

"""
import dataclasses
import unittest.mock

import pytest
from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.business import bids as bids_module
from pantos.servicenode.business.bids import BidInteractor
from pantos.servicenode.business.bids import BidInteractorError

HUB_ADDRESS = 'hub_address'


@dataclasses.dataclass
class Bid:
    active: bool
    destination_blockchain: Blockchain
    execution_time: int
    valid_until: int
    locked_stake: int
    fee: int


class MockDatabaseAccess:

    def create_bid(self, source_blockchain, destination_blockchain,
                   execution_time, valid_until, fee):
        assert isinstance(source_blockchain, Blockchain)
        assert isinstance(destination_blockchain, Blockchain)
        assert isinstance(execution_time, int)
        assert execution_time > 0
        assert isinstance(valid_until, int)
        assert valid_until > 0
        assert isinstance(fee, int)
        assert fee > 0
        return 0

    def read_cross_blockchain_bids(self, source_blockchain,
                                   destination_blockchain):
        assert isinstance(source_blockchain, int)
        assert isinstance(destination_blockchain, int)
        return [
            Bid(True, destination_blockchain, 0, 0, 0, 0),
            Bid(True, destination_blockchain, 1, 1, 1, 1)
        ]


@pytest.fixture
def bid_interactor():
    return BidInteractor()


def generate_bids(blockchains,
                  number_bids,
                  only_active=True,
                  bid_id_offset=0,
                  extra_fee=0):
    all_bids = {}
    all_blockchain_ids = [blockchain.value for blockchain in Blockchain]
    for blockchain in blockchains:
        bids = {}
        first_bid_id = blockchain.value + bid_id_offset
        for bid_id in range(first_bid_id, first_bid_id + number_bids):
            active = only_active or (bid_id - bid_id_offset) % 2 == 0
            destination_blockchain = Blockchain(
                all_blockchain_ids[bid_id % len(Blockchain)])
            execution_time = (bid_id + 1) * 60
            valid_until = (bid_id + 1) * 60
            locked_stake = 1
            fee = (bid_id + 1) * 10**7 + extra_fee
            bids[bid_id] = Bid(active, destination_blockchain, execution_time,
                               valid_until, locked_stake, fee)
        all_bids[blockchain] = bids
    return all_bids


@pytest.fixture(autouse=True)
def mock_config(request, monkeypatch):
    active_marker = request.node.get_closest_marker('active')
    active = {} if active_marker is None else active_marker.args[0]
    config = {}
    config['blockchains'] = {}
    for blockchain in Blockchain:
        blockchain_name = blockchain.name.lower()
        config['blockchains'][blockchain_name] = {}
        config['blockchains'][blockchain_name]['active'] = blockchain in active
        config['blockchains'][blockchain_name]['hub'] = HUB_ADDRESS
    config['signer'] = {}
    config['signer']['pem'] = 'test.path'
    config['signer']['pem_password'] = '1234'

    def mock_get_signer_config():
        return config['signer']

    monkeypatch.setattr(bids_module, 'get_signer_config',
                        mock_get_signer_config)

    monkeypatch.setattr(bids_module, 'get_signer_config',
                        mock_get_signer_config)


@pytest.fixture(autouse=True)
def mock_database_access(monkeypatch):
    mock_database_access = MockDatabaseAccess()
    monkeypatch.setattr(bids_module, 'database_access', mock_database_access)


@unittest.mock.patch('pantos.servicenode.business.bids.get_signer')
def test_get_cross_blockchain_bids_correct(mocked_get_signer, bid_interactor):
    mocked_get_signer.return_value.sign_message.return_value = 'sig'
    bids = bid_interactor.get_cross_blockchain_bids(0, 1)
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
    'pantos.servicenode.business.bids.database_access.'
    'read_cross_blockchain_bids',
    side_effect=BidInteractorError)
def test_get_cross_blockchain_bids_error(mocked_db_read, bid_interactor):
    with pytest.raises(BidInteractorError):
        bid_interactor.get_cross_blockchain_bids(0, 1)
