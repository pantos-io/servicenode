import unittest.mock
import uuid

import pytest

from pantos.servicenode.database.access import update_transfer_task_id
from pantos.servicenode.database.exceptions import DatabaseError


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_update_transfer_task_id_correct(mocked_session,
                                         db_initialized_session,
                                         embedded_db_session_maker, uuid_,
                                         transfer, on_chain_transfer_id):
    new_task_id = uuid.UUID(uuid_)
    mocked_session.return_value = embedded_db_session_maker
    db_initialized_session.add(transfer)
    db_initialized_session.commit()

    update_transfer_task_id(transfer.id, new_task_id)

    db_initialized_session.refresh(transfer)
    assert transfer.task_id == str(new_task_id)


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_update_transfer_task_id_unknown_database_error(
        mocked_session, embedded_db_session_maker, uuid_, transfer,
        on_chain_transfer_id):
    new_task_id = uuid.UUID(uuid_)
    mocked_session.return_value = embedded_db_session_maker

    with pytest.raises(DatabaseError):
        update_transfer_task_id(transfer.id, new_task_id)
