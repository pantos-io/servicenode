import unittest.mock

import pytest

from pantos.servicenode.database.access import update_transfer_status
from pantos.servicenode.database.enums import TransferStatus
from pantos.servicenode.database.exceptions import DatabaseError


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_update_transfer_status_correct(mocked_session, db_initialized_session,
                                        embedded_db_session_maker, transfer):
    mocked_session.return_value = embedded_db_session_maker
    new_transfer_status = TransferStatus.FAILED
    db_initialized_session.add(transfer)
    db_initialized_session.commit()

    update_transfer_status(transfer.id, new_transfer_status)

    db_initialized_session.refresh(transfer)
    assert transfer.status_id == new_transfer_status.value
    assert transfer.sender_nonce is None


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_update_transfer_status_database_error(mocked_session,
                                               embedded_db_session_maker,
                                               transfer):
    new_transfer_status = TransferStatus.FAILED
    mocked_session.return_value = embedded_db_session_maker

    with pytest.raises(DatabaseError):
        update_transfer_status(transfer.id, new_transfer_status)
