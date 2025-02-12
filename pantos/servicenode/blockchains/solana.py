"""Module for Solana-specific clients and errors.

"""
import typing
import uuid

from hexbytes import HexBytes
from pantos.common.blockchains.enums import Blockchain
from pantos.common.types import BlockchainAddress

from pantos.servicenode.blockchains.base import BlockchainClient
from pantos.servicenode.blockchains.base import BlockchainClientError


class SolanaClientError(BlockchainClientError):
    """Exception class for all Solana client errors.

    """
    pass


class SolanaClient(BlockchainClient):
    """Solana-specific blockchain client.

    """
    def __init__(self):
        # Docstring inherited
        pass  # pragma: no cover

    @classmethod
    def get_blockchain(cls) -> Blockchain:
        # Docstring inherited
        return Blockchain.SOLANA

    @classmethod
    def get_error_class(cls) -> type[BlockchainClientError]:
        # Docstring inherited
        return SolanaClientError

    def get_own_address(self) -> BlockchainAddress:
        # Docstring inherited
        raise NotImplementedError  # pragma: no cover

    def is_node_registered(self) -> bool:
        # Docstring inherited
        return False  # pragma: no cover

    def is_valid_recipient_address(self, recipient_address: str) -> bool:
        # Docstring inherited
        raise NotImplementedError  # pragma: no cover

    def read_external_token_record(
            self, request: BlockchainClient.ExternalTokenRecordRequest) \
            -> BlockchainClient.ExternalTokenRecordResponse:
        # Docstring inherited
        raise NotImplementedError  # pragma: no cover

    def read_minimum_deposit(self) -> int:
        # Docstring inherited
        raise NotImplementedError  # pragma: no cover

    def read_node_url(self) -> str:
        # Docstring inherited
        raise NotImplementedError  # pragma: no cover

    def register_node(self, node_url: str, node_deposit: int,
                      withdrawal_address: BlockchainAddress) -> None:
        # Docstring inherited
        raise NotImplementedError  # pragma: no cover

    def start_transfer_submission(
            self, request: BlockchainClient.TransferSubmissionStartRequest) \
            -> uuid.UUID:
        # Docstring inherited
        raise NotImplementedError  # pragma: no cover

    def start_transfer_from_submission(
            self,
            request: BlockchainClient.TransferFromSubmissionStartRequest) \
            -> uuid.UUID:
        # Docstring inherited
        raise NotImplementedError  # pragma: no cover

    def unregister_node(self) -> None:
        # Docstring inherited
        raise NotImplementedError  # pragma: no cover

    def update_node_url(self, node_url: str) -> None:
        # Docstring inherited
        raise NotImplementedError  # pragma: no cover

    def is_unbonding(self) -> bool:
        # Docstring inherited
        raise NotImplementedError  # pragma: no cover

    def cancel_unregistration(self) -> None:
        # Docstring inherited
        raise NotImplementedError  # pragma: no cover

    def calculate_commitment(self, abi_types: list[str],
                             values: list[typing.Any]) -> HexBytes:
        # Docstring inherited
        raise NotImplementedError

    def get_commitment_wait_period(self, blockchain: Blockchain) -> int:
        # Docstring inherited
        raise NotImplementedError

    def get_validator_fee_factor(self, blockchain: Blockchain) -> int:
        # Docstring inherited
        raise NotImplementedError  # pragma: no cover

    def _read_on_chain_transfer_id(self, transaction_id: str,
                                   destination_blockchain: Blockchain) -> int:
        # Docstring inherited
        raise NotImplementedError  # pragma: no cover
