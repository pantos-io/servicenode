import collections.abc
import time
import typing

from pantos.common.blockchains.enums import Blockchain
from pantos.common.configuration import Config
from pantos.servicenode.plugins.base import Bid
from pantos.servicenode.plugins.base import BidPlugin
from pantos.servicenode.plugins.base import BidPluginError

_BLOCKCHAIN_NAME_REGEX = "|".join([b.name.lower() for b in Blockchain])

_BIDS_SCHEMA = {
    'blockchains': {
        'type': 'dict',
        'keysrules': {
            'type': 'string',
            'regex': _BLOCKCHAIN_NAME_REGEX,
        },
        'valuesrules': {
            'type': 'dict',
            'keysrules': {
                'type': 'string',
                'regex': _BLOCKCHAIN_NAME_REGEX,
            },
            'valuesrules': {
                'type': 'list',
                'schema': {
                    'type': 'dict',
                    'schema': {
                        'execution_time': {
                            'type': 'integer',
                            'required': True
                        },
                        'fee': {
                            'type': 'integer',
                            'required': True
                        },
                        'valid_period': {
                            'type': 'integer',
                            'required': True
                        }
                    }
                }
            }
        }
    }
}


class ConfigFileBidPlugin(BidPlugin):
    """Pantos implementation of the bid plugin. It reads the bids from a
    configuration file and returns them. The configuration file must be
    provided as a keyword argument with the key 'file_path'.

    Attributes
    ----------
    config : Config
        The configuration object.
    delay : int
        The delay in seconds until the next bid calculation.
    """
    def __init__(self):
        """Initializes the plugin.
        """
        self.config = None
        self.delay = 60

    def get_bids(
            self, source_blockchain_id: int, destination_blockchain_id: int,
            **kwargs: typing.Any) \
            -> typing.Tuple[collections.abc.Iterable[Bid], int]:
        # Docstring inherited
        self._load_bids_config(kwargs['file_path'])

        source_blockchain_bids = self.config['blockchains'].get(
            Blockchain(source_blockchain_id).name.lower())

        if source_blockchain_bids is None:
            raise BidPluginError(
                f'no bids for source blockchain {source_blockchain_id}')

        bids = source_blockchain_bids.get(
            Blockchain(destination_blockchain_id).name.lower())
        if bids is None:
            raise BidPluginError(
                f'no bids for source blockchain {source_blockchain_id} and'
                f' destination blockchain {destination_blockchain_id}')

        bids = [
            Bid(source_blockchain_id, destination_blockchain_id, bid['fee'],
                bid['execution_time'],
                int(time.time()) + bid['valid_period']) for bid in bids
        ]

        return bids, self.delay

    def accept_bid(self, bid: Bid, **kwargs: typing.Any) -> bool:
        # Docstring inherited
        return True

    def _load_bids_config(self, path):
        if self.config is None:
            self.config = Config(path)
            self.config.load(_BIDS_SCHEMA)
