import unittest.mock

import sqlalchemy
import sqlalchemy.exc

from pantos.common.blockchains.enums import Blockchain
from pantos.servicenode.database.access import create_bid
from pantos.servicenode.database.access import replace_bids
from pantos.servicenode.database.models import Bid

_SOURCE_BLOCKCHAIN_ID = 0

_DESTINATION_BLOCKCHAIN_ID = 1

_ANOTHER_DESTINATION_BLOCKCHAIN_ID = 3

_EXECUTION_TIME = 600

_FEE = 10**8

_DOUBLE_FEE = _FEE * 2

_TRIPLE_FEE = _FEE * 3

_BID_VALID_UNTIL = 1000

_NEW_BID = [{
    'source_blockchain_id': _SOURCE_BLOCKCHAIN_ID,
    'destination_blockchain_id': _DESTINATION_BLOCKCHAIN_ID,
    'fee': _TRIPLE_FEE,
    'execution_time': _EXECUTION_TIME * 3,
    'valid_until': _BID_VALID_UNTIL * 3
}]


def create_bids():
    create_bid(Blockchain(_SOURCE_BLOCKCHAIN_ID),
               Blockchain(_DESTINATION_BLOCKCHAIN_ID), _EXECUTION_TIME,
               _BID_VALID_UNTIL, _FEE)
    create_bid(Blockchain(_SOURCE_BLOCKCHAIN_ID),
               Blockchain(_DESTINATION_BLOCKCHAIN_ID), _EXECUTION_TIME * 2,
               _BID_VALID_UNTIL, _DOUBLE_FEE)
    create_bid(Blockchain(_SOURCE_BLOCKCHAIN_ID),
               Blockchain(_ANOTHER_DESTINATION_BLOCKCHAIN_ID),
               _EXECUTION_TIME * 2, _BID_VALID_UNTIL, _DOUBLE_FEE)


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_replace_bids_correct(mocked_session, db_initialized_session,
                              embedded_db_session_maker):
    mocked_session.return_value = embedded_db_session_maker
    create_bids()
    bid = db_initialized_session.execute(sqlalchemy.select(Bid)).all()

    assert len(bid) == 3
    assert bid[0][0].fee == _FEE
    assert bid[1][0].fee == _FEE * 2

    replace_bids(Blockchain(_SOURCE_BLOCKCHAIN_ID),
                 Blockchain(_DESTINATION_BLOCKCHAIN_ID), _NEW_BID)

    bid = db_initialized_session.execute(sqlalchemy.select(Bid)).all()
    assert len(bid) == 2
    assert bid[0][0].destination_blockchain_id == \
        _ANOTHER_DESTINATION_BLOCKCHAIN_ID
    assert bid[1][0].destination_blockchain_id == _DESTINATION_BLOCKCHAIN_ID
    assert bid[1][0].fee == _TRIPLE_FEE
