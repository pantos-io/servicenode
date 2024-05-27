import unittest.mock

import pytest
import sqlalchemy
import sqlalchemy.exc
from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.database.access import read_transfer_nonce
from pantos.servicenode.database.enums import TransferStatus
from pantos.servicenode.database.models import Transfer
from tests.database.conftest import populate_transfer_database


@pytest.mark.parametrize(
    ("statuses", "blockchain_ids", "nonces"),
    [([TransferStatus.CONFIRMED, TransferStatus.CONFIRMED
       ], [Blockchain.ETHEREUM, Blockchain.ETHEREUM], [0, 1])])
@unittest.mock.patch('pantos.servicenode.database.access.get_session')
def test_read_nonce_with_success_nonces_equal_nonce_received(
        mocked_get_session, db_initialized_session, statuses, blockchain_ids,
        nonces):
    mocked_get_session.return_value = db_initialized_session
    populate_transfer_database(db_initialized_session, blockchain_ids,
                               statuses, nonces)
    transfer = db_initialized_session.execute(
        sqlalchemy.select(Transfer).filter(
            Transfer.nonce == 0)).fetchall()[0][0]

    assert (transfer.nonce == read_transfer_nonce(transfer.id))
