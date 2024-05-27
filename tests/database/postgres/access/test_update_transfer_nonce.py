import unittest.mock

import pytest
import sqlalchemy
import sqlalchemy.exc
from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.database.access import update_transfer_nonce
from pantos.servicenode.database.enums import TransferStatus
from pantos.servicenode.database.models import Transfer
from tests.database.conftest import populate_transfer_database


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_update_nonce_empty_database_correct(mocked_get_session,
                                             postgres_db_session_maker,
                                             postgres_db_initialized_session):
    mocked_get_session.return_value = postgres_db_session_maker
    transfer_ids = populate_transfer_database(postgres_db_initialized_session,
                                              [Blockchain.ETHEREUM],
                                              [TransferStatus.CONFIRMED],
                                              [None])
    transfer = postgres_db_initialized_session.execute(
        sqlalchemy.select(Transfer).filter(
            Transfer.id == transfer_ids[0])).fetchall()[0][0]
    assert transfer.nonce is None

    update_transfer_nonce(transfer.id, Blockchain.ETHEREUM, 0)
    postgres_db_initialized_session.refresh(transfer)

    assert transfer.nonce == 0


@pytest.mark.parametrize(("statuses", "blockchain_ids", "nonces"), [([
    TransferStatus.CONFIRMED, TransferStatus.FAILED, TransferStatus.CONFIRMED,
    TransferStatus.CONFIRMED, TransferStatus.FAILED, TransferStatus.CONFIRMED,
    TransferStatus.FAILED, TransferStatus.FAILED, TransferStatus.FAILED
], [
    Blockchain.ETHEREUM, Blockchain.ETHEREUM, Blockchain.ETHEREUM,
    Blockchain.ETHEREUM, Blockchain.ETHEREUM, Blockchain.ETHEREUM,
    Blockchain.ETHEREUM, Blockchain.BNB_CHAIN, Blockchain.AVALANCHE
], [None, 2, 0, 1, 3, 7, 4, 6, 5])])
@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_update_nonce_with_failed_nonces_created_first(
        mocked_get_session, postgres_db_session_maker,
        postgres_db_initialized_session, statuses, blockchain_ids, nonces):
    mocked_get_session.return_value = postgres_db_session_maker
    transfer_ids = populate_transfer_database(postgres_db_initialized_session,
                                              blockchain_ids, statuses, nonces)
    minimum_failed_nonce_transfer = postgres_db_initialized_session.execute(
        sqlalchemy.select(Transfer).filter(
            Transfer.nonce == 2)).fetchall()[0][0]

    update_transfer_nonce(transfer_ids[0], Blockchain.ETHEREUM, 100)

    postgres_db_initialized_session.refresh(minimum_failed_nonce_transfer)
    transfer = postgres_db_initialized_session.execute(
        sqlalchemy.select(Transfer).filter(
            Transfer.id == transfer_ids[0])).fetchall()[0][0]
    assert minimum_failed_nonce_transfer.nonce is None
    assert transfer.nonce == 2


@pytest.mark.parametrize(("statuses", "blockchain_ids", "nonces"), [([
    TransferStatus.FAILED, TransferStatus.CONFIRMED, TransferStatus.CONFIRMED,
    TransferStatus.FAILED, TransferStatus.ACCEPTED, TransferStatus.FAILED,
    TransferStatus.FAILED, TransferStatus.FAILED, TransferStatus.FAILED
], [
    Blockchain.ETHEREUM, Blockchain.ETHEREUM, Blockchain.ETHEREUM,
    Blockchain.ETHEREUM, Blockchain.ETHEREUM, Blockchain.ETHEREUM,
    Blockchain.ETHEREUM, Blockchain.BNB_CHAIN, Blockchain.AVALANCHE
], [2, 0, 1, 3, None, 7, 4, 6, 5])])
@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_update_nonce_with_failed_nonces_created_in_the_middle(
        mocked_get_session, postgres_db_session_maker,
        postgres_db_initialized_session, statuses, blockchain_ids, nonces):
    mocked_get_session.return_value = postgres_db_session_maker
    transfer_ids = populate_transfer_database(postgres_db_initialized_session,
                                              blockchain_ids, statuses, nonces)
    minimum_failed_nonce_transfer = postgres_db_initialized_session.execute(
        sqlalchemy.select(Transfer).filter(
            Transfer.nonce == 2)).fetchall()[0][0]

    update_transfer_nonce(transfer_ids[4], Blockchain.ETHEREUM, 100)

    postgres_db_initialized_session.refresh(minimum_failed_nonce_transfer)
    transfer = postgres_db_initialized_session.execute(
        sqlalchemy.select(Transfer).filter(
            Transfer.id == transfer_ids[4])).fetchall()[0][0]
    assert minimum_failed_nonce_transfer.nonce is None
    assert transfer.nonce == 2


@pytest.mark.parametrize(("statuses", "blockchain_ids", "nonces"), [([
    TransferStatus.CONFIRMED, TransferStatus.CONFIRMED, TransferStatus.FAILED,
    TransferStatus.FAILED, TransferStatus.ACCEPTED
], [
    Blockchain.ETHEREUM, Blockchain.ETHEREUM, Blockchain.ETHEREUM,
    Blockchain.AVALANCHE, Blockchain.ETHEREUM
], [0, 1, None, None, None])])
@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_update_nonce_failed_transfers_with_empty_nonces(
        mocked_get_session, postgres_db_session_maker,
        postgres_db_initialized_session, statuses, blockchain_ids, nonces):
    mocked_get_session.return_value = postgres_db_session_maker
    transfer_ids = populate_transfer_database(postgres_db_initialized_session,
                                              blockchain_ids, statuses, nonces)

    update_transfer_nonce(transfer_ids[4], Blockchain.ETHEREUM, 2)

    transfer = postgres_db_initialized_session.execute(
        sqlalchemy.select(Transfer).filter(
            Transfer.id == transfer_ids[4])).fetchall()[0][0]
    assert transfer.nonce == 2


@pytest.mark.parametrize(("statuses", "blockchain_ids", "nonces"), [([
    TransferStatus.FAILED, TransferStatus.CONFIRMED, TransferStatus.CONFIRMED,
    TransferStatus.FAILED, TransferStatus.FAILED, TransferStatus.FAILED,
    TransferStatus.FAILED, TransferStatus.FAILED, TransferStatus.ACCEPTED
], [
    Blockchain.ETHEREUM, Blockchain.ETHEREUM, Blockchain.ETHEREUM,
    Blockchain.ETHEREUM, Blockchain.ETHEREUM, Blockchain.ETHEREUM,
    Blockchain.BNB_CHAIN, Blockchain.AVALANCHE, Blockchain.ETHEREUM
], [2, 0, 1, 3, 7, 4, 6, 5, None])])
@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_update_nonce_with_failed_nonces_created_last(
        mocked_get_session, postgres_db_session_maker,
        postgres_db_initialized_session, statuses, blockchain_ids, nonces):
    mocked_get_session.return_value = postgres_db_session_maker
    transfer_ids = populate_transfer_database(postgres_db_initialized_session,
                                              blockchain_ids, statuses, nonces)
    minimum_failed_nonce_transfer = postgres_db_initialized_session.execute(
        sqlalchemy.select(Transfer).filter(
            Transfer.nonce == 2)).fetchall()[0][0]

    update_transfer_nonce(transfer_ids[8], Blockchain.ETHEREUM, 100)

    postgres_db_initialized_session.refresh(minimum_failed_nonce_transfer)
    transfer = postgres_db_initialized_session.execute(
        sqlalchemy.select(Transfer).filter(
            Transfer.id == transfer_ids[8])).fetchall()[0][0]
    assert minimum_failed_nonce_transfer.nonce is None
    assert transfer.nonce == 2


@pytest.mark.parametrize(("statuses", "blockchain_ids", "nonces"), [([
    TransferStatus.CONFIRMED, TransferStatus.CONFIRMED,
    TransferStatus.CONFIRMED, TransferStatus.CONFIRMED,
    TransferStatus.CONFIRMED
], [
    Blockchain.ETHEREUM, Blockchain.ETHEREUM, Blockchain.ETHEREUM,
    Blockchain.AVALANCHE, Blockchain.ETHEREUM
], [0, 1, 2, 3, None])])
@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_update_nonce_with_success_nonces_greater_nonce_received(
        mocked_get_session, postgres_db_session_maker,
        postgres_db_initialized_session, statuses, blockchain_ids, nonces):
    mocked_get_session.return_value = postgres_db_session_maker
    transfer_ids = populate_transfer_database(postgres_db_initialized_session,
                                              blockchain_ids, statuses, nonces)

    update_transfer_nonce(transfer_ids[4], Blockchain.ETHEREUM, 100)

    transfer = postgres_db_initialized_session.execute(
        sqlalchemy.select(Transfer).filter(
            Transfer.id == transfer_ids[4])).fetchall()[0][0]
    assert transfer.nonce == 100


@pytest.mark.parametrize(("statuses", "blockchain_ids", "nonces"), [([
    TransferStatus.CONFIRMED, TransferStatus.ACCEPTED, TransferStatus.ACCEPTED,
    TransferStatus.CONFIRMED, TransferStatus.ACCEPTED
], [
    Blockchain.ETHEREUM, Blockchain.ETHEREUM, Blockchain.ETHEREUM,
    Blockchain.AVALANCHE, Blockchain.ETHEREUM
], [0, 1, 2, 3, None])])
@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_update_nonce_with_success_nonces_smaller_nonce_received(
        mocked_get_session, postgres_db_session_maker,
        postgres_db_initialized_session, statuses, blockchain_ids, nonces):
    mocked_get_session.return_value = postgres_db_session_maker
    transfer_ids = populate_transfer_database(postgres_db_initialized_session,
                                              blockchain_ids, statuses, nonces)

    update_transfer_nonce(transfer_ids[4], Blockchain.ETHEREUM, 1)

    transfer = postgres_db_initialized_session.execute(
        sqlalchemy.select(Transfer).filter(
            Transfer.id == transfer_ids[4])).fetchall()[0][0]
    assert transfer.nonce == 1


@pytest.mark.parametrize(("statuses", "blockchain_ids", "nonces"), [([
    TransferStatus.CONFIRMED, TransferStatus.ACCEPTED, TransferStatus.ACCEPTED,
    TransferStatus.CONFIRMED, TransferStatus.ACCEPTED
], [
    Blockchain.ETHEREUM, Blockchain.ETHEREUM, Blockchain.ETHEREUM,
    Blockchain.AVALANCHE, Blockchain.ETHEREUM
], [0, 1, 2, 3, None])])
@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_update_nonce_with_success_nonces_equal_nonce_received(
        mocked_get_session, postgres_db_session_maker,
        postgres_db_initialized_session, statuses, blockchain_ids, nonces):
    mocked_get_session.return_value = postgres_db_session_maker
    transfer_ids = populate_transfer_database(postgres_db_initialized_session,
                                              blockchain_ids, statuses, nonces)

    update_transfer_nonce(transfer_ids[4], Blockchain.ETHEREUM, 3)

    transfer = postgres_db_initialized_session.execute(
        sqlalchemy.select(Transfer).filter(
            Transfer.id == transfer_ids[4])).fetchall()[0][0]
    assert transfer.nonce == 1
