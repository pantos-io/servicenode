"""Business logic for handling token transfers.

"""
import dataclasses
import logging
import math
import time
import typing
import uuid

import celery  # type: ignore
from pantos.common.blockchains.enums import Blockchain
from pantos.common.entities import ServiceNodeBid
from pantos.common.entities import TransactionStatus
from pantos.common.signer import get_signer

from pantos.servicenode.blockchains.base import BlockchainClient
from pantos.servicenode.blockchains.base import InsufficientBalanceError
from pantos.servicenode.blockchains.base import InvalidSignatureError
from pantos.servicenode.blockchains.base import \
    UnresolvableTransferSubmissionError
from pantos.servicenode.blockchains.factory import get_blockchain_client
from pantos.servicenode.business.base import Interactor
from pantos.servicenode.business.base import InteractorError
from pantos.servicenode.business.bids import BidInteractorError
from pantos.servicenode.configuration import config
from pantos.servicenode.configuration import get_blockchain_config
from pantos.servicenode.configuration import get_signer_config
from pantos.servicenode.database import access as database_access
from pantos.servicenode.database.enums import TransferStatus
from pantos.servicenode.database.exceptions import SenderNonceNotUniqueError
from pantos.servicenode.plugins import get_bid_plugin

_logger = logging.getLogger(__name__)
"""Logger for this module."""


class TransferInteractorError(InteractorError):
    """Exception class for all transfer interactor errors.

    """
    pass


class TransferInteractorBidNotAcceptedError(TransferInteractorError):
    """Exception class for transfer bid not accepted by the service node
    maintainer custom reason.

    """
    pass


class TransferInteractorResourceNotFoundError(TransferInteractorError):
    """Exception class for transfer resource not found errors.

    """
    pass


class TransferInteractorUnrecoverableError(TransferInteractorError):
    """Exception class for all unrecoverable transfer
    interactor errors.

    """
    pass


class TransferInteractor(Interactor):
    """Interactor for handling token transfers.

    """
    @dataclasses.dataclass
    class ConfirmTransferRequest:
        """Request data for confirming the inclusion of a token transfer
        on the source blockchain.

        Attributes
        ----------
        internal_transfer_id : int
            The unique internal ID of the transfer.
        source_blockchain : Blockchain
            The token transfer's source blockchain.
        destination_blockchain : Blockchain
            The token transfer's destination blockchain.
        internal_transaction_id : uuid.UUID
            The unique internal transaction ID.

        """
        internal_transfer_id: int
        source_blockchain: Blockchain
        destination_blockchain: Blockchain
        internal_transaction_id: uuid.UUID

    def confirm_transfer(self, request: ConfirmTransferRequest) -> bool:
        """Confirm the inclusion of a token transfer on the source
        blockchain.

        Parameters
        ----------
        request : ConfirmTransferRequest
            The token transfer confirmation request data.

        Returns
        -------
        bool
            True if the transfer transaction is not unconfirmed anymore,
            i.e., if the transfer transaction is either confirmed or
            reverted.

        Raises
        ------
        TransferInteractorError
            If it cannot be determined if a token transfer is confirmed.

        """
        _logger.info('determining if a token transfer is confirmed',
                     extra=vars(request))
        try:
            extra_info = vars(request)
            source_blockchain_client = get_blockchain_client(
                request.source_blockchain)
            try:
                status_response = \
                    source_blockchain_client.get_transfer_submission_status(
                        request.internal_transaction_id,
                        request.destination_blockchain)
            except UnresolvableTransferSubmissionError:
                _logger.error('token transfer failed', extra=extra_info,
                              exc_info=True)
                database_access.reset_transfer_nonce(
                    request.internal_transfer_id)
                database_access.update_transfer_status(
                    request.internal_transfer_id, TransferStatus.FAILED)
                return True
            if not status_response.transaction_submission_completed:
                _logger.info('token transfer not yet confirmed',
                             extra=extra_info)
                return False
            transaction_status = status_response.transaction_status
            transaction_id = status_response.transaction_id
            assert transaction_id is not None
            extra_info |= {'transaction_id': transaction_id}
            if transaction_status is TransactionStatus.REVERTED:
                _logger.warning('token transfer reverted', extra=extra_info)
                database_access.update_transfer_status(
                    request.internal_transfer_id, TransferStatus.REVERTED)
                return True
            assert transaction_status is TransactionStatus.CONFIRMED
            on_chain_transfer_id = status_response.on_chain_transfer_id
            assert on_chain_transfer_id is not None
            extra_info |= {'on_chain_transfer_id': on_chain_transfer_id}
            _logger.info('token transfer confirmed', extra=extra_info)
            database_access.update_transfer_transaction_id(
                request.internal_transfer_id, transaction_id)
            database_access.update_on_chain_transfer_id(
                request.internal_transfer_id, on_chain_transfer_id)
            database_access.update_transfer_status(
                request.internal_transfer_id, TransferStatus.CONFIRMED)
            return True
        except Exception:
            raise TransferInteractorError(
                'unable to determine if a token transfer is confirmed',
                request=request)

    @dataclasses.dataclass
    class ExecuteTransferRequest:
        """Request data for executing a token transfer.

        Attributes
        ----------
        internal_transfer_id : int
            The unique internal ID of the transfer.
        source_blockchain : Blockchain
            The token transfer's source blockchain.
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
            The fee in 10^-8 PAN a user has to pay for the token transfer.
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
        source_blockchain: Blockchain
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

    def execute_transfer(self, request: ExecuteTransferRequest) -> uuid.UUID:
        """Execute a token transfer.

        Parameters
        ----------
        request : ExecuteTransferRequest
            The token transfer execution request data.

        Returns
        -------
        uuid.UUID
            The unique internal transaction ID.

        Raises
        ------
        TransferInteractorError
            If the token transfer cannot be executed.
        TransferInteractorUnrecoverableError
            If the token transfer cannot be executed or retried.

        """
        try:
            _logger.info('executing a token transfer', extra=vars(request))
            if request.valid_until < time.time():
                database_access.update_transfer_status(
                    request.internal_transfer_id, TransferStatus.FAILED)
                raise TransferInteractorUnrecoverableError(
                    'validity of the transfer request has expired',
                    request=request)
            if request.source_blockchain is request.destination_blockchain:
                internal_transaction_id = self.__single_chain_transfer(request)
            else:
                internal_transaction_id = self.__cross_chain_transfer(request)
            database_access.update_transfer_status(
                request.internal_transfer_id, TransferStatus.SUBMITTED)
            return internal_transaction_id
        except TransferInteractorUnrecoverableError:
            raise
        except Exception:
            raise TransferInteractorError('unable to execute a token transfer',
                                          request=request)

    def __single_chain_transfer(self,
                                request: ExecuteTransferRequest) -> uuid.UUID:
        if request.source_token_address != request.destination_token_address:
            database_access.update_transfer_status(
                request.internal_transfer_id, TransferStatus.FAILED)
            raise TransferInteractorUnrecoverableError(
                'source and destination token addresses must be equal for '
                'a single-chain token transfer', request=request)
        transfer_request = BlockchainClient.TransferSubmissionStartRequest(
            request.internal_transfer_id, request.sender_address,
            request.recipient_address, request.source_token_address,
            request.amount, request.fee, request.sender_nonce,
            request.valid_until, request.signature)
        source_blockchain_client = get_blockchain_client(
            request.source_blockchain)
        try:
            return source_blockchain_client.start_transfer_submission(
                transfer_request)
        except (InsufficientBalanceError, InvalidSignatureError):
            database_access.update_transfer_status(
                request.internal_transfer_id, TransferStatus.FAILED)
            raise TransferInteractorUnrecoverableError(
                'unable to send a single-chain transfer', request=request)
        except Exception:
            # Transfer should keep the status ACCEPTED because it was
            # temporarily assigned ACCEPTED_NEW_NONCE_ASSIGNED
            database_access.update_transfer_status(
                request.internal_transfer_id, TransferStatus.ACCEPTED)
            raise

    def __cross_chain_transfer(self,
                               request: ExecuteTransferRequest) -> uuid.UUID:
        transfer_from_request = \
            BlockchainClient.TransferFromSubmissionStartRequest(
                request.internal_transfer_id,
                request.destination_blockchain,
                request.sender_address, request.recipient_address,
                request.source_token_address,
                request.destination_token_address,
                request.amount, request.fee, request.sender_nonce,
                request.valid_until, request.signature)
        source_blockchain_client = get_blockchain_client(
            request.source_blockchain)
        try:
            return source_blockchain_client.start_transfer_from_submission(
                transfer_from_request)
        except (InsufficientBalanceError, InvalidSignatureError):
            database_access.update_transfer_status(
                request.internal_transfer_id, TransferStatus.FAILED)
            raise TransferInteractorUnrecoverableError(
                'unable to send a cross-chain transfer', request=request)
        except Exception:
            # Transfer should keep the status ACCEPTED because it was
            # temporarily assigned ACCEPTED_NEW_NONCE_ASSIGNED
            database_access.update_transfer_status(
                request.internal_transfer_id, TransferStatus.ACCEPTED)
            raise

    def __check_valid_until(self, source_blockchain: Blockchain,
                            valid_until: int, bid_execution_time: int,
                            time_received: float) -> None:
        """Check if a given execution time limit matches the execution time
        specified by a service node bid. The execution time limit must be at
        least the start time plus the service node bid's execution time.

        Parameters
        ----------
        source_blockchain : Blockchain
            The token transfer's source blockchain.
        valid_until : int
            The timestamp until when the token transfer is valid on the
            source blockchain (in seconds since the epoch).
        bid_execution_time : int
            The execution time specified by a service node bid.
        time_received : float
            The time at which the transfer request was received (in
            seconds since the epoch).

        Raises
        ------
        BidInteractorError
            If the given execution time limit does not match the execution time
            specified by a service node bid.

        """
        try:
            if not self.__is_valid_execution_time_limit(
                    source_blockchain, valid_until, bid_execution_time,
                    time_received):
                _logger.warning(
                    'new transfer request: invalid "valid until" timestamp '
                    f'{valid_until} for bid on '
                    f'{source_blockchain.name}')
                raise TransferInteractorBidNotAcceptedError(
                    message='"valid until" timestamp must be at least '
                    'the current timestamp plus the service '
                    'node bid\'s execution time', field_name='valid_until')
        except TransferInteractorBidNotAcceptedError:
            _logger.critical('unable to check the "valid until" timestamp',
                             exc_info=True)
            raise

    def __is_valid_execution_time_limit(
            self, blockchain: Blockchain, execution_time_limit: int,
            bid_execution_time: int,
            start_time: typing.Optional[float] = None) -> bool:
        """Check if a given execution time limit matches the execution
        time specified by a service node bid. The execution time limit
        must be at least the start time plus the service node bid's
        execution time.

        Parameters
        ----------
        blockchain : Blockchain
            The blockchain the service node bid is registered on.
        execution_time_limit : int
            The execution time limit (in seconds since the epoch) to
            check.
        bid_execution_time : int
            The execution time (in seconds) of the service node bid.
        start_time : float
            The start time (in seconds since the epoch) to check the
            execution time limit for (optional, default: current time).

        Returns
        -------
        bool
            True if the given execution time limit is valid for the
            service node bid, else False.

        Raises
        ------
        BidInteractorError
            If the service node bid's execution time limit cannot be
            checked.

        """
        try:
            start_time = time.time() if start_time is None else start_time
            return math.floor(start_time) + bid_execution_time <= \
                execution_time_limit
        except Exception:
            raise BidInteractorError(
                'unable to check a service node bid\'s execution time limit',
                blockchain=blockchain,
                execution_time_limit=execution_time_limit,
                start_time=start_time)

    def __check_valid_bid(self, bid: ServiceNodeBid, source_blockchain_id: int,
                          destination_blockchain_id: int) -> bool:
        """Checks if a given bid is valid. That includes checking if it expired
        and if the signature is valid.

        Parameters
        ----------
        fee : int
            The fee in 10^-8 PAN a user has to pay for the token transfer.
        bid_valid_until : int
            The timestamp until when the bid is valid (in seconds since
            the epoch).
        execution_time : int
            The time in seconds it takes to execute the token transfer.
        source_blockchain_id : int
            The token transfer's source blockchain ID.
        destination_blockchain_id : int
            The token transfer's destination blockchain ID.
        bid_signature : str
            The signature of the bid.

        Returns
        -------
        bool
            True if the bid is valid.

        Raises
        ------
        TransferInteractorBidNotAcceptedError
            If the given bid is not valid.

        """
        _logger.debug(
            'Checking if given bid is for source/destination blockchain')
        if (bid.source_blockchain != source_blockchain_id
                or bid.destination_blockchain != destination_blockchain_id):
            _logger.info(
                'new transfer request: invalid bid', extra={
                    'bid.fee': bid.fee,
                    'bid.valid_until': bid.valid_until,
                    'bid.execution_time': bid.execution_time,
                    'bid.source_blockchain': bid.source_blockchain,
                    'bid.destination_blockchain': bid.destination_blockchain,
                    'source_blockchain_id': source_blockchain_id,
                    'destination_blockchain_id': destination_blockchain_id,
                    'bid.signature': bid.signature
                })
            raise TransferInteractorBidNotAcceptedError(
                message='bid not valid for blockchain pair',
                field_name='bid.source_blockchain/bid.destination_blockchain')
        _logger.debug(
            'Bid is for correct blockchain pair. Checking if expired')

        bid_expired = self.__has_bid_expired(bid.valid_until)

        if bid_expired:
            _logger.info(
                'new transfer request: bid expired', extra={
                    'bid.fee': bid.fee,
                    'bid.valid_until': bid.valid_until,
                    'bid.execution_time': bid.execution_time,
                    'bid.source_blockchain': bid.source_blockchain,
                    'bid.destination_blockchain': bid.destination_blockchain,
                    'bid.signature': bid.signature
                })
            raise TransferInteractorBidNotAcceptedError(
                message='bid has expired', field_name='bid.valid_until')

        _logger.info('Bid has not expired. Verifying bids signature')
        valid_bid = self.__verify_bids_signature(int(bid.fee), bid.valid_until,
                                                 bid.execution_time,
                                                 source_blockchain_id,
                                                 destination_blockchain_id,
                                                 bid.signature)
        if not valid_bid:
            _logger.info(
                'new transfer request: invalid bid', extra={
                    'bid.fee': bid.fee,
                    'bid.valid_until': bid.valid_until,
                    'bid.execution_time': bid.execution_time,
                    'source_blockchain_id': source_blockchain_id,
                    'destination_blockchain_id': destination_blockchain_id,
                    'bid.signature': bid.signature
                })
            raise TransferInteractorBidNotAcceptedError(
                message='bid\'s signature is invalid',
                field_name='bid.signature')
        return valid_bid

    def __verify_bids_signature(self, fee: int, bid_valid_until: int,
                                execution_time: int, source_blockchain_id: int,
                                destination_blockchain_id: int,
                                bid_signature: str) -> bool:
        """Verifies a given bid if it has been signed correctly by the
        service node.

        Parameters
        ----------
        fee : int
            The fee of the bid.
        bid_valid_until : int
            The valid_until of the bid.
        execution_time : int
            The execution time of the bid.
        source_blockchain_id : int
            The id of the source blockchain.
        destination_blockchain_id : int
            The id of the destination blockchain.
        bid_signature : str
            The signature of the bid.

        Returns
        -------
        bool
            True if the bid is valid, False otherwise.
        """
        signer_config = get_signer_config()
        signer = get_signer(signer_config['pem'],
                            signer_config['pem_password'])
        bid_message = signer.build_message('', fee, bid_valid_until,
                                           source_blockchain_id,
                                           destination_blockchain_id,
                                           execution_time)
        return signer.verify_message(bid_message, bid_signature)

    def __has_bid_expired(self, bid_valid_until: int) -> bool:
        """Verifies if a bid has expired.

        Parameters
        ----------
        bid_valid_until : int
            The valid_until timestamp of a bid.

        Returns
        -------
        bool
            True if expired, False otherwise.
        """
        bid_expired = time.time() > bid_valid_until
        if bid_expired:
            _logger.info('bid expired')
            return True
        return False

    @dataclasses.dataclass
    class FindTransferResponse:
        """Response data for finding a token transfer by its unique task
        ID.

        Attributes
        ----------
        source_blockchain : Blockchain
            The token transfer's source blockchain.
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
            The fee of the service node bid accepted by the sender for
            the token transfer.
        status : TransferStatus
            The current status of the token transfer.
        transfer_id : int, optional
            The Pantos transfer ID on the source blockchain (if
            available).
        transaction_id : str, optional
            The ID/hash of the token transfer's transaction on the
            source blockchain (if available).

        """
        source_blockchain: Blockchain = Blockchain(0)
        destination_blockchain: Blockchain = Blockchain(0)
        sender_address: str = ''
        recipient_address: str = ''
        source_token_address: str = ''
        destination_token_address: str = ''
        amount: int = 0
        fee: int = 0
        status: TransferStatus = TransferStatus(0)
        transfer_id: typing.Optional[int] = None
        transaction_id: typing.Optional[str] = None

    def find_transfer(self, task_id: uuid.UUID) -> FindTransferResponse:
        """Find a token transfer by its unique task ID.

        Parameters
        ----------
        task_id : uuid.UUID
            The unique task ID of the token transfer.

        Returns
        -------
        FindTransferResponse
            The found token transfer data.

        Raises
        ------
        TransferInteractorError
            If the token transfer cannot be searched for.

        """
        _logger.info('searching for a token transfer: {}'.format(task_id))
        try:
            transfer = database_access.read_transfer_by_task_id(task_id)
            if transfer is None:
                raise TransferInteractorResourceNotFoundError(
                    f'resource with task_id "{task_id}" not found')
            return TransferInteractor.FindTransferResponse(
                Blockchain(typing.cast(int, transfer.source_blockchain_id)),
                Blockchain(typing.cast(int,
                                       transfer.destination_blockchain_id)),
                typing.cast(str, transfer.sender_address),
                typing.cast(str, transfer.recipient_address),
                transfer.source_token_contract.address,
                transfer.destination_token_contract.address,
                int(transfer.amount), int(transfer.fee),
                TransferStatus(typing.cast(int, transfer.status_id)),
                None if transfer.on_chain_transfer_id is None else int(
                    transfer.on_chain_transfer_id),
                typing.cast(str, transfer.transaction_id))
        except TransferInteractorResourceNotFoundError:
            raise
        except Exception:
            raise TransferInteractorError(
                'unable to search for a token transfer', task_id=task_id)

    @dataclasses.dataclass
    class InitiateTransferRequest:
        """Request data for initiating a new token transfer.

        Attributes
        ----------
        source_blockchain : Blockchain
            The token transfer's source blockchain.
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
        nonce : int
            The unique nonce of the sender for the token transfer on the
            source blockchain.
        valid_until : int
            The timestamp until when the token transfer is valid on the
            source blockchain (in seconds since the epoch).
        signature : str
            The sender's token transfer signature.
        time_received : float
            The time at which the transfer request was received (in
            seconds since the epoch).
        bid : ServiceNodeBid
            Bid used for the initiation of the transfer request.

        """
        source_blockchain: Blockchain
        destination_blockchain: Blockchain
        sender_address: str
        recipient_address: str
        source_token_address: str
        destination_token_address: str
        amount: int
        nonce: int
        valid_until: int
        signature: str
        time_received: float
        bid: ServiceNodeBid

    def initiate_transfer(self, request: InitiateTransferRequest) -> uuid.UUID:
        """Initiate a new token transfer. The token transfer is
        scheduled to be executed asynchronously.

        Parameters
        ----------
        request : InitiateTransferRequest
            The token transfer initiation request data.

        Returns
        -------
        uuid.UUID
            The unique task ID of the initiated token transfer.

        Raises
        ------
        SenderNonceNotUniqueError
            If the sender's nonce on the source blockchain is not unique
            in the database. Note that the nonce is not checked on chain
            at this point.
        TransferInteractorBidNotAcceptedError
            If the bid is not accepted by the service node maintainer due to
            custom reasons.
        TransferInteractorError
            If the token transfer cannot be initiated.

        """
        _logger.info('initiating a new token transfer', extra=vars(request))
        try:
            source_blockchain_config = get_blockchain_config(
                request.source_blockchain)
            source_blockchain_client = get_blockchain_client(
                request.source_blockchain)
            destination_blockchain_client = get_blockchain_client(
                request.destination_blockchain)
            assert source_blockchain_config['active']
            assert source_blockchain_config['registered']
            assert source_blockchain_client.is_valid_address(
                request.sender_address)
            assert destination_blockchain_client.is_valid_address(
                request.recipient_address)
            assert source_blockchain_client.is_valid_address(
                request.source_token_address)
            assert destination_blockchain_client.is_valid_address(
                request.destination_token_address)
            assert request.amount > 0
            assert request.time_received < time.time()
            if not get_bid_plugin().accept_bid(request.bid):
                _logger.info('bid declined by plugin', extra=vars(request.bid))
                raise TransferInteractorBidNotAcceptedError('bid not accepted')
            self.__check_valid_until(request.source_blockchain,
                                     request.valid_until,
                                     request.bid.execution_time,
                                     request.time_received)
            self.__check_valid_bid(request.bid,
                                   request.source_blockchain.value,
                                   request.destination_blockchain.value)
            # Write the transfer request data to the database
            internal_transfer_id = database_access.create_transfer(
                request.source_blockchain, request.destination_blockchain,
                request.sender_address, request.recipient_address,
                request.source_token_address,
                request.destination_token_address, request.amount,
                int(request.bid.fee), request.nonce, request.signature,
                source_blockchain_config['hub'],
                source_blockchain_config['forwarder'])
            # Schedule a new transfer task
            task_result = execute_transfer_task.delay(
                internal_transfer_id, request.source_blockchain.value,
                request.destination_blockchain.value, request.sender_address,
                request.recipient_address, request.source_token_address,
                request.destination_token_address, request.amount,
                request.bid.fee, request.nonce, request.valid_until,
                request.signature)

            task_id = uuid.UUID(task_result.id)
            # Add the transfer task ID to the database record
            database_access.update_transfer_task_id(internal_transfer_id,
                                                    task_id)
            return task_id
        except SenderNonceNotUniqueError:
            raise
        except TransferInteractorBidNotAcceptedError:
            raise
        except Exception:
            raise TransferInteractorError(
                'unable to initiate a new token transfer', request=request)


@celery.current_app.task(bind=True, max_retries=100)
def confirm_transfer_task(self, internal_transfer_id: int,
                          source_blockchain_id: int,
                          destination_blockchain_id: int,
                          internal_transaction_id: str) -> bool:
    """Celery task for confirming the inclusion of a token transfer on
    the source blockchain.

    Parameters
    ----------
    internal_transfer_id : int
        The unique internal ID of the transfer.
    source_blockchain_id : int
        The token transfer's source blockchain ID.
    destination_blockchain_id : int
        The token transfer's destination blockchain ID.
    internal_transaction_id : str
        The unique internal transaction ID.

    Returns
    -------
    bool
        True if the task is executed without error.

    """
    assert source_blockchain_id >= 0
    assert source_blockchain_id <= max(Blockchain)
    assert destination_blockchain_id >= 0
    assert destination_blockchain_id <= max(Blockchain)
    source_blockchain = Blockchain(source_blockchain_id)
    destination_blockchain = Blockchain(destination_blockchain_id)
    confirm_transfer_request = TransferInteractor.ConfirmTransferRequest(
        internal_transfer_id, source_blockchain, destination_blockchain,
        uuid.UUID(internal_transaction_id))
    try:
        confirmation_completed = TransferInteractor().confirm_transfer(
            confirm_transfer_request)
    except Exception as error:
        _logger.error('unable to confirm a token transfer',
                      extra=vars(confirm_transfer_request), exc_info=True)
        retry_interval = config['tasks']['confirm_transfer'][
            'retry_interval_after_error']
        raise self.retry(countdown=retry_interval, exc=error)
    if not confirmation_completed:
        retry_interval = config['tasks']['confirm_transfer']['interval']
        raise self.retry(countdown=retry_interval)
    return True


@celery.current_app.task(bind=True, max_retries=None)
def execute_transfer_task(self, internal_transfer_id: int,
                          source_blockchain_id: int,
                          destination_blockchain_id: int, sender_address: str,
                          recipient_address: str, source_token_address: str,
                          destination_token_address: str, amount: int,
                          fee: int, sender_nonce: int, valid_until: int,
                          signature: str) -> bool:
    """Celery task for executing a token transfer.

    Parameters
    ----------
    internal_transfer_id : int
        The unique internal ID of the transfer.
    source_blockchain_id : int
        The token transfer's source blockchain ID.
    destination_blockchain_id : int
        The token transfer's destination blockchain ID.
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
        The fee in 10^-8 PAN a user has to pay for the token transfer.
    sender_nonce : int
        The unique nonce of the sender for the token transfer on the
        source blockchain.
    valid_until : int
        The timestamp until when the token transfer is valid on the
        source blockchain (in seconds since the epoch).
    signature : str
        The sender's token transfer signature.

    Returns
    -------
    bool
        True if the task is executed without error.

    """
    assert source_blockchain_id >= 0
    assert source_blockchain_id <= max(Blockchain)
    assert destination_blockchain_id >= 0
    assert destination_blockchain_id <= max(Blockchain)
    source_blockchain = Blockchain(source_blockchain_id)
    destination_blockchain = Blockchain(destination_blockchain_id)
    execute_transfer_request = TransferInteractor.ExecuteTransferRequest(
        internal_transfer_id, source_blockchain, destination_blockchain,
        sender_address, recipient_address, source_token_address,
        destination_token_address, amount, fee, sender_nonce, valid_until,
        signature)
    try:
        internal_transaction_id = TransferInteractor().execute_transfer(
            execute_transfer_request)
        confirm_transfer_interval = config['tasks']['confirm_transfer'][
            'interval']
        confirm_transfer_task.apply_async(
            args=(internal_transfer_id, source_blockchain_id,
                  destination_blockchain_id, str(internal_transaction_id)),
            countdown=confirm_transfer_interval)
        return True
    except TransferInteractorUnrecoverableError as error:
        _logger.error(
            'unable to execute a token transfer - unrecoverable error',
            extra=error.details, exc_info=True)
        return False
    except TransferInteractorError as error:
        _logger.error('unable to execute a token transfer - retrying',
                      extra=error.details, exc_info=True)
        retry_interval = config['tasks']['execute_transfer'][
            'retry_interval_after_error']
        raise self.retry(countdown=retry_interval, exc=error)
