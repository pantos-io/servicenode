import time
import typing

from pantos.common.blockchains.enums import Blockchain
from pantos.common.configuration import Config

from pantos.servicenode.plugins.base import Bid
from pantos.servicenode.plugins.base import BidPlugin
from pantos.servicenode.plugins.base import BidPluginError

_DEFAULT_CONFIGURATION_FILE_NAME: typing.Final[str] = 'service-node-bids.yml'
"""Default configuration file name."""

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

    def get_bids(self, source_blockchain_id: int,
                 destination_blockchain_id: int,
                 **kwargs: typing.Any) -> tuple[list[Bid], int]:
        # Docstring inherited
        self._load_bids_config(kwargs['file_path'])
        assert self.config is not None

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
            self.config = Config(_DEFAULT_CONFIGURATION_FILE_NAME)
            self.config.load(_BIDS_SCHEMA, path)
