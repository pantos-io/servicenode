import unittest.mock

import pytest

from pantos.servicenode.database.access import update_on_chain_transfer_id
from pantos.servicenode.database.exceptions import DatabaseError


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_update_on_chain_transfer_id_correct(mocked_session,
                                             db_initialized_session,
                                             embedded_db_session_maker,
                                             transfer, on_chain_transfer_id):
    new_on_chain_id = on_chain_transfer_id + 1
    mocked_session.return_value = embedded_db_session_maker
    db_initialized_session.add(transfer)
    db_initialized_session.commit()

    update_on_chain_transfer_id(transfer.id, new_on_chain_id)

    db_initialized_session.refresh(transfer)
    assert transfer.on_chain_transfer_id == new_on_chain_id


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_update_on_chain_transfer_id_unknown_database_error(
        mocked_session, embedded_db_session_maker, transfer,
        on_chain_transfer_id):
    new_on_chain_id = on_chain_transfer_id + 1
    mocked_session.return_value = embedded_db_session_maker

    with pytest.raises(DatabaseError):
        update_on_chain_transfer_id(transfer.id, new_on_chain_id)
