import time

import pytest

from pantos.common.blockchains.enums import Blockchain
from pantos.common.entities import ServiceNodeBid
from pantos.servicenode.business.transfers import TransferInteractor
from pantos.servicenode.database.enums import TransferStatus
from pantos.servicenode.restapi import flask_app

_SOURCE_BLOCKCHAIN = Blockchain.ETHEREUM

_DESTIONATION_BLOCKCHAIN = Blockchain.BNB_CHAIN

_SENDER_ADDRESS = '0x0000000000000000000000000000000000000000'

_RECIPIENT_ADDRESS = '0x0000000000000000000000000000000000000001'

_SOURCE_TOKEN_ADDRESS = '0x0000000000000000000000000000000000000002'

_DESTINATION_TOKEN_ADDR = '0x0000000000000000000000000000000000000003'

_AMOUNT = 5

_BID_ID = 7

_BID_EXECUTION_TIME = 100000

_BID_SIGNATURE = 'bid_signature'

_FEE = 500000

_NONCE = 22222

_VALID_UNTIL = _BID_EXECUTION_TIME * 2

_SIGNATURE = '0xb83380f6e1d09411ebf49afd1a95c738686bfb2b0fe2391134f46d7'

_TIME_RECEIVED = 100

_INVALID_BLOCKCHAIN_ID = -1

_INACTIVE_BLOCKCHAIN_ID = 0

_UUID = 'eb25af90-b3a0-4680-9d7e-e6f086f48ace'

_STATUS = TransferStatus.CONFIRMED

_TRANSFER_ID = 0

_TRANSACTION_ID = 'some_tx_id'

_BIDS = [{
    'fee': 0,
    'execution_time': 0,
    'valid_until': 0,
    'signature': 0
}, {
    'fee': 1,
    'execution_time': 1,
    'valid_until': 1,
    'signature': 1
}]

_BID_VALID_UNTIL = time.time() * 2


@pytest.fixture()
def test_client():
    """Flask test client, used for calling REST endpoints.

    """
    with flask_app.test_client() as test_client:
        return test_client


@pytest.fixture(scope='module')
def source_blockchain():
    return _SOURCE_BLOCKCHAIN


@pytest.fixture(scope='module')
def destination_blockchain():
    return _DESTIONATION_BLOCKCHAIN


@pytest.fixture(scope='module')
def sender_address():
    return _SENDER_ADDRESS


@pytest.fixture(scope='module')
def recipient_address():
    return _RECIPIENT_ADDRESS


@pytest.fixture(scope='module')
def source_token_address():
    return _SOURCE_TOKEN_ADDRESS


@pytest.fixture(scope='module')
def destination_token_address():
    return _DESTINATION_TOKEN_ADDR


@pytest.fixture(scope='module')
def amount():
    return _AMOUNT


@pytest.fixture(scope='module')
def bid_id():
    return _BID_ID


@pytest.fixture(scope='module')
def bid_execution_time():
    return _BID_EXECUTION_TIME


@pytest.fixture(scope='module')
def fee():
    return _FEE


@pytest.fixture(scope='module')
def nonce():
    return _NONCE


@pytest.fixture(scope='module')
def valid_until():
    return _VALID_UNTIL


@pytest.fixture(scope='module')
def signature():
    return _SIGNATURE


@pytest.fixture(scope='module')
def time_received():
    return _TIME_RECEIVED


@pytest.fixture(scope='module')
def invalid_blockchain_id():
    return _INVALID_BLOCKCHAIN_ID


@pytest.fixture(scope='module')
def inactive_blockchain_id():
    return _INACTIVE_BLOCKCHAIN_ID


@pytest.fixture(scope='module')
def uuid_():
    return _UUID


@pytest.fixture(scope='module')
def status():
    return _STATUS


@pytest.fixture(scope='module')
def transfer_id():
    return _TRANSFER_ID


@pytest.fixture(scope='module')
def transaction_id():
    return _TRANSACTION_ID


@pytest.fixture(scope='module')
def bids():
    return _BIDS


@pytest.fixture(scope='module')
def bid_valid_until():
    return int(_BID_VALID_UNTIL)


@pytest.fixture(scope='module')
def bid_signature():
    return _BID_SIGNATURE


@pytest.fixture(scope='module')
def service_node_bid(source_blockchain, destination_blockchain, fee,
                     bid_execution_time, bid_valid_until, bid_signature):
    return ServiceNodeBid(source_blockchain, destination_blockchain, fee,
                          bid_execution_time, bid_valid_until, bid_signature)


@pytest.fixture(scope='module')
def transfer_request(source_blockchain, destination_blockchain, sender_address,
                     recipient_address, source_token_address,
                     destination_token_address, amount, bid_valid_until, fee,
                     nonce, valid_until, signature, time_received,
                     bid_execution_time, bid_signature):
    return {
        'source_blockchain_id': source_blockchain.value,
        'destination_blockchain_id': destination_blockchain.value,
        'sender_address': sender_address,
        'recipient_address': recipient_address,
        'source_token_address': source_token_address,
        'destination_token_address': destination_token_address,
        'amount': amount,
        'nonce': nonce,
        'valid_until': valid_until,
        'signature': signature,
        'bid': {
            'execution_time': bid_execution_time,
            'fee': fee,
            'valid_until': bid_valid_until,
            'signature': bid_signature,
        },
        'time_received': time_received
    }


@pytest.fixture(scope='module')
def initiate_transfer_request(source_blockchain, destination_blockchain,
                              sender_address, recipient_address,
                              source_token_address, destination_token_address,
                              amount, nonce, valid_until, signature,
                              time_received, service_node_bid):
    return TransferInteractor.InitiateTransferRequest(
        source_blockchain, destination_blockchain, sender_address,
        recipient_address, source_token_address, destination_token_address,
        amount, nonce, valid_until, signature, time_received, service_node_bid)


@pytest.fixture(scope='module')
def find_transfer_response(source_blockchain, destination_blockchain,
                           sender_address, recipient_address,
                           source_token_address, destination_token_address,
                           amount, fee, status, transfer_id, transaction_id):
    return TransferInteractor.FindTransferResponse(
        source_blockchain, destination_blockchain, sender_address,
        recipient_address, source_token_address, destination_token_address,
        amount, fee, status, transfer_id, transaction_id)
