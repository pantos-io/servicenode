import unittest.mock

from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.database.access import create_bid
from pantos.servicenode.database.access import read_cross_blockchain_bids

_SOURCE_BLOCKCHAIN_ID = 0

_DESTINATION_BLOCKCHAIN_ID = 1

_EXECUTION_TIME = 600

_FEE = 10**8

_DOUBLE_FEE = 10**8 * 2

_BID_VALID_UNTIL = 1000


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
@unittest.mock.patch('pantos.servicenode.database.access.get_session')
def test_read_cross_blockchain_bids_correct(mocked_session,
                                            mocked_session_maker,
                                            db_initialized_session,
                                            embedded_db_session_maker):
    mocked_session.side_effect = embedded_db_session_maker
    mocked_session_maker.return_value = embedded_db_session_maker
    create_bid(Blockchain(_SOURCE_BLOCKCHAIN_ID),
               Blockchain(_DESTINATION_BLOCKCHAIN_ID), _EXECUTION_TIME,
               _BID_VALID_UNTIL, _FEE)
    create_bid(Blockchain(_SOURCE_BLOCKCHAIN_ID),
               Blockchain(_DESTINATION_BLOCKCHAIN_ID), _EXECUTION_TIME * 2,
               _BID_VALID_UNTIL, _DOUBLE_FEE)

    bids = read_cross_blockchain_bids(_SOURCE_BLOCKCHAIN_ID,
                                      _DESTINATION_BLOCKCHAIN_ID)

    assert bids[0].fee == _FEE
    assert bids[0].destination_blockchain_id == _DESTINATION_BLOCKCHAIN_ID
    assert bids[0].execution_time == _EXECUTION_TIME

    assert bids[1].fee == _DOUBLE_FEE
    assert bids[1].destination_blockchain_id == _DESTINATION_BLOCKCHAIN_ID
    assert bids[1].execution_time == _EXECUTION_TIME * 2


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
@unittest.mock.patch('pantos.servicenode.database.access.get_session')
def test_read_cross_blockchain_bids_non_existent_correct(
        mocked_session, mocked_session_maker, db_initialized_session,
        embedded_db_session_maker):
    mocked_session.side_effect = embedded_db_session_maker
    mocked_session_maker.return_value = embedded_db_session_maker
    create_bid(Blockchain(_SOURCE_BLOCKCHAIN_ID),
               Blockchain(_DESTINATION_BLOCKCHAIN_ID), _EXECUTION_TIME,
               _BID_VALID_UNTIL, _DOUBLE_FEE)

    # the chain ids have been switched
    bids = read_cross_blockchain_bids(_DESTINATION_BLOCKCHAIN_ID,
                                      _SOURCE_BLOCKCHAIN_ID)

    assert len(bids) == 0
