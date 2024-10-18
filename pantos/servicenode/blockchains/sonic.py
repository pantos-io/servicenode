"""Module for Sonic-specific clients and errors. Since Sonic is
Ethereum-compatible, the client implementation inherits from the
pantos.servicenode.blockchains.ethereum module.

Note that Pantos used to support Sonic's predecessor Fantom. This module
was renamed accordingly on 2024-10-18.

"""
from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.blockchains.base import BlockchainClientError
from pantos.servicenode.blockchains.ethereum import EthereumClient
from pantos.servicenode.blockchains.ethereum import EthereumClientError


class SonicClientError(EthereumClientError):
    """Exception class for all Sonic client errors.

    """
    pass


class SonicClient(EthereumClient):
    """Sonic-specific blockchain client.

    """
    @classmethod
    def get_blockchain(cls) -> Blockchain:
        # Docstring inherited
        return Blockchain.SONIC

    @classmethod
    def get_error_class(cls) -> type[BlockchainClientError]:
        # Docstring inherited
        return SonicClientError
