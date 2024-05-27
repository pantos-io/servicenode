"""Factory for blockchain clients.

"""
import typing

from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.blockchains.base import BlockchainClient
from pantos.servicenode.configuration import get_blockchain_config

_blockchain_clients: typing.Dict[Blockchain, BlockchainClient] = {}
"""Blockchain-specific client objects."""

_blockchain_client_classes = BlockchainClient.find_subclasses()
"""Blockchain-specific client classes."""


def initialize_blockchain_clients() -> None:
    """Initialize the blockchain-specific client objects for all active
    blockchains.

    """
    for blockchain in Blockchain:
        if get_blockchain_config(blockchain)['active']:
            blockchain_client = _blockchain_client_classes[blockchain]()
            _blockchain_clients[blockchain] = blockchain_client


def get_blockchain_client(blockchain: Blockchain) -> BlockchainClient:
    """Factory for blockchain-specific client objects.

    Parameters
    ----------
    blockchain : Blockchain
        The blockchain to get the client instance for.

    Returns
    -------
    BlockchainClient
        A blockchain client instance for the specified blockchain.

    """
    assert get_blockchain_config(blockchain)['active']
    return _blockchain_clients[blockchain]
