"""Base classes for all blockchain clients and errors.

"""
import abc
import dataclasses
import logging
import typing
import uuid

from pantos.common.blockchains.base import BlockchainHandler
from pantos.common.blockchains.base import BlockchainUtilities
from pantos.common.blockchains.base import BlockchainUtilitiesError
from pantos.common.blockchains.base import NodeConnections
from pantos.common.blockchains.enums import Blockchain
from pantos.common.blockchains.enums import ContractAbi
from pantos.common.blockchains.factory import get_blockchain_utilities
from pantos.common.blockchains.factory import initialize_blockchain_utilities
from pantos.common.entities import TransactionStatus
from pantos.common.exceptions import ErrorCreator
from pantos.common.types import BlockchainAddress
from pantos.common.types import ContractFunctionArgs

from pantos.servicenode.configuration import get_blockchain_config
from pantos.servicenode.exceptions import ServiceNodeError

_logger = logging.getLogger(__name__)


class BlockchainClientError(ServiceNodeError):
    """Exception class for all blockchain client errors.

    """
    pass


class InsufficientBalanceError(BlockchainClientError):
    """Exception class for all blockchain client errors caused by an
    insufficient balance.

    """
    def __init__(self, **kwargs: typing.Any):
        # Docstring inherited
        super().__init__('insufficient balance', **kwargs)


class InvalidSignatureError(BlockchainClientError):
    """Exception class for all blockchain client errors caused by an
    invalid signature.

    """
    def __init__(self, **kwargs: typing.Any):
        # Docstring inherited
        super().__init__('invalid signature', **kwargs)


class UnresolvableTransferSubmissionError(BlockchainClientError):
    """Exception to be raised if there has been an unresolvable error
    during a single-chain transfer or cross-chain transferFrom
    submission.

    """
    def __init__(self, **kwargs: typing.Any):
        # Docstring inherited
        super().__init__('unresolvable transfer/transferFrom submission error',
                         **kwargs)


class BlockchainClient(BlockchainHandler, ErrorCreator[BlockchainClientError]):
    """Base class for all blockchain clients.

    """
    def __init__(self):
        """Construct a blockchain client instance.

        Raises
        ------
        BlockchainClientError
            If the corresponding blockchain utilities cannot be
            initialized.

        """
        blockchain_node_url = self._get_config()['provider']
        fallback_blockchain_nodes_urls = self._get_config().get(
            'fallback_providers', [])
        average_block_time = self._get_config()['average_block_time']
        required_transaction_confirmations = \
            self._get_config()['confirmations']
        transaction_network_id = self._get_config().get('chain_id')
        private_key = self._get_config()['private_key']
        private_key_password = self._get_config()['private_key_password']
        try:
            initialize_blockchain_utilities(
                self.get_blockchain(), [blockchain_node_url],
                fallback_blockchain_nodes_urls, average_block_time,
                required_transaction_confirmations, transaction_network_id,
                default_private_key=(private_key, private_key_password),
                celery_tasks_enabled=True)
        except BlockchainUtilitiesError:
            raise self._create_error(
                f'unable to initialize the {self.get_blockchain_name()} '
                'utilities')

    @abc.abstractmethod
    def is_node_registered(self) -> bool:
        """Determine if the service node is registered at the Pantos Hub
        on the blockchain.

        Returns
        -------
        bool
            True if the service node is registered, else False.

        Raises
        ------
        BlockchainClientError
            If it cannot be determined if the service node is
            registered.

        """
        pass  # pragma: no cover

    def is_valid_address(self, address: str) -> bool:
        """Determine if an address string is a valid address on the
        blockchain.

        Parameters
        ----------
        address : str
            The address string to check.

        Returns
        -------
        bool
            True if the given address string is a valid address on the
            blockchain, else False.

        """
        return self._get_utilities().is_valid_address(
            address)  # pragma: no cover

    @abc.abstractmethod
    def is_valid_recipient_address(self, recipient_address: str) -> bool:
        """Determine if an address string is a valid recipient address
        on the blockchain.

        Parameters
        ----------
        recipient_address : str
            The address string to check.

        Returns
        -------
        bool
            True if the given address string is a valid recipient
            address on the blockchain.

        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def read_node_url(self) -> str:
        """Read the service node's URL that is registered at the Pantos
        Hub on the blockchain.

        Returns
        -------
        str
            The service node's registered URL.

        Raises
        ------
        BlockchainClientError
            If the service node's registered URL cannot be read.

        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def register_node(self, node_url: str, node_stake: int,
                      unstaking_address: BlockchainAddress) -> None:
        """Register the service node at the Pantos Hub on the blockchain.

        Parameters
        ----------
        node_url : str
            The service node's URL to be registered.
        node_stake : int
            The service node's stake to be locked (must be at least the
            minimum required service node stake at the Pantos Hub).
        unstaking_address : str
            The address where the stake will be returned when the
            service node will be unregistered.

        Raises
        ------
        BlockchainClientError
            If the service node cannot be registered.

        """
        pass  # pragma: no cover

    @dataclasses.dataclass
    class TransferSubmissionStartRequest:
        """Request data for starting a single-chain transfer submission.

        Attributes
        ----------
        internal_transfer_id : int
            The internal unique ID of the transfer record.
        sender_address : str
            The sender's blockchain address.
        recipient_address : str
            The recipient's blockchain address.
        token_address : str
            The transferred token's blockchain address.
        amount : int
            The transferred token amount (in 10^-d units, where d is the
            token's number of decimals).
        fee : int
            The fee in 10^-8 PAN a user has to pay for the token
            transfer.
        sender_nonce : int
            The unique nonce of the sender for the token transfer.
        valid_until : int
            The timestamp until when the token transfer is valid (in
            seconds since the epoch).
        signature : str
            The sender's token transfer signature.

        """
        internal_transfer_id: int
        sender_address: str
        recipient_address: str
        token_address: str
        amount: int
        fee: int
        sender_nonce: int
        valid_until: int
        signature: str

    @abc.abstractmethod
    def start_transfer_submission(
            self, request: TransferSubmissionStartRequest) -> uuid.UUID:
        """Start a single-chain transfer submission. The transaction is
        automatically resubmitted with higher transaction fees until it
        is included in a block.

        Parameters
        ----------
        request : TransferSubmissionStartRequest
            The request data.

        Returns
        -------
        uuid.UUID
            The unique internal transaction ID.

        Raises
        ------
        InsufficientBalanceError
            If the sender's balance is insufficient.
        InvalidSignatureError
            If the sender's signature is invalid.
        BlockchainClientError
            If the transfer submission cannot be processed or started
            for any other reason.

        """
        pass  # pragma: no cover

    @dataclasses.dataclass
    class TransferFromSubmissionStartRequest:
        """Request data for starting a cross-chain transferFrom
        submission.

        Attributes
        ----------
        internal_transfer_id : int
            The internal unique ID of the transfer record.
        destination_blockchain : Blockchain
            The token transfer's destination blockchain.
        sender_address : str
            The sender's address on the source blockchain.
        recipient_address : str
            The recipient's address on the destination blockchain.
        source_token_address : str
            The transferred token's address on the source blockchain.
        destination_token_address : str
            The transferred token's address on the destination
            blockchain.
        amount : int
            The transferred token amount (in 10^-d units, where d is the
            token's number of decimals).
        fee : int
            The fee in 10^-8 PAN a user has to pay for the token
            transfer.
        sender_nonce : int
            The unique nonce of the sender for the token transfer on the
            source blockchain.
        valid_until : int
            The timestamp until when the token transfer is valid on the
            source blockchain (in seconds since the epoch).
        signature : str
            The sender's token transfer signature.

        """
        internal_transfer_id: int
        destination_blockchain: Blockchain
        sender_address: str
        recipient_address: str
        source_token_address: str
        destination_token_address: str
        amount: int
        fee: int
        sender_nonce: int
        valid_until: int
        signature: str

    @abc.abstractmethod
    def start_transfer_from_submission(
            self, request: TransferFromSubmissionStartRequest) -> uuid.UUID:
        """Start a cross-chain transferFrom submission. The transaction
        is automatically resubmitted with higher transaction fees until
        it is included in a block.

        Parameters
        ----------
        request : TransferFromSubmissionStartRequest
            The request data.

        Returns
        -------
        uuid.UUID
            The unique internal transaction ID.

        Raises
        ------
        InsufficientBalanceError
            If the sender's balance is insufficient.
        InvalidSignatureError
            If the sender's signature is invalid.
        BlockchainClientError
            If the transferFrom submission cannot be processed or
            started for any other reason.

        """
        pass  # pragma: no cover

    @dataclasses.dataclass
    class TransferSubmissionStatusResponse:
        """Response data from retrieving the status of a single-chain
        transfer or cross-chain transferFrom submission.

        Attributes
        ----------
        transaction_submission_completed : bool
            True if and only if the transaction submission has been
            completed (i.e. the transaction is either confirmed or
            reverted).
        transaction_status : TransactionStatus or None
            The status of the submitted (and eventually included)
            transaction (available if the transaction submission has
            been completed).
        transaction_id : str or None
            The ID/hash of the submitted (and eventually included)
            transaction (available if the transaction submission has
            been completed).
        on_chain_transfer_id : int or None
            The Pantos transfer ID on the source blockchain (available
            if the transaction has been confirmed).

        """
        transaction_submission_completed: bool
        transaction_status: typing.Optional[TransactionStatus] = None
        transaction_id: typing.Optional[str] = None
        on_chain_transfer_id: typing.Optional[int] = None

    def get_transfer_submission_status(
            self, internal_transaction_id: uuid.UUID,
            destination_blockchain: Blockchain) \
            -> TransferSubmissionStatusResponse:
        """Retrieve the status of a single-chain transfer or cross-chain
        transferFrom submission.

        Parameters
        ----------
        internal_transaction_id : uuid.UUID
            The unique internal transaction ID.
        destination_blockchain : Blockchain
            The token transfer's destination blockchain.

        Returns
        -------
        TransferSubmissionStatusResponse
            The response data.

        Raises
        ------
        UnresolvableTransferSubmissionError
            If there has been an unresolvable error during the
            transfer/transferFrom submission.
        BlockchainClientError
            If the Pantos transfer ID on the source blockchain cannot be
            read.

        """
        try:
            status_response = \
                self._get_utilities().get_transaction_submission_status(
                    internal_transaction_id)
        except BlockchainUtilitiesError:
            raise self._create_unresolvable_transfer_submission_error(
                internal_transaction_id=internal_transaction_id)
        _logger.info(
            'transfer/transferFrom transaction submission status',
            extra=vars(status_response)
            | {'internal_transaction_id': internal_transaction_id})
        if not status_response.transaction_submission_completed:
            return BlockchainClient.TransferSubmissionStatusResponse(False)
        transaction_status = status_response.transaction_status
        assert transaction_status in [
            TransactionStatus.CONFIRMED, TransactionStatus.REVERTED
        ]
        transaction_id = status_response.transaction_id
        assert transaction_id is not None
        on_chain_transfer_id = (None if transaction_status
                                is not TransactionStatus.CONFIRMED else
                                self._read_on_chain_transfer_id(
                                    transaction_id, destination_blockchain))
        return BlockchainClient.TransferSubmissionStatusResponse(
            True, transaction_status=transaction_status,
            transaction_id=transaction_id,
            on_chain_transfer_id=on_chain_transfer_id)

    @abc.abstractmethod
    def unregister_node(self) -> None:
        """Unregister the service node at the Pantos Hub on the
        blockchain.

        Raises
        ------
        BlockchainClientError
            If the service node cannot be unregistered.

        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def update_node_url(self, node_url: str) -> None:
        """Update the service node's URL that is registered at the
        Pantos Hub on the blockchain.

        Parameters
        ----------
        node_url : str
            The service node's new URL to be registered.

        Raises
        ------
        BlockchainClientError
            If the service node's registered URL cannot be updated.

        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def is_unbonding(self) -> bool:
        """Determine if the service node is during the unbonding period
        and has withdrawn its stake.

        Returns
        -------
        bool
            True if service node is during the unbonding period
            and has not withdrawn its stake, else false.

        Raises
        ------
        BlockchainClientError
            If the unbonding status cannot be checked.

        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def cancel_unregistration(self) -> None:
        """Cancel the service node unregistration.

        Raises
        ------
        BlockchainClientError
            If the unregistration cannot be cancelled.

        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def get_validator_fee_factor(self, blockchain: Blockchain) -> int:
        """Get the Validator fee factor of the given blockchain.

        Returns
        -------
            The Validator fee factor.

        Raises
        ------
        BlockchainClientError
            If the Validator factor cannot be obtained.

        """
        pass  # pragma: no cover

    def _create_insufficient_balance_error(
            self, **kwargs: typing.Any) -> BlockchainClientError:
        return self._create_error(
            specialized_error_class=InsufficientBalanceError, **kwargs)

    def _create_invalid_signature_error(
            self, **kwargs: typing.Any) -> BlockchainClientError:
        return self._create_error(
            specialized_error_class=InvalidSignatureError, **kwargs)

    def _create_unresolvable_transfer_submission_error(
            self, **kwargs: typing.Any) -> BlockchainClientError:
        return self._create_error(
            specialized_error_class=UnresolvableTransferSubmissionError,
            **kwargs)

    def _get_config(self) -> typing.Dict[str, typing.Any]:
        return get_blockchain_config(self.get_blockchain())  # pragma: no cover

    def _get_utilities(self) -> BlockchainUtilities:
        return get_blockchain_utilities(
            self.get_blockchain())  # pragma: no cover

    @abc.abstractmethod
    def _read_on_chain_transfer_id(self, transaction_id: str,
                                   destination_blockchain: Blockchain) -> int:
        """Read the Pantos transfer ID on the source blockchain.

        Parameters
        ----------
        transaction_id : str
            The ID/hash of the transaction.
        destination_blockchain : Blockchain
            The token transfer's destination blockchain.

        Returns
        -------
        int
            The Pantos transfer ID on the source blockchain.

        Raises
        ------
        BlockchainClientError
            If the Pantos transfer ID on the source blockchain cannot be
            read.

        """
        pass  # pragma: no cover

    @dataclasses.dataclass
    class _TransactionSubmissionStartRequest:
        """Request data for starting a transaction submission.

        Attributes
        ----------
        contract_abi : ContractAbi
            The ABI of the contract to invoke a function on in the
            transaction.
        function_selector : str
            The selector of the contract function to be invoked in the
            transaction.
        function_args : ContractFunctionArgs
            The arguments of the contract function to be invoked in the
            transaction.
        gas : int or None
            The gas to be provided for the transaction. Depending on the
            blockchain, it may not be necessary to specify the gas
            explicitly or it may be possible to estimate the required gas
            automatically.
        amount : int or None
            The amount of native coins to be sent in the transaction
            (specified in the blockchain's smallest coin denomination).
        nonce : int
            The unique transaction nonce of the account controlled by
            the default private key.

        """
        contract_abi: ContractAbi
        function_selector: str
        function_args: ContractFunctionArgs
        gas: typing.Optional[int]
        amount: typing.Optional[int]
        nonce: int

    def _start_transaction_submission(
            self, request: _TransactionSubmissionStartRequest,
            node_connections: NodeConnections) -> uuid.UUID:
        """Start a transaction submission. The transaction is
        automatically resubmitted with higher transaction fees until it
        is included in a block.

        Parameters
        ----------
        request : _TransactionSubmissionStartRequest
            The request data for starting a transaction submission.
        node_connections : NodeConnections
            The NodeConnections instance to be used when interacting
            with blockchain nodes.

        Returns
        -------
        uuid.UUID
            The unique internal transaction ID, which can be used later
            to retrieve the status of the transaction submission.

        Raises
        ------
        pantos.common.blockchains.base.MaxTotalFeePerGasExceededError
            If the maximum total fee per gas would be exceeded for the
            transaction to be submitted.
        pantos.common.blockchains.base.TransactionNonceTooLowError
            If the transaction has been submitted with a nonce too low.
        BlockchainUtilitiesError
            If the transaction submission cannot be started for any
            other reason.

        """
        if request.contract_abi is ContractAbi.PANTOS_HUB:
            contract_address = self._get_config()['hub']
        elif request.contract_abi is ContractAbi.PANTOS_TOKEN:
            contract_address = self._get_config()['pan_token']
        else:
            raise NotImplementedError
        min_adaptable_fee_per_gas = \
            self._get_config()['min_adaptable_fee_per_gas']
        max_total_fee_per_gas = self._get_config().get('max_total_fee_per_gas')
        adaptable_fee_increase_factor = \
            self._get_config()['adaptable_fee_increase_factor']
        blocks_until_resubmission = \
            self._get_config()['blocks_until_resubmission']
        request_ = BlockchainUtilities.TransactionSubmissionStartRequest(
            contract_address, request.contract_abi, request.function_selector,
            request.function_args, request.gas, min_adaptable_fee_per_gas,
            max_total_fee_per_gas, request.amount, request.nonce,
            adaptable_fee_increase_factor, blocks_until_resubmission)
        return self._get_utilities().start_transaction_submission(
            request_, node_connections)
