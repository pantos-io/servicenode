import pytest
from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.database.enums import TransferStatus
from pantos.servicenode.database.models import Bid
from pantos.servicenode.database.models import ForwarderContract
from pantos.servicenode.database.models import HubContract
from pantos.servicenode.database.models import TokenContract
from pantos.servicenode.database.models import Transfer

_BID_EXECUTION_TIME = 1200

_BID_VALID_UNTIL = 1300

_BID_FEE = 10**7

_DESTINATION_BLOCKCHAIN_ID = Blockchain.AVALANCHE.value

_DESTINATION_TOKEN_ADDRESS = 'destination_token_address'

_FORWARDER_ADDRESS = 'forwarder_address'

_HUB_ADDRESS = 'hub_address'

_ON_CHAIN_BID_ID = 11

_ON_CHAIN_TRANSFER_ID = 22

_SOURCE_BLOCKCHAIN_ID = Blockchain.BNB_CHAIN.value

_SOURCE_TOKEN_ADDRESS = 'source_token_address'

_TRANSFER_AMOUNT = 10**10

_TRANSFER_RECIPIENT_ADDRESS = 'recipient_address'

_TRANSFER_SENDER_ADDRESS = 'sender_address'

_TRANSFER_SENDER_NONCE = 983

_TRANSFER_SIGNATURE = 'signature'

_TRANSFER_STATUS_ID = TransferStatus.ACCEPTED.value

_TRANSFER_TASK_ID = '17df868e-b120-4dd2-b551-85a0c78a86d6'

_TRANSFER_TRANSACTION_ID = 'transaction_hash'

_UUID = '64814d84-e4fb-11ed-b5ea-0242ac120002'


@pytest.fixture
def bid(source_blockchain_id, destination_blockchain_id, bid_execution_time,
        bid_valid_until, bid_fee):
    return Bid(source_blockchain_id=source_blockchain_id,
               destination_blockchain_id=destination_blockchain_id,
               execution_time=bid_execution_time, valid_until=bid_valid_until,
               fee=bid_fee)


@pytest.fixture(scope='module')
def bid_execution_time():
    return _BID_EXECUTION_TIME


@pytest.fixture(scope='module')
def bid_valid_until():
    return _BID_VALID_UNTIL


@pytest.fixture(scope='module')
def bid_fee():
    return _BID_FEE


@pytest.fixture(scope='module')
def destination_blockchain_id():
    return _DESTINATION_BLOCKCHAIN_ID


@pytest.fixture(scope='module')
def destination_token_address():
    return _DESTINATION_TOKEN_ADDRESS


@pytest.fixture
def destination_token_contract(destination_blockchain_id,
                               destination_token_address):
    return TokenContract(blockchain_id=destination_blockchain_id,
                         address=destination_token_address)


@pytest.fixture(scope='module')
def forwarder_address():
    return _FORWARDER_ADDRESS


@pytest.fixture
def forwarder_contract(source_blockchain_id, forwarder_address):
    return ForwarderContract(blockchain_id=source_blockchain_id,
                             address=forwarder_address)


@pytest.fixture(scope='module')
def hub_address():
    return _HUB_ADDRESS


@pytest.fixture
def hub_contract(source_blockchain_id, hub_address):
    return HubContract(blockchain_id=source_blockchain_id, address=hub_address)


@pytest.fixture(scope='module')
def on_chain_bid_id():
    return _ON_CHAIN_BID_ID


@pytest.fixture(scope='module')
def on_chain_transfer_id():
    return _ON_CHAIN_TRANSFER_ID


@pytest.fixture(scope='module')
def source_blockchain_id():
    return _SOURCE_BLOCKCHAIN_ID


@pytest.fixture(scope='module')
def source_token_address():
    return _SOURCE_TOKEN_ADDRESS


@pytest.fixture
def source_token_contract(source_blockchain_id, source_token_address):
    return TokenContract(blockchain_id=source_blockchain_id,
                         address=source_token_address)


@pytest.fixture
def transfer(source_blockchain_id, destination_blockchain_id,
             transfer_sender_address, transfer_recipient_address,
             source_token_contract, destination_token_contract,
             transfer_amount, bid_fee, transfer_sender_nonce,
             transfer_signature, hub_contract, forwarder_contract,
             transfer_task_id, on_chain_transfer_id, transfer_status_id,
             transfer_transaction_id):
    return Transfer(
        source_blockchain_id=source_blockchain_id,
        destination_blockchain_id=destination_blockchain_id,
        sender_address=transfer_sender_address,
        recipient_address=transfer_recipient_address,
        source_token_contract=source_token_contract,
        destination_token_contract=destination_token_contract,
        amount=transfer_amount, fee=bid_fee,
        sender_nonce=transfer_sender_nonce, signature=transfer_signature,
        hub_contract=hub_contract, forwarder_contract=forwarder_contract,
        task_id=transfer_task_id, on_chain_transfer_id=on_chain_transfer_id,
        status_id=transfer_status_id, transaction_id=transfer_transaction_id)


@pytest.fixture(scope='module')
def transfer_amount():
    return _TRANSFER_AMOUNT


@pytest.fixture(scope='module')
def transfer_recipient_address():
    return _TRANSFER_RECIPIENT_ADDRESS


@pytest.fixture(scope='module')
def transfer_sender_address():
    return _TRANSFER_SENDER_ADDRESS


@pytest.fixture(scope='module')
def transfer_sender_nonce():
    return _TRANSFER_SENDER_NONCE


@pytest.fixture(scope='module')
def transfer_signature():
    return _TRANSFER_SIGNATURE


@pytest.fixture(scope='module')
def transfer_task_id():
    return _TRANSFER_TASK_ID


@pytest.fixture(scope='module')
def transfer_status_id():
    return _TRANSFER_STATUS_ID


@pytest.fixture(scope='module')
def transfer_transaction_id():
    return _TRANSFER_TRANSACTION_ID


@pytest.fixture(scope='module')
def uuid_():
    return _UUID
