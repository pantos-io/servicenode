import uuid

import marshmallow
import pytest

from pantos.servicenode.restapi import _TransferStatusSchema


def test_transfer_status_schema_correct(uuid_):
    task_id_uuid = _TransferStatusSchema().load({'task_id': uuid_})

    assert type(task_id_uuid) == uuid.UUID
    assert str(task_id_uuid) == uuid_


def test_transfer_status_schema_not_valid():
    expected_message = {'task_id': ['Not a valid UUID.']}

    with pytest.raises(marshmallow.ValidationError) as exc_info:
        _TransferStatusSchema().load({'task_id': 0})

    assert exc_info.value.messages == expected_message
