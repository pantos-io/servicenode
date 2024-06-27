"""Module for creating, reading, updating, and deleting database
records.

"""
import datetime
import threading
import typing
import uuid

import sqlalchemy  # type: ignore
import sqlalchemy.exc  # type: ignore
import sqlalchemy.orm  # type: ignore
from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.database import get_session
from pantos.servicenode.database import get_session_maker
from pantos.servicenode.database.enums import TransferStatus
from pantos.servicenode.database.exceptions import DatabaseError
from pantos.servicenode.database.exceptions import SenderNonceNotUniqueError
from pantos.servicenode.database.models import UNIQUE_SENDER_NONCE_CONSTRAINT
from pantos.servicenode.database.models import Base
from pantos.servicenode.database.models import Bid
from pantos.servicenode.database.models import ForwarderContract
from pantos.servicenode.database.models import HubContract
from pantos.servicenode.database.models import TokenContract
from pantos.servicenode.database.models import Transfer

_forwarder_contract_lock = threading.Lock()
_hub_contract_lock = threading.Lock()
_token_contract_lock = threading.Lock()

B = typing.TypeVar('B', bound=Base)


def create_bid(source_blockchain: Blockchain,
               destination_blockchain: Blockchain, execution_time: int,
               valid_until: int, fee: int) -> None:
    """Create a bid database record.

    Parameters
    ----------
    source_blockchain : Blockchain
        The bid's source blockchain.
    destination_blockchain : Blockchain
        The bid's destination blockchain.
    execution_time : int
        The maximum execution time of a transfer on the source
        blockchain (in seconds).
    valid_until: int
        The maximum time until which the bid is valid (in seconds).
    fee : int
        The fee for a transfer (in PAN).

    """
    assert execution_time > 0
    assert valid_until > 0
    assert fee > 0
    bid = Bid(source_blockchain_id=source_blockchain.value,
              destination_blockchain_id=destination_blockchain.value,
              execution_time=execution_time, valid_until=valid_until, fee=fee)
    with get_session_maker().begin() as session:
        session.add(bid)
        session.flush()


def replace_bids(source_blockchain_id: int, destination_blockchain_id: int,
                 bids: typing.List[typing.Dict[typing.Any, typing.Any]]):
    """Deletes all bids which are used for the given source and destination
    blockchains and adds new one for those blockchains.

    Parameters
    ----------
    source_blockchain_id : int
        The bid's source blockchain.
    destination_blockchain_id : int
        The bid's destination blockchain.
    bids : List of dict
        A list of dicts, containing the fee, execution time and valid until
        attributes of a bid.

    """
    delete_statement = sqlalchemy.delete(Bid).where(
        sqlalchemy.and_(
            Bid.source_blockchain_id == source_blockchain_id,
            Bid.destination_blockchain_id == destination_blockchain_id))
    _bids = [Bid(**bid) for bid in bids]
    with get_session_maker().begin() as session:
        session.execute(delete_statement)
        # based on https://github.com/sqlalchemy/sqlalchemy/issues/2501
        session.flush()
        session.bulk_save_objects(_bids)


def create_transfer(source_blockchain: Blockchain,
                    destination_blockchain: Blockchain, sender_address: str,
                    recipient_address: str, source_token_address: str,
                    destination_token_address: str, amount: int, fee: int,
                    sender_nonce: int, signature: str, hub_address: str,
                    forwarder_address: str) -> int:
    """Create a transfer database record.

    Parameters
    ----------
    source_blockchain : Blockchain
        The token transfer's source blockchain.
    destination_blockchain : Blockchain
        The token transfer's destination blockchain.
    sender_address : str
        The address of the sender on the source blockchain.
    recipient_address : str
        The address of the recipient on the destination blockchain.
    source_token_address : str
        The address of the token on the source blockchain.
    destination_token_address : str
        The address of the token on the destination blockchain.
    amount : int
        The amount of tokens sent by the sender to the recipient.
    fee : int
        The fee for the transfer (in PAN) payed by the sender.
    sender_nonce : int
        The nonce of the sender at the Pantos Forwarder contract of the
        source blockchain.
    signature : str
        The signature of the sender for the transfer.
    hub_address : str
        The address of the Pantos Hub contract on the token transfer's
        source blockchain.
    forwarder_address : str
        The address of the Pantos Forwarder contract on the token
        transfer's source blockchain.

    Returns
    -------
    int
        The assigned ID of the created record.

    Raises
    ------
    SenderNonceNotUniqueError
        If the sender nonce is not unique.

    """
    try:
        with get_session_maker().begin() as session:
            # Create the source and destination token contract instances if
            # they do not exist yet
            source_token_contract = _read_token_contract(
                session, blockchain_id=source_blockchain.value,
                address=source_token_address)
            source_token_contract_id = (
                source_token_contract.id if source_token_contract is not None
                else _create_token_contract(
                    blockchain_id=source_blockchain.value,
                    address=source_token_address))
            destination_token_contract = _read_token_contract(
                session, blockchain_id=destination_blockchain.value,
                address=destination_token_address)
            destination_token_contract_id = (
                destination_token_contract.id if destination_token_contract
                is not None else _create_token_contract(
                    blockchain_id=destination_blockchain.value,
                    address=destination_token_address))
            # Create the hub and forwarder contract instances if they do not
            # exist yet
            hub_contract = _read_hub_contract(
                session, blockchain_id=source_blockchain.value,
                address=hub_address)
            hub_contract_id = (hub_contract.id if hub_contract is not None else
                               _create_hub_contract(
                                   blockchain_id=source_blockchain.value,
                                   address=hub_address))
            forwarder_contract = _read_forwarder_contract(
                session, blockchain_id=source_blockchain.value,
                address=forwarder_address)
            forwarder_contract_id = (forwarder_contract.id
                                     if forwarder_contract is not None else
                                     _create_forwarder_contract(
                                         blockchain_id=source_blockchain.value,
                                         address=forwarder_address))

            transfer = Transfer(
                source_blockchain_id=source_blockchain.value,
                destination_blockchain_id=destination_blockchain.value,
                sender_address=sender_address,
                recipient_address=recipient_address,
                source_token_contract_id=source_token_contract_id,
                destination_token_contract_id=destination_token_contract_id,
                amount=amount, fee=fee, sender_nonce=sender_nonce,
                signature=signature, hub_contract_id=hub_contract_id,
                forwarder_contract_id=forwarder_contract_id,
                status_id=TransferStatus.ACCEPTED.value)
            session.add(transfer)
            session.flush()
            return int(transfer.id)
    except sqlalchemy.exc.IntegrityError as e:
        session.rollback()
        if UNIQUE_SENDER_NONCE_CONSTRAINT in str(e):
            raise SenderNonceNotUniqueError(source_blockchain, sender_address,
                                            sender_nonce)
        raise


def read_cross_blockchain_bids(source_blockchain_id: int,
                               destination_blockchain_id: int) -> list[Bid]:
    """Reads the bids for a cross-blockchain transfer from the database.

    Parameters
    ----------
    source_blockchain_id : int
        The ID of the source blockchain.
    destination_blockchain_id : int
        The ID of the destination blockchain.

    Returns
    -------
    list of Bid
        The bids for a cross-blockchain transfer from the database.

    """
    statement = sqlalchemy.select(Bid).filter_by(
        source_blockchain_id=source_blockchain_id,
        destination_blockchain_id=destination_blockchain_id)
    with get_session() as session:
        bids = session.execute(statement).scalars().all()
        session.expunge_all()
        return list(bids)


def read_transfer_by_task_id(task_id: uuid.UUID) -> typing.Optional[Transfer]:
    """Read a transfer database record.

    Parameters
    ----------
    task_id : uuid.UUID
        The unique task ID of the transfer.

    Returns
    -------
    Transfer
        The transfer with the given task ID.

    """
    with get_session() as session:
        transfer = session.query(Transfer).filter_by(
            task_id=str(task_id)).first()
        if transfer is None:
            return None
        session.expunge(transfer)
        return transfer


def read_transfer_nonce(internal_transfer_id: int) -> int:
    """Read the nonce of a transfer database record.

    Parameters
    ----------
    internal_transfer_id : int
        The unique internal ID of the transfer.

    Returns
    -------
    int
        The nonce of the transfer.

    """
    statement = sqlalchemy.select(
        Transfer.nonce).filter(Transfer.id == internal_transfer_id)
    with get_session() as session:
        result = session.execute(statement).fetchall()
        return result[0][0]  # type: ignore


def reset_transfer_nonce(internal_transfer_id: int) -> None:
    """Update a transfer by setting its transaction nonce to NULL.

    Parameters
    ----------
    internal_transfer_id : int
        The unique internal ID of the transfer.

    """
    statement = sqlalchemy.update(Transfer).where(
        Transfer.id == internal_transfer_id).values(nonce=sqlalchemy.null())
    with get_session_maker().begin() as session:
        session.execute(statement)


def update_on_chain_transfer_id(internal_transfer_id: int,
                                on_chain_transfer_id: int) -> None:
    """Update the on-chain transfer ID of a transfer database record.

    Parameters
    ----------
    internal_transfer_id : int
        The unique internal ID of the transfer.
    on_chain_transfer_id : int
        The Pantos transfer ID assigned by the Pantos Hub contract on
        the source blockchain.

    Raises
    ------
    DatabaseError
        If there is no transfer database record for the given internal
        transfer ID.

    """
    with get_session_maker().begin() as session:
        transfer = session.get(Transfer, internal_transfer_id)
        if transfer is None:
            raise DatabaseError(
                f'unknown internal transfer ID: {internal_transfer_id}')
        transfer.on_chain_transfer_id = typing.cast(sqlalchemy.Column,
                                                    on_chain_transfer_id)
        transfer.updated = typing.cast(sqlalchemy.Column,
                                       datetime.datetime.utcnow())


def update_transfer_nonce(internal_transfer_id: int, blockchain: Blockchain,
                          latest_blockchain_nonce: int) -> None:
    """Update the nonce of a transfer database record.

    Parameters
    ----------
    internal_transfer_id : int
        The unique internal ID of the transfer.
    blockchain : Blockchain
        The blockchain on which the nonce is considered.
    latest_blockchain_nonce : int
        The latest nonce on the blockchain.

    """
    failed_transactions_expression = sqlalchemy.and_(
        Transfer.source_blockchain_id == blockchain.value,
        Transfer.nonce.is_not(None),  # noqa: E711
        sqlalchemy.or_(Transfer.status_id == TransferStatus.FAILED.value,
                       Transfer.status_id == TransferStatus.ACCEPTED.value))

    count_failed_nonces_subquery = sqlalchemy.select(
        sqlalchemy.func.count()).filter(
            failed_transactions_expression).scalar_subquery()

    minimum_failed_nonce_cte = sqlalchemy.select(
        sqlalchemy.func.min(Transfer.nonce).label('min')).filter(
            failed_transactions_expression).cte('minimum_failed_nonce_cte')

    maximum_transfer_nonce_subquery = sqlalchemy.select(
        sqlalchemy.func.max(
            Transfer.nonce)).filter(Transfer.source_blockchain_id ==
                                    blockchain.value).scalar_subquery()

    statement = sqlalchemy.update(Transfer).where(
        sqlalchemy.or_(
            Transfer.id == internal_transfer_id,
            sqlalchemy.and_(
                Transfer.source_blockchain_id == blockchain.value,
                Transfer.nonce == minimum_failed_nonce_cte.c.min))).values({
                    Transfer.nonce: sqlalchemy.case(
                        (count_failed_nonces_subquery == 0,
                         sqlalchemy.case((maximum_transfer_nonce_subquery
                                          >= latest_blockchain_nonce,
                                          maximum_transfer_nonce_subquery + 1),
                                         else_=latest_blockchain_nonce)),
                        (Transfer.id == internal_transfer_id,
                         minimum_failed_nonce_cte.c.min),
                        else_=sqlalchemy.null()),
                    Transfer.status_id: sqlalchemy.case(
                        (Transfer.id == internal_transfer_id,
                         TransferStatus.ACCEPTED_NEW_NONCE_ASSIGNED.value),
                        else_=sqlalchemy.case(
                            (Transfer.status_id == TransferStatus.FAILED.value,
                             TransferStatus.FAILED.value),
                            else_=TransferStatus.ACCEPTED.value))
                })
    with get_session_maker().begin() as session:
        # Execute the transaction
        session.execute(
            statement,
            execution_options=sqlalchemy.util._collections.immutabledict(
                {'synchronize_session': False}))


def update_transfer_status(internal_transfer_id: int,
                           status: TransferStatus) -> None:
    """Update the status of a transfer database record.

    Parameters
    ----------
    internal_transfer_id : int
        The unique internal ID of the transfer.
    status : TransferStatus
        The new status of the transfer.

    Raises
    ------
    DatabaseError
        If there is no transfer database record for the given internal
        transfer ID.

    """
    with get_session_maker().begin() as session:
        transfer = session.get(Transfer, internal_transfer_id)
        if transfer is None:
            raise DatabaseError(
                f'unknown internal transfer ID: {internal_transfer_id}')
        transfer.status_id = typing.cast(sqlalchemy.Column, status.value)
        if (status is TransferStatus.FAILED
                or status is TransferStatus.REVERTED):
            # In case of a failed or reverted transfer, the sender nonce
            # can be used again, which should thus not be excluded by
            # the unique sender nonce constraint
            transfer.sender_nonce = typing.cast(sqlalchemy.Column, None)
        transfer.updated = typing.cast(sqlalchemy.Column,
                                       datetime.datetime.utcnow())


def update_transfer_transaction_id(internal_transfer_id: int,
                                   transaction_id: str) -> None:
    """Update the transaction ID/hash of a transfer database record.

    Parameters
    ----------
    internal_transfer_id : int
        The unique internal ID of the transfer.
    transaction_id : str
        The ID/hash of the token transfer's transaction on the
        source blockchain.

    Raises
    ------
    DatabaseError
        If there is no transfer database record for the given internal
        transfer ID.

    """
    with get_session_maker().begin() as session:
        transfer = session.get(Transfer, internal_transfer_id)
        if transfer is None:
            raise DatabaseError(
                f'unknown internal transfer ID: {internal_transfer_id}')
        transfer.transaction_id = typing.cast(sqlalchemy.Column,
                                              transaction_id)
        transfer.updated = typing.cast(sqlalchemy.Column,
                                       datetime.datetime.utcnow())


def update_transfer_task_id(internal_transfer_id: int,
                            task_id: uuid.UUID) -> None:
    """Update the task ID of a transfer database record.

    Parameters
    ----------
    internal_transfer_id : int
        The unique internal ID of the transfer.
    task_id : uuid.UUID
        The unique task ID of the transfer.

    Raises
    ------
    DatabaseError
        If there is no transfer database record for the given internal
        transfer ID.

    """
    with get_session_maker().begin() as session:
        transfer = session.get(Transfer, internal_transfer_id)
        if transfer is None:
            raise DatabaseError(
                f'unknown internal transfer ID: {internal_transfer_id}')
        transfer.task_id = typing.cast(sqlalchemy.Column, str(task_id))
        transfer.updated = typing.cast(sqlalchemy.Column,
                                       datetime.datetime.utcnow())


def _create_forwarder_contract(**kwargs: typing.Any) -> int:
    return _create_instance(ForwarderContract, _forwarder_contract_lock,
                            **kwargs)


def _create_hub_contract(**kwargs: typing.Any) -> int:
    return _create_instance(HubContract, _hub_contract_lock, **kwargs)


def _create_instance(model: Base, lock: threading.Lock,
                     **kwargs: typing.Any) -> int:
    """Create a new model instance in a thread-safe manner.

    """
    with lock:
        with get_session_maker().begin() as session:
            # New session necessary to allow committing after the new
            # model instance has been added (flush is not sufficient in
            # a multithreaded environment)
            instance = session.query(model).filter_by(**kwargs).one_or_none()
            if instance is None:
                # Instance has been added by another thread in between
                instance = model(**kwargs)
                session.add(instance)
                session.flush()
            return instance.id


def _create_token_contract(**kwargs: typing.Any) -> int:
    return _create_instance(TokenContract, _token_contract_lock, **kwargs)


def _read_forwarder_contract(session: sqlalchemy.orm.Session,
                             **kwargs: typing.Any) -> ForwarderContract:
    return _read_instance(session, ForwarderContract, **kwargs)


def _read_hub_contract(session: sqlalchemy.orm.Session,
                       **kwargs: typing.Any) -> HubContract:
    return _read_instance(session, HubContract, **kwargs)


def _read_instance(session: sqlalchemy.orm.Session, model: typing.Type[B],
                   **kwargs: typing.Any) -> B:
    return typing.cast(B,
                       session.query(model).filter_by(**kwargs).one_or_none())


def _read_token_contract(session: sqlalchemy.orm.Session,
                         **kwargs: typing.Any) -> TokenContract:
    return _read_instance(session, TokenContract, **kwargs)
