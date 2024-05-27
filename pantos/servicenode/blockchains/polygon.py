"""Module for Polygon-specific clients and errors. Since Polygon is
Ethereum-compatible, the client implementation inherits from the
pantos.servicenode.blockchains.ethereum module.

"""
from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.blockchains.base import BlockchainClientError
from pantos.servicenode.blockchains.ethereum import EthereumClient
from pantos.servicenode.blockchains.ethereum import EthereumClientError


class PolygonClientError(EthereumClientError):
    """Exception class for all Polygon client errors.

    """
    pass


class PolygonClient(EthereumClient):
    """Polygon-specific blockchain client.

    """
    @classmethod
    def get_blockchain(cls) -> Blockchain:
        # Docstring inherited
        return Blockchain.POLYGON

    @classmethod
    def get_error_class(cls) -> type[BlockchainClientError]:
        # Docstring inherited
        return PolygonClientError
