import unittest.mock
import uuid

from pantos.servicenode.database.access import read_transfer_by_task_id


@unittest.mock.patch('pantos.servicenode.database.access.get_session')
def test_read_transfer_by_task_id_correct(mocked_session,
                                          db_initialized_session,
                                          embedded_db_session_maker, transfer):
    mocked_session.side_effect = embedded_db_session_maker
    db_initialized_session.add(transfer)
    db_initialized_session.commit()
    task_id_uuid = uuid.UUID(transfer.task_id)
    result_attributes = {}
    transfer_attributes = {}

    result = read_transfer_by_task_id(task_id_uuid)

    for column in result.__table__.columns:
        result_attributes[column.name] = str(getattr(result, column.name))
        transfer_attributes[column.name] = str(getattr(transfer, column.name))
    assert result.__table__ == transfer.__table__
    assert result_attributes == transfer_attributes


@unittest.mock.patch('pantos.servicenode.database.access.get_session')
def test_read_transfer_by_task_id_not_found(mocked_session,
                                            embedded_db_session_maker):
    mocked_session.side_effect = embedded_db_session_maker
    task_id = uuid.uuid4()

    result = read_transfer_by_task_id(task_id)

    assert result is None
