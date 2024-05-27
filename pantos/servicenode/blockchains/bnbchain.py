"""Module for BNB-Chain-specific clients and errors. Since the BNB
Smart Chain is Ethereum-compatible, the client implementation inherits
from the pantos.servicenode.blockchains.ethereum module.

"""
from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.blockchains.base import BlockchainClientError
from pantos.servicenode.blockchains.ethereum import EthereumClient
from pantos.servicenode.blockchains.ethereum import EthereumClientError


class BnbChainClientError(EthereumClientError):
    """Exception class for all BNB Chain client errors.

    """
    pass


class BnbChainClient(EthereumClient):
    """BNB-Chain-specific blockchain client.

    """
    @classmethod
    def get_blockchain(cls) -> Blockchain:
        # Docstring inherited
        return Blockchain.BNB_CHAIN

    @classmethod
    def get_error_class(cls) -> type[BlockchainClientError]:
        # Docstring inherited
        return BnbChainClientError
