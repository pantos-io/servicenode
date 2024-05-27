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


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_create_transfer_hub_existent_correct(
        mocked_session, db_initialized_session, embedded_db_session_maker, bid,
        source_blockchain_id, destination_blockchain_id,
        transfer_sender_address, transfer_recipient_address,
        source_token_address, destination_token_address, transfer_amount,
        bid_fee, transfer_sender_nonce, transfer_signature, hub_address,
        forwarder_address):
    mocked_session.return_value = embedded_db_session_maker
    db_initialized_session.add(bid)
    db_initialized_session.commit()
    transfer_id = create_transfer(Blockchain(source_blockchain_id),
                                  Blockchain(destination_blockchain_id),
                                  transfer_sender_address,
                                  transfer_recipient_address,
                                  source_token_address,
                                  destination_token_address, transfer_amount,
                                  bid_fee, transfer_sender_nonce,
                                  transfer_signature, hub_address,
                                  forwarder_address)
    transfer = db_initialized_session.execute(
        sqlalchemy.select(Transfer)).one_or_none()[0]
    assert transfer.id == transfer_id
    _check_transfer(transfer, source_blockchain_id, destination_blockchain_id,
                    transfer_sender_address, transfer_recipient_address,
                    source_token_address, destination_token_address,
                    transfer_amount, transfer_sender_nonce, transfer_signature,
                    hub_address, forwarder_address, bid.execution_time,
                    bid.valid_until, bid.fee)


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_create_transfer_source_token_hub_existent_correct(
        mocked_session, db_initialized_session, embedded_db_session_maker, bid,
        source_token_contract, source_blockchain_id, destination_blockchain_id,
        transfer_sender_address, transfer_recipient_address,
        source_token_address, destination_token_address, transfer_amount,
        bid_fee, transfer_sender_nonce, transfer_signature, hub_address,
        forwarder_address):
    mocked_session.return_value = embedded_db_session_maker
    db_initialized_session.add(bid)
    db_initialized_session.add(source_token_contract)
    db_initialized_session.commit()
    transfer_id = create_transfer(Blockchain(source_blockchain_id),
                                  Blockchain(destination_blockchain_id),
                                  transfer_sender_address,
                                  transfer_recipient_address,
                                  source_token_address,
                                  destination_token_address, transfer_amount,
                                  bid_fee, transfer_sender_nonce,
                                  transfer_signature, hub_address,
                                  forwarder_address)
    transfer = db_initialized_session.execute(
        sqlalchemy.select(Transfer)).one_or_none()[0]
    assert transfer.id == transfer_id
    assert transfer.source_token_contract_id == source_token_contract.id
    _check_transfer(transfer, source_blockchain_id, destination_blockchain_id,
                    transfer_sender_address, transfer_recipient_address,
                    source_token_address, destination_token_address,
                    transfer_amount, transfer_sender_nonce, transfer_signature,
                    hub_address, forwarder_address, bid.execution_time,
                    bid.valid_until, bid.fee)


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_create_transfer_destination_token_hub_existent_correct(
        mocked_session, db_initialized_session, embedded_db_session_maker, bid,
        destination_token_contract, source_blockchain_id,
        destination_blockchain_id, transfer_sender_address,
        transfer_recipient_address, source_token_address,
        destination_token_address, transfer_amount, bid_fee,
        transfer_sender_nonce, transfer_signature, hub_address,
        forwarder_address):
    mocked_session.return_value = embedded_db_session_maker
    db_initialized_session.add(bid)
    db_initialized_session.add(destination_token_contract)
    db_initialized_session.commit()
    transfer_id = create_transfer(Blockchain(source_blockchain_id),
                                  Blockchain(destination_blockchain_id),
                                  transfer_sender_address,
                                  transfer_recipient_address,
                                  source_token_address,
                                  destination_token_address, transfer_amount,
                                  bid_fee, transfer_sender_nonce,
                                  transfer_signature, hub_address,
                                  forwarder_address)
    transfer = db_initialized_session.execute(
        sqlalchemy.select(Transfer)).one_or_none()[0]
    assert transfer.id == transfer_id
    assert (transfer.destination_token_contract_id ==
            destination_token_contract.id)
    _check_transfer(transfer, source_blockchain_id, destination_blockchain_id,
                    transfer_sender_address, transfer_recipient_address,
                    source_token_address, destination_token_address,
                    transfer_amount, transfer_sender_nonce, transfer_signature,
                    hub_address, forwarder_address, bid.execution_time,
                    bid.valid_until, bid.fee)


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_create_transfer_tokens_hub_existent_correct(
        mocked_session, db_initialized_session, embedded_db_session_maker, bid,
        source_token_contract, destination_token_contract,
        source_blockchain_id, destination_blockchain_id,
        transfer_sender_address, transfer_recipient_address,
        source_token_address, destination_token_address, transfer_amount,
        bid_fee, transfer_sender_nonce, transfer_signature, hub_address,
        forwarder_address):
    mocked_session.return_value = embedded_db_session_maker
    db_initialized_session.add(bid)
    db_initialized_session.add(source_token_contract)
    db_initialized_session.add(destination_token_contract)
    db_initialized_session.commit()
    transfer_id = create_transfer(Blockchain(source_blockchain_id),
                                  Blockchain(destination_blockchain_id),
                                  transfer_sender_address,
                                  transfer_recipient_address,
                                  source_token_address,
                                  destination_token_address, transfer_amount,
                                  bid_fee, transfer_sender_nonce,
                                  transfer_signature, hub_address,
                                  forwarder_address)
    transfer = db_initialized_session.execute(
        sqlalchemy.select(Transfer)).one_or_none()[0]
    assert transfer.id == transfer_id
    assert transfer.source_token_contract_id == source_token_contract.id
    assert (transfer.destination_token_contract_id ==
            destination_token_contract.id)
    _check_transfer(transfer, source_blockchain_id, destination_blockchain_id,
                    transfer_sender_address, transfer_recipient_address,
                    source_token_address, destination_token_address,
                    transfer_amount, transfer_sender_nonce, transfer_signature,
                    hub_address, forwarder_address, bid.execution_time,
                    bid.valid_until, bid.fee)


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_create_transfer_hub_forwarder_existent_correct(
        mocked_session, db_initialized_session, embedded_db_session_maker, bid,
        forwarder_contract, source_blockchain_id, destination_blockchain_id,
        transfer_sender_address, transfer_recipient_address,
        source_token_address, destination_token_address, transfer_amount,
        bid_fee, transfer_sender_nonce, transfer_signature, hub_address,
        forwarder_address):
    mocked_session.return_value = embedded_db_session_maker
    db_initialized_session.add(bid)
    db_initialized_session.add(forwarder_contract)
    db_initialized_session.commit()
    transfer_id = create_transfer(Blockchain(source_blockchain_id),
                                  Blockchain(destination_blockchain_id),
                                  transfer_sender_address,
                                  transfer_recipient_address,
                                  source_token_address,
                                  destination_token_address, transfer_amount,
                                  bid_fee, transfer_sender_nonce,
                                  transfer_signature, hub_address,
                                  forwarder_address)
    transfer = db_initialized_session.execute(
        sqlalchemy.select(Transfer)).one_or_none()[0]
    assert transfer.id == transfer_id
    assert transfer.forwarder_contract_id == forwarder_contract.id
    _check_transfer(transfer, source_blockchain_id, destination_blockchain_id,
                    transfer_sender_address, transfer_recipient_address,
                    source_token_address, destination_token_address,
                    transfer_amount, transfer_sender_nonce, transfer_signature,
                    hub_address, forwarder_address, bid.execution_time,
                    bid.valid_until, bid.fee)


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_create_transfer_source_token_hub_forwarder_existent_correct(
        mocked_session, db_initialized_session, embedded_db_session_maker, bid,
        source_token_contract, forwarder_contract, source_blockchain_id,
        destination_blockchain_id, transfer_sender_address,
        transfer_recipient_address, source_token_address,
        destination_token_address, transfer_amount, bid_fee,
        transfer_sender_nonce, transfer_signature, hub_address,
        forwarder_address):
    mocked_session.return_value = embedded_db_session_maker
    db_initialized_session.add(bid)
    db_initialized_session.add(source_token_contract)
    db_initialized_session.add(forwarder_contract)
    db_initialized_session.commit()
    transfer_id = create_transfer(Blockchain(source_blockchain_id),
                                  Blockchain(destination_blockchain_id),
                                  transfer_sender_address,
                                  transfer_recipient_address,
                                  source_token_address,
                                  destination_token_address, transfer_amount,
                                  bid_fee, transfer_sender_nonce,
                                  transfer_signature, hub_address,
                                  forwarder_address)
    transfer = db_initialized_session.execute(
        sqlalchemy.select(Transfer)).one_or_none()[0]
    assert transfer.id == transfer_id
    assert transfer.source_token_contract_id == source_token_contract.id
    assert transfer.forwarder_contract_id == forwarder_contract.id
    _check_transfer(transfer, source_blockchain_id, destination_blockchain_id,
                    transfer_sender_address, transfer_recipient_address,
                    source_token_address, destination_token_address,
                    transfer_amount, transfer_sender_nonce, transfer_signature,
                    hub_address, forwarder_address, bid.execution_time,
                    bid.valid_until, bid.fee)


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_create_transfer_destination_token_hub_forwarder_existent_correct(
        mocked_session, db_initialized_session, embedded_db_session_maker, bid,
        destination_token_contract, forwarder_contract, source_blockchain_id,
        destination_blockchain_id, transfer_sender_address,
        transfer_recipient_address, source_token_address,
        destination_token_address, transfer_amount, bid_fee,
        transfer_sender_nonce, transfer_signature, hub_address,
        forwarder_address):
    mocked_session.return_value = embedded_db_session_maker
    db_initialized_session.add(bid)
    db_initialized_session.add(destination_token_contract)
    db_initialized_session.add(forwarder_contract)
    db_initialized_session.commit()
    transfer_id = create_transfer(Blockchain(source_blockchain_id),
                                  Blockchain(destination_blockchain_id),
                                  transfer_sender_address,
                                  transfer_recipient_address,
                                  source_token_address,
                                  destination_token_address, transfer_amount,
                                  bid_fee, transfer_sender_nonce,
                                  transfer_signature, hub_address,
                                  forwarder_address)
    transfer = db_initialized_session.execute(
        sqlalchemy.select(Transfer)).one_or_none()[0]
    assert transfer.id == transfer_id
    assert (transfer.destination_token_contract_id ==
            destination_token_contract.id)
    assert transfer.forwarder_contract_id == forwarder_contract.id
    _check_transfer(transfer, source_blockchain_id, destination_blockchain_id,
                    transfer_sender_address, transfer_recipient_address,
                    source_token_address, destination_token_address,
                    transfer_amount, transfer_sender_nonce, transfer_signature,
                    hub_address, forwarder_address, bid.execution_time,
                    bid.valid_until, bid.fee)


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_create_transfer_tokens_hub_forwarder_existent_correct(
        mocked_session, db_initialized_session, embedded_db_session_maker, bid,
        source_token_contract, destination_token_contract, forwarder_contract,
        source_blockchain_id, destination_blockchain_id,
        transfer_sender_address, transfer_recipient_address,
        source_token_address, destination_token_address, transfer_amount,
        bid_fee, transfer_sender_nonce, transfer_signature, hub_address,
        forwarder_address):
    mocked_session.return_value = embedded_db_session_maker
    db_initialized_session.add(bid)
    db_initialized_session.add(source_token_contract)
    db_initialized_session.add(destination_token_contract)
    db_initialized_session.add(forwarder_contract)
    db_initialized_session.commit()
    transfer_id = create_transfer(Blockchain(source_blockchain_id),
                                  Blockchain(destination_blockchain_id),
                                  transfer_sender_address,
                                  transfer_recipient_address,
                                  source_token_address,
                                  destination_token_address, transfer_amount,
                                  bid_fee, transfer_sender_nonce,
                                  transfer_signature, hub_address,
                                  forwarder_address)
    transfer = db_initialized_session.execute(
        sqlalchemy.select(Transfer)).one_or_none()[0]
    assert transfer.id == transfer_id
    assert transfer.source_token_contract_id == source_token_contract.id
    assert (transfer.destination_token_contract_id ==
            destination_token_contract.id)
    assert transfer.forwarder_contract_id == forwarder_contract.id
    _check_transfer(transfer, source_blockchain_id, destination_blockchain_id,
                    transfer_sender_address, transfer_recipient_address,
                    source_token_address, destination_token_address,
                    transfer_amount, transfer_sender_nonce, transfer_signature,
                    hub_address, forwarder_address, bid.execution_time,
                    bid.valid_until, bid.fee)


@unittest.mock.patch('pantos.servicenode.database.access._read_token_contract')
@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_create_transfer_sender_nonce_not_unique_error(
        mocked_session, mocked_read_token_contract, embedded_db_session_maker,
        source_blockchain_id, destination_blockchain_id,
        transfer_sender_address, transfer_recipient_address,
        source_token_address, destination_token_address, transfer_amount,
        bid_fee, transfer_sender_nonce, transfer_signature, hub_address,
        forwarder_address):
    mocked_session.return_value = embedded_db_session_maker
    mocked_read_token_contract.side_effect = sqlalchemy.exc.IntegrityError(
        UNIQUE_SENDER_NONCE_CONSTRAINT, '', '')
    with pytest.raises(SenderNonceNotUniqueError):
        create_transfer(Blockchain(source_blockchain_id),
                        Blockchain(destination_blockchain_id),
                        transfer_sender_address, transfer_recipient_address,
                        source_token_address, destination_token_address,
                        transfer_amount, bid_fee, transfer_sender_nonce,
                        transfer_signature, hub_address, forwarder_address)


@unittest.mock.patch('pantos.servicenode.database.access._read_token_contract')
@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_create_transfer_integrity_error(
        mocked_session, mocked_read_token_contract, embedded_db_session_maker,
        source_blockchain_id, destination_blockchain_id,
        transfer_sender_address, transfer_recipient_address,
        source_token_address, destination_token_address, transfer_amount,
        bid_fee, transfer_sender_nonce, transfer_signature, hub_address,
        forwarder_address):
    mocked_session.return_value = embedded_db_session_maker
    mocked_read_token_contract.side_effect = sqlalchemy.exc.IntegrityError(
        '', '', '')
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        create_transfer(Blockchain(source_blockchain_id),
                        Blockchain(destination_blockchain_id),
                        transfer_sender_address, transfer_recipient_address,
                        source_token_address, destination_token_address,
                        transfer_amount, bid_fee, transfer_sender_nonce,
                        transfer_signature, hub_address, forwarder_address)


@unittest.mock.patch('pantos.servicenode.database.access._read_token_contract')
@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_create_transfer_error(
        mocked_session, mocked_read_token_contract, embedded_db_session_maker,
        source_blockchain_id, destination_blockchain_id,
        transfer_sender_address, transfer_recipient_address,
        source_token_address, destination_token_address, transfer_amount,
        bid_fee, transfer_sender_nonce, transfer_signature, hub_address,
        forwarder_address):
    mocked_session.return_value = embedded_db_session_maker
    mocked_read_token_contract.side_effect = Exception()
    with pytest.raises(Exception):
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
