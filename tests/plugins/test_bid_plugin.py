import time

import pytest

from pantos.servicenode.plugins.base import BidPluginError
from pantos.servicenode.plugins.bids import ConfigFileBidPlugin

FILE_PATH = 'bids.yml'


def test_get_bids_correct():
    plugin = ConfigFileBidPlugin()
    bids, delay = plugin.get_bids(0, 1, **{'file_path': FILE_PATH})
    assert len(bids) == 2
    assert delay > 0
    for bid in bids:
        assert bid.valid_until > time.time()


@pytest.mark.parametrize('source_blockchain_id', [0, 3])
def test_get_bids_bid_plugin_error(source_blockchain_id):
    plugin = ConfigFileBidPlugin()
    plugin.config = {
        'blockchains': {
            'ethereum': {
                'ethereum': [{
                    'execution_time': 600,
                    'fee': 50000000,
                    'valid_period': 300
                }]
            }
        }
    }
    with pytest.raises(BidPluginError):
        plugin.get_bids(source_blockchain_id, 1, **{'file_path': FILE_PATH})


def test_accept_bids():
    plugin = ConfigFileBidPlugin()
    bids, _ = plugin.get_bids(0, 1, **{'file_path': FILE_PATH})
    assert plugin.accept_bid(bids[0]) is True
