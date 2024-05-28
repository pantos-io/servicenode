import dataclasses
import unittest

import pytest
from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.business.plugins import BidPluginInteractor
from pantos.servicenode.business.plugins import execute_bid_plugin
from pantos.servicenode.plugins.base import Bid
from pantos.servicenode.plugins.base import BidPluginError


class MockedBidPlugin:
    def __init__(self, raise_error=False):
        self.raise_error = raise_error

    def get_bids(self, source_blockchain_id, destination_blockchain_id):
        if self.raise_error:
            raise BidPluginError()
        return [
            Bid(source_blockchain_id, destination_blockchain_id, 75, 0, 0),
            Bid(source_blockchain_id, destination_blockchain_id, 30, 1, 1)
        ], 10


@unittest.mock.patch('pantos.servicenode.business.plugins.'
                     'get_blockchain_config')
@unittest.mock.patch('pantos.servicenode.business.plugins.execute_bid_plugin.'
                     'apply_async')
@unittest.mock.patch.object(BidPluginInteractor, 'replace_bids')
def test_execute_bid_plugin_correct(mocked_replace_bids, mocked_task,
                                    mocked_get_blockchain_config):
    mocked_replace_bids.return_value = 1

    task = execute_bid_plugin.s(Blockchain.ETHEREUM.value).apply()

    assert task is not None
    assert task.status == 'SUCCESS'
    mocked_replace_bids.assert_called_once_with(Blockchain.ETHEREUM)
    mocked_task.assert_called_once_with(args=[Blockchain.ETHEREUM.value],
                                        countdown=1)


@unittest.mock.patch('pantos.servicenode.business.plugins.'
                     'get_blockchain_config')
@unittest.mock.patch('pantos.servicenode.business.plugins.execute_bid_plugin.'
                     'apply_async')
@unittest.mock.patch.object(BidPluginInteractor, 'replace_bids')
def test_execute_bid_plugin_interactor_error(mocked_replace_bids, mocked_task,
                                             mocked_get_blockchain_config):
    mocked_replace_bids.side_effect = Exception()

    task = execute_bid_plugin.s(Blockchain.ETHEREUM.value).apply()

    assert task is not None
    assert task.status == 'SUCCESS'
    mocked_replace_bids.assert_called_once_with(Blockchain.ETHEREUM)
    mocked_task.assert_called_once_with(args=[Blockchain.ETHEREUM.value],
                                        countdown=60)


@pytest.mark.parametrize('bids_config', [{'arguments': {}}, {'args': {}}])
@unittest.mock.patch('pantos.servicenode.business.plugins.get_bid_plugin',
                     return_value=MockedBidPlugin(False))
@unittest.mock.patch('pantos.servicenode.business.plugins.'
                     'get_blockchain_client')
@unittest.mock.patch('pantos.servicenode.business.plugins.replace_bids')
@unittest.mock.patch('pantos.servicenode.business.plugins.get_plugin_config')
def test_replace_bids_correct(mocked_get_plugin_config, mocked_replace_bids,
                              mocked_get_blockchain_client,
                              mocked_get_bid_plugin, bids_config):
    mocked_get_plugin_config.return_value = {'bids': bids_config}
    bid_plugin_interactor = BidPluginInteractor()
    mocked_bid_plugin = MockedBidPlugin()
    mocked_get_blockchain_client().get_validator_fee_factor = \
        lambda blockchain: 1 if blockchain is Blockchain.ETHEREUM else 2
    bids, delay = mocked_bid_plugin.get_bids(Blockchain.ETHEREUM.value,
                                             Blockchain.CELO.value)

    delay = bid_plugin_interactor.replace_bids(Blockchain.ETHEREUM)

    assert delay == 10
    assert mocked_replace_bids.call_count == len(Blockchain)
    assert mocked_get_plugin_config.call_count == 1
    for bid in bids:
        bid.fee = bid.fee * 3
    bids_to_dics = [dataclasses.asdict(bid) for bid in bids]
    mocked_replace_bids.assert_called_with(Blockchain.ETHEREUM.value,
                                           Blockchain.CELO.value, bids_to_dics)


@unittest.mock.patch('pantos.servicenode.business.plugins.get_bid_plugin',
                     return_value=MockedBidPlugin(True))
@unittest.mock.patch('pantos.servicenode.business.plugins.'
                     'get_blockchain_client')
@unittest.mock.patch('pantos.servicenode.business.plugins.get_plugin_config',
                     return_value={'bids': {
                         'arguments': {}
                     }})
def test_replace_bids_plugin_error(mocked_get_plugin_config,
                                   mocked_get_blockchain_client,
                                   mocked_get_bid_plugin):
    bid_plugin_interactor = BidPluginInteractor()
    mocked_get_blockchain_client().get_validator_fee_factor.return_value = 1

    assert bid_plugin_interactor.replace_bids(Blockchain.ETHEREUM) == 60


@unittest.mock.patch('pantos.servicenode.business.plugins.get_bid_plugin')
@unittest.mock.patch('pantos.servicenode.business.plugins.'
                     'get_blockchain_client')
@unittest.mock.patch('pantos.servicenode.business.plugins.get_plugin_config',
                     return_value={'bids': {
                         'arguments': {}
                     }})
def test_replace_bids_error(mocked_get_plugin_config,
                            mocked_get_blockchain_client,
                            mocked_get_bid_plugin):
    bid_plugin_interactor = BidPluginInteractor()
    mocked_get_bid_plugin().get_bids.side_effect = Exception
    mocked_get_blockchain_client().get_validator_fee_factor.return_value = 1

    assert bid_plugin_interactor.replace_bids(Blockchain.ETHEREUM) == 60
