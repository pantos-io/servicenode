import datetime
import unittest.mock

import pytest
import sqlalchemy
import sqlalchemy.exc
from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.database.access import create_transfer
from pantos.servicenode.database.enums import TransferStatus
from pantos.servicenode.database.exceptions import SenderNonceNotUniqueError
from pantos.servicenode.database.models import UNIQUE_SENDER_NONCE_CONSTRAINT
from pantos.servicenode.database.models import Transfer


@pytest.mark.parametrize('forwarder_contract_existent', [True, False])
@pytest.mark.parametrize('hub_contract_existent', [True, False])
@pytest.mark.parametrize('destination_token_contract_existent', [True, False])
@pytest.mark.parametrize('source_token_contract_existent', [True, False])
@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_create_transfer_correct(
        mock_get_session_maker, source_token_contract_existent,
        destination_token_contract_existent, hub_contract_existent,
        forwarder_contract_existent, db_initialized_session,
        embedded_db_session_maker, bid, source_token_contract,
        destination_token_contract, hub_contract, forwarder_contract,
        source_blockchain_id, destination_blockchain_id,
        transfer_sender_address, transfer_recipient_address,
        source_token_address, destination_token_address, transfer_amount,
        bid_fee, transfer_sender_nonce, transfer_signature, hub_address,
        forwarder_address):
    mock_get_session_maker.return_value = embedded_db_session_maker
    db_initialized_session.add(bid)
    if source_token_contract_existent:
        db_initialized_session.add(source_token_contract)
    if destination_token_contract_existent:
        db_initialized_session.add(destination_token_contract)
    if hub_contract_existent:
        db_initialized_session.add(hub_contract)
    if forwarder_contract_existent:
        db_initialized_session.add(forwarder_contract)
    db_initialized_session.commit()

    internal_transfer_id = create_transfer(
        Blockchain(source_blockchain_id),
        Blockchain(destination_blockchain_id), transfer_sender_address,
        transfer_recipient_address, source_token_address,
        destination_token_address, transfer_amount, bid_fee,
        transfer_sender_nonce, transfer_signature, hub_address,
        forwarder_address)

    transfer = db_initialized_session.execute(
        sqlalchemy.select(Transfer)).one_or_none()[0]
    assert transfer.id == internal_transfer_id
    assert (not source_token_contract_existent
            or transfer.source_token_contract_id == source_token_contract.id)
    assert (not destination_token_contract_existent
            or transfer.destination_token_contract_id
            == destination_token_contract.id)
    assert (not hub_contract_existent
            or transfer.hub_contract_id == hub_contract.id)
    assert (not forwarder_contract_existent
            or transfer.forwarder_contract_id == forwarder_contract.id)
    _check_transfer(transfer, source_blockchain_id, destination_blockchain_id,
                    transfer_sender_address, transfer_recipient_address,
                    source_token_address, destination_token_address,
                    transfer_amount, transfer_sender_nonce, transfer_signature,
                    hub_address, forwarder_address, bid.execution_time,
                    bid.valid_until, bid.fee)


@unittest.mock.patch(
    'sqlalchemy.orm.session.Session.begin_nested',
    side_effect=sqlalchemy.exc.IntegrityError('', None, Exception()))
@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_create_transfer_race_conditions_correct(
        mock_get_session_maker, mock_begin_nested, db_initialized_session,
        embedded_db_session_maker, bid, source_token_contract,
        destination_token_contract, hub_contract, forwarder_contract,
        source_blockchain_id, destination_blockchain_id,
        transfer_sender_address, transfer_recipient_address,
        source_token_address, destination_token_address, transfer_amount,
        bid_fee, transfer_sender_nonce, transfer_signature, hub_address,
        forwarder_address):
    mock_get_session_maker.return_value = embedded_db_session_maker
    db_initialized_session.add(bid)
    db_initialized_session.add(source_token_contract)
    db_initialized_session.add(destination_token_contract)
    db_initialized_session.add(hub_contract)
    db_initialized_session.add(forwarder_contract)
    db_initialized_session.commit()
    read_id_return_values = [
        None, source_token_contract.id, None, destination_token_contract.id,
        None, hub_contract.id, None, forwarder_contract.id
    ]

    with unittest.mock.patch('pantos.servicenode.database.access._read_id',
                             side_effect=read_id_return_values):
        internal_transfer_id = create_transfer(
            Blockchain(source_blockchain_id),
            Blockchain(destination_blockchain_id), transfer_sender_address,
            transfer_recipient_address, source_token_address,
            destination_token_address, transfer_amount, bid_fee,
            transfer_sender_nonce, transfer_signature, hub_address,
            forwarder_address)

    transfer = db_initialized_session.execute(
        sqlalchemy.select(Transfer)).one_or_none()[0]
    assert transfer.id == internal_transfer_id
    assert transfer.source_token_contract_id == source_token_contract.id
    assert (transfer.destination_token_contract_id ==
            destination_token_contract.id)
    assert transfer.hub_contract_id == hub_contract.id
    assert transfer.forwarder_contract_id == forwarder_contract.id
    _check_transfer(transfer, source_blockchain_id, destination_blockchain_id,
                    transfer_sender_address, transfer_recipient_address,
                    source_token_address, destination_token_address,
                    transfer_amount, transfer_sender_nonce, transfer_signature,
                    hub_address, forwarder_address, bid.execution_time,
                    bid.valid_until, bid.fee)


@pytest.mark.parametrize(
    'error',
    [(sqlalchemy.exc.IntegrityError(UNIQUE_SENDER_NONCE_CONSTRAINT, None,
                                    Exception()), SenderNonceNotUniqueError),
     (sqlalchemy.exc.IntegrityError(
         '', None, Exception()), sqlalchemy.exc.IntegrityError)])
@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_create_transfer_error(mock_get_session_maker, error,
                               source_blockchain_id, destination_blockchain_id,
                               transfer_sender_address,
                               transfer_recipient_address,
                               source_token_address, destination_token_address,
                               transfer_amount, bid_fee, transfer_sender_nonce,
                               transfer_signature, hub_address,
                               forwarder_address):
    mock_get_session_maker().begin().__enter__().execute.side_effect = error[0]

    with pytest.raises(error[1]):
        create_transfer(Blockchain(source_blockchain_id),
                        Blockchain(destination_blockchain_id),
                        transfer_sender_address, transfer_recipient_address,
                        source_token_address, destination_token_address,
                        transfer_amount, bid_fee, transfer_sender_nonce,
                        transfer_signature, hub_address, forwarder_address)


def _check_transfer(transfer, source_blockchain_id, destination_blockchain_id,
                    transfer_sender_address, transfer_recipient_address,
                    source_token_address, destination_token_address,
                    transfer_amount, transfer_sender_nonce, transfer_signature,
                    hub_address, forwarder_address, bid_execution_time,
                    bid_valid_until, bid_fee):
    assert transfer.source_blockchain_id == source_blockchain_id
    assert transfer.destination_blockchain_id == destination_blockchain_id
    assert transfer.sender_address == transfer_sender_address
    assert transfer.recipient_address == transfer_recipient_address
    assert (
        transfer.source_token_contract.blockchain_id == source_blockchain_id)
    assert transfer.source_token_contract.address == source_token_address
    assert (transfer.destination_token_contract.blockchain_id ==
            destination_blockchain_id)
    assert (transfer.destination_token_contract.address ==
            destination_token_address)
    assert transfer.amount == transfer_amount
    assert transfer.sender_nonce == transfer_sender_nonce
    assert transfer.signature == transfer_signature
    assert transfer.hub_contract.blockchain_id == source_blockchain_id
    assert transfer.hub_contract.address == hub_address
    assert transfer.forwarder_contract.blockchain_id == source_blockchain_id
    assert transfer.forwarder_contract.address == forwarder_address
    assert transfer.task_id is None
    assert transfer.on_chain_transfer_id is None
    assert transfer.transaction_id is None
    assert transfer.nonce is None
    assert transfer.status_id == TransferStatus.ACCEPTED.value
    assert transfer.created < datetime.datetime.utcnow()
    assert transfer.updated is None
