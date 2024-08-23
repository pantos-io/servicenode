import unittest.mock

import sqlalchemy
import sqlalchemy.exc
from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.database.access import create_bid
from pantos.servicenode.database.models import Bid

_SOURCE_BLOCKCHAIN_ID = 0

_DESTINATION_BLOCKCHAIN_ID = 1

_EXECUTION_TIME = 600

_FEE = 10**8

_BID_VALID_UNTIL = 1000


@unittest.mock.patch('pantos.servicenode.database.access.get_session_maker')
def test_create_bid_correct(mocked_session, db_initialized_session,
                            embedded_db_session_maker):
    mocked_session.return_value = embedded_db_session_maker
    create_bid(Blockchain(_SOURCE_BLOCKCHAIN_ID),
               Blockchain(_DESTINATION_BLOCKCHAIN_ID), _EXECUTION_TIME,
               _BID_VALID_UNTIL, _FEE)
    bid = db_initialized_session.execute(
        sqlalchemy.select(Bid)).one_or_none()[0]
    _check_bid(bid)


def _check_bid(bid):
    assert bid.source_blockchain_id == _SOURCE_BLOCKCHAIN_ID
    assert bid.destination_blockchain_id == _DESTINATION_BLOCKCHAIN_ID
    assert bid.execution_time == _EXECUTION_TIME
    assert bid.valid_until == _BID_VALID_UNTIL
    assert bid.fee == _FEE
