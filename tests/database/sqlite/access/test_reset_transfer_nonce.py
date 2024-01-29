import unittest.mock

from pantos.servicenode.database.access import reset_transfer_nonce

_TRANSFER_NONCE = 17


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_reset_transfer_nonce(mocked_get_session_maker, db_initialized_session,
                              embedded_db_session_maker, transfer):
    mocked_get_session_maker.return_value = embedded_db_session_maker
    transfer.nonce = _TRANSFER_NONCE
    db_initialized_session.add(transfer)
    db_initialized_session.commit()
    db_initialized_session.refresh(transfer)
    assert transfer.nonce == _TRANSFER_NONCE
    reset_transfer_nonce(transfer.id)
    db_initialized_session.refresh(transfer)
    assert transfer.nonce is None
