"""Shared fixtures for all pantos.servicenode.business package tests.

"""
import time
import uuid

import pytest

from pantos.common.blockchains.enums import Blockchain
from pantos.common.entities import ServiceNodeBid
from pantos.servicenode.business.transfers import TransferInteractor
from pantos.servicenode.database.enums import TransferStatus

_SOURCE_BLOCKCHAIN = Blockchain.ETHEREUM

_DESTINATION_BLOCKCHAIN = Blockchain.BNB_CHAIN

_SENDER_ADDRESS = 'sender_address'

_RECIPIENT_ADDRESS = 'recipient_address'

_SOURCE_TOKEN_ADDRESS = 'source_token_address'

_DESTINATION_TOKEN_ADDRESS = 'destination_token_address'

_AMOUNT = 10**10

_FEE = 1337

_BID_ID = 11

_BID_VALID_UNTIL = time.time() * 2

_BID_EXECUTION_TIME = 100000

_BID_SIGNATURE = 'some_signature'

_NONCE = 321

_VALID_UNTIL = 543

_SIGNATURE = 'some_signature'

_TIME_RECEIVED = 123.5

_TRANSFER_INTERNAL_ID = 3

_TRANSFER_STATUS = TransferStatus.ACCEPTED

_TRANSFER_ON_CHAIN_ID = 7

_TRANSACTION_ID = 'some_tx_id'

_UUID = '5cff3b4a-afdf-4140-a3ee-3a809dc62811'

_CONFIRM_TRANSFER_RETRY_INTERVAL = 10

_CONFIRM_TRANSFER_RETRY_INTERVAL_AFTER_ERROR = 12

_EXECUTE_TRANSFER_RETRY_INTERVAL_AFTER_ERROR = 1


@pytest.fixture(scope='module')
def source_blockchain():
    return _SOURCE_BLOCKCHAIN


@pytest.fixture(scope='module')
def destination_blockchain():
    return _DESTINATION_BLOCKCHAIN


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
    return _DESTINATION_TOKEN_ADDRESS


@pytest.fixture(scope='module')
def amount():
    return _AMOUNT


@pytest.fixture(scope='module')
def fee():
    return _FEE


@pytest.fixture(scope='module')
def bid_id():
    return _BID_ID


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
def internal_transaction_id():
    return uuid.uuid4()


@pytest.fixture(scope='module')
def transfer_internal_id():
    return _TRANSFER_INTERNAL_ID


@pytest.fixture(scope='module')
def transfer_status():
    return _TRANSFER_STATUS


@pytest.fixture(scope='module')
def transfer_on_chain_id():
    return _TRANSFER_ON_CHAIN_ID


@pytest.fixture(scope='module')
def transaction_id():
    return _TRANSACTION_ID


@pytest.fixture(scope='module')
def uuid_():
    return _UUID


@pytest.fixture(scope='module')
def confirm_retry_interval():
    return _CONFIRM_TRANSFER_RETRY_INTERVAL


@pytest.fixture(scope='module')
def confirm_retry_interval_after_err():
    return _CONFIRM_TRANSFER_RETRY_INTERVAL_AFTER_ERROR


@pytest.fixture(scope='module')
def execute_retry_interval():
    return _EXECUTE_TRANSFER_RETRY_INTERVAL_AFTER_ERROR


@pytest.fixture(scope='module')
def bid_valid_until():
    return int(_BID_VALID_UNTIL)


@pytest.fixture(scope='module')
def bid_execution_time():
    return _BID_EXECUTION_TIME


@pytest.fixture(scope='module')
def bid_signature():
    return _BID_SIGNATURE


@pytest.fixture(scope='module')
def bid():
    return ServiceNodeBid(_SOURCE_BLOCKCHAIN,
                          _DESTINATION_BLOCKCHAIN, _FEE, _BID_EXECUTION_TIME,
                          int(_BID_VALID_UNTIL), _BID_SIGNATURE)


@pytest.fixture(scope='function')
def initiate_transfer_request(source_blockchain, destination_blockchain,
                              sender_address, recipient_address,
                              source_token_address, destination_token_address,
                              amount, nonce, valid_until, signature,
                              time_received, service_node_bid):
    return TransferInteractor.InitiateTransferRequest(
        source_blockchain, destination_blockchain, sender_address,
        recipient_address, source_token_address, destination_token_address,
        amount, nonce, valid_until, signature, time_received, service_node_bid)


@pytest.fixture(scope='function')
def service_node_bid(source_blockchain, destination_blockchain,
                     bid_execution_time, bid_valid_until, fee, bid_signature):
    return ServiceNodeBid(source_blockchain, destination_blockchain, fee,
                          bid_execution_time, bid_valid_until, bid_signature)


@pytest.fixture(scope='function')
def execute_transfer_request(transfer_internal_id, source_blockchain,
                             destination_blockchain, sender_address,
                             recipient_address, source_token_address,
                             destination_token_address, amount, nonce, fee,
                             valid_until, signature):
    return TransferInteractor.ExecuteTransferRequest(
        transfer_internal_id, source_blockchain, destination_blockchain,
        sender_address, recipient_address, source_token_address,
        destination_token_address, amount, fee, nonce, valid_until, signature)


@pytest.fixture(scope='function')
def confirm_transfer_request(transfer_internal_id, source_blockchain,
                             destination_blockchain, internal_transaction_id):
    return TransferInteractor.ConfirmTransferRequest(transfer_internal_id,
                                                     source_blockchain,
                                                     destination_blockchain,
                                                     internal_transaction_id)
