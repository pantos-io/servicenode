import pytest
from pantos.common.entities import ServiceNodeTransferStatus

from pantos.servicenode.database.enums import TransferStatus


@pytest.mark.parametrize(
    'transfer_status_value',
    [transfer_status.value for transfer_status in ServiceNodeTransferStatus])
def test_transfer_status_to_public_status_public(transfer_status_value):
    transfer_status = TransferStatus(transfer_status_value)
    assert transfer_status.to_public_status() is transfer_status


@pytest.mark.parametrize(
    'non_public_transfer_status, public_transfer_status',
    [(TransferStatus.ACCEPTED_NEW_NONCE_ASSIGNED, TransferStatus.ACCEPTED)])
def test_transfer_status_to_public_status_non_public(
        non_public_transfer_status, public_transfer_status):
    assert (non_public_transfer_status.to_public_status()
            is public_transfer_status)
