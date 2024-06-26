import unittest.mock
import uuid

import hexbytes
import pytest
import web3
import web3.datastructures
from eth_account.account import Account
from pantos.common.blockchains.base import NodeConnections
from pantos.common.blockchains.base import TransactionNonceTooLowError
from pantos.common.blockchains.base import TransactionUnderpricedError
from pantos.common.blockchains.enums import Blockchain
from pantos.common.blockchains.enums import ContractAbi
from pantos.common.blockchains.ethereum import EthereumUtilitiesError

from pantos.servicenode.blockchains.base import BlockchainClient
from pantos.servicenode.blockchains.base import InsufficientBalanceError
from pantos.servicenode.blockchains.base import InvalidSignatureError
from pantos.servicenode.blockchains.ethereum import EthereumClient
from pantos.servicenode.blockchains.ethereum import EthereumClientError

_TRANSFER_FROM_TRANSACTION_RECEIPT = web3.datastructures.AttributeDict({
    'blockHash': hexbytes.HexBytes(
        '0x24aa438ba5aa72634a09f77acefb5c8cce1261b44681e72488d4405e311fa9a2'),
    'blockNumber': 18862558,
    'contractAddress': None,
    'cumulativeGasUsed': 697584,
    'effectiveGasPrice': 8000000000,
    'from': '0xaAE34Ec313A97265635B8496468928549cdd4AB7',
    'gasUsed': 129822,
    'logs': [
        web3.datastructures.AttributeDict({
            'address': '0xE1b042d1e27BF7B2bee000a23C59f9eB0aC6Fdce',
            'topics': [
                hexbytes.HexBytes(
                    '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4'
                    'df523b3ef'),
                hexbytes.HexBytes(
                    '0x000000000000000000000000707527eb76bad9099a302b2e33851e9'
                    '587e30ed0'),
                hexbytes.HexBytes(
                    '0x0000000000000000000000000000000000000000000000000000000'
                    '000000000')
            ],
            'data': '0x0000000000000000000000000000000000000000000000000000000'
            '0127a3980',
            'blockNumber': 18862558,
            'transactionHash': hexbytes.HexBytes(
                '0xa34a0d63bac40ae34153483a5c69663c2b32e5e200c2e2460b189aed3f0'
                'a76c9'),
            'transactionIndex': 1,
            'blockHash': hexbytes.HexBytes(
                '0x24aa438ba5aa72634a09f77acefb5c8cce1261b44681e72488d4405e311'
                'fa9a2'),
            'logIndex': 0,
            'removed': False
        }),
        web3.datastructures.AttributeDict({
            'address': '0xE1b042d1e27BF7B2bee000a23C59f9eB0aC6Fdce',
            'topics': [
                hexbytes.HexBytes(
                    '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4'
                    'df523b3ef'),
                hexbytes.HexBytes(
                    '0x000000000000000000000000707527eb76bad9099a302b2e33851e9'
                    '587e30ed0'),
                hexbytes.HexBytes(
                    '0x000000000000000000000000aae34ec313a97265635b84964689285'
                    '49cdd4ab7')
            ],
            'data': '0x0000000000000000000000000000000000000000000000000000000'
            '008f0d180',
            'blockNumber': 18862558,
            'transactionHash': hexbytes.HexBytes(
                '0xa34a0d63bac40ae34153483a5c69663c2b32e5e200c2e2460b189aed3f0'
                'a76c9'),
            'transactionIndex': 1,
            'blockHash': hexbytes.HexBytes(
                '0x24aa438ba5aa72634a09f77acefb5c8cce1261b44681e72488d4405e311'
                'fa9a2'),
            'logIndex': 1,
            'removed': False
        }),
        web3.datastructures.AttributeDict({
            'address': '0x5FE61d63264390b748EF714B461f3BA8965F541D',
            'topics': [
                hexbytes.HexBytes(
                    '0xe2d69d9df6c1e740c72aecc4a0cd85eca27cbc5273ec079de974008'
                    'f492a9f8b')
            ],
            'data': '0x0000000000000000000000000000000000000000000000000000000'
            '00000000000000000000000000000000000000000000000000000000000000000'
            '00000006000000000000000000000000707527eb76bad9099a302b2e33851e958'
            '7e30ed00000000000000000000000000000000000000000000000000000000000'
            '000120000000000000000000000000e1b042d1e27bf7b2bee000a23c59f9eb0ac'
            '6fdce000000000000000000000000000000000000000000000000000000000000'
            '018000000000000000000000000000000000000000000000000000000000127a3'
            '9800000000000000000000000000000000000000000000000000000000008f0d1'
            '80000000000000000000000000aae34ec313a97265635b8496468928549cdd4ab'
            '7000000000000000000000000000000000000000000000000000000000000002a'
            '30786141453334456333313341393732363536333542383439363436383932383'
            '53439636464344142370000000000000000000000000000000000000000000000'
            '0000000000000000000000000000000000000000000000000000000000002a307'
            '84531623034326431653237424637423262656530303061323343353966396542'
            '306143364664636500000000000000000000000000000000000000000000',
            'blockNumber': 18862558,
            'transactionHash': hexbytes.HexBytes(
                '0xa34a0d63bac40ae34153483a5c69663c2b32e5e200c2e2460b189aed3f0'
                'a76c9'),
            'transactionIndex': 1,
            'blockHash': hexbytes.HexBytes(
                '0x24aa438ba5aa72634a09f77acefb5c8cce1261b44681e72488d4405e311'
                'fa9a2'),
            'logIndex': 2,
            'removed': False
        })
    ],
    'logsBloom': hexbytes.HexBytes(
        '0x0000200000000000000000000000000000000000000000000040000020000000000'
        '000000000000000000000000000000000000000000000000020000000000000400040'
        '000000000000000800000000000000000000000000100000000000000000020002000'
        '000000000000000080000000000400000000000081000000000000000000000000000'
        '000000000000000000000000000000000000000000000000008000004000000000000'
        '000000000000000000400020000000000000000000000000200000000000000000000'
        '000000000000000000000000000000002000000000000000000000000000000000000'
        '0000001000000000000000000000000'),
    'status': 1,
    'to': '0x5FE61d63264390b748EF714B461f3BA8965F541D',
    'transactionHash': hexbytes.HexBytes(
        '0xa34a0d63bac40ae34153483a5c69663c2b32e5e200c2e2460b189aed3f0a76c9'),
    'transactionIndex': 1,
    'type': '0x2'
})

_TRANSFER_TRANSACTION_RECEIPT = web3.datastructures.AttributeDict({
    'blockHash': hexbytes.HexBytes(
        '0x3171ae38d5b93610423636162f2e18f00e691616f31876fa90ba818d30e3588d'),
    'blockNumber': 18862990,
    'contractAddress': None,
    'cumulativeGasUsed': 457893,
    'effectiveGasPrice': 8000000000,
    'from': '0xaAE34Ec313A97265635B8496468928549cdd4AB7',
    'gasUsed': 97949,
    'logs': [
        web3.datastructures.AttributeDict({
            'address': '0xE1b042d1e27BF7B2bee000a23C59f9eB0aC6Fdce',
            'topics': [
                hexbytes.HexBytes(
                    '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4'
                    'df523b3ef'),
                hexbytes.HexBytes(
                    '0x000000000000000000000000707527eb76bad9099a302b2e33851e9'
                    '587e30ed0'),
                hexbytes.HexBytes(
                    '0x000000000000000000000000aae34ec313a97265635b84964689285'
                    '49cdd4ab7')
            ],
            'data': '0x0000000000000000000000000000000000000000000000000000000'
            '0127a3980',
            'blockNumber': 18862990,
            'transactionHash': hexbytes.HexBytes(
                '0x5976353de3a0f9914a21cd3b49901bfc4c58630be6ccd87734e015d5015'
                '9eeba'),
            'transactionIndex': 1,
            'blockHash': hexbytes.HexBytes(
                '0x3171ae38d5b93610423636162f2e18f00e691616f31876fa90ba818d30e'
                '3588d'),
            'logIndex': 0,
            'removed': False
        }),
        web3.datastructures.AttributeDict({
            'address': '0xE1b042d1e27BF7B2bee000a23C59f9eB0aC6Fdce',
            'topics': [
                hexbytes.HexBytes(
                    '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4'
                    'df523b3ef'),
                hexbytes.HexBytes(
                    '0x000000000000000000000000707527eb76bad9099a302b2e33851e9'
                    '587e30ed0'),
                hexbytes.HexBytes(
                    '0x000000000000000000000000aae34ec313a97265635b84964689285'
                    '49cdd4ab7')
            ],
            'data': '0x0000000000000000000000000000000000000000000000000000000'
            '002faf080',
            'blockNumber': 18862990,
            'transactionHash': hexbytes.HexBytes(
                '0x5976353de3a0f9914a21cd3b49901bfc4c58630be6ccd87734e015d5015'
                '9eeba'),
            'transactionIndex': 1,
            'blockHash': hexbytes.HexBytes(
                '0x3171ae38d5b93610423636162f2e18f00e691616f31876fa90ba818d30e'
                '3588d'),
            'logIndex': 1,
            'removed': False
        }),
        web3.datastructures.AttributeDict({
            'address': '0x5FE61d63264390b748EF714B461f3BA8965F541D',
            'topics': [
                hexbytes.HexBytes(
                    '0xc554ec28e750cd02386397060a6c443fb4ad8e987c8f874185a60f9'
                    'e08ccbaad')
            ],
            'data': '0x0000000000000000000000000000000000000000000000000000000'
            '000000001000000000000000000000000707527eb76bad9099a302b2e'
            '33851e9587e30ed0000000000000000000000000aae34ec313a972656'
            '35b8496468928549cdd4ab7000000000000000000000000e1b042d1e2'
            '7bf7b2bee000a23c59f9eb0ac6fdce000000000000000000000000000'
            '00000000000000000000000000000127a398000000000000000000000'
            '00000000000000000000000000000000000002faf0800000000000000'
            '00000000000aae34ec313a97265635b8496468928549cdd4ab7',
            'blockNumber': 18862990,
            'transactionHash': hexbytes.HexBytes(
                '0x5976353de3a0f9914a21cd3b49901bfc4c58630be6ccd87734e015d5015'
                '9eeba'),
            'transactionIndex': 1,
            'blockHash': hexbytes.HexBytes(
                '0x3171ae38d5b93610423636162f2e18f00e691616f31876fa90ba818d30e'
                '3588d'),
            'logIndex': 2,
            'removed': False
        })
    ],
    'logsBloom': hexbytes.HexBytes(
        '0x0000200000000000000000000000000000400000000000000000000020000000000'
        '000000000000000000000000000000000000000000000000020000000000000400040'
        '000000000000000800000000000000010000000000100000000000000000000000000'
        '000008000000000000000000000400000000000081000000000000000000000000000'
        '000000000000000000000000000000000000000000000000008000004000000000000'
        '000000000000000000400000000000000000000000000000200000000000000000000'
        '000000000000000000000000000000000000000000000000000000000000000000000'
        '0000001000000000000000000000000'),
    'status': 1,
    'to': '0x5FE61d63264390b748EF714B461f3BA8965F541D',
    'transactionHash': hexbytes.HexBytes(
        '0x5976353de3a0f9914a21cd3b49901bfc4c58630be6ccd87734e015d50159eeba'),
    'transactionIndex': 1,
    'type': '0x2'
})

_INVALID_SIGNATURE_ERROR = 'PantosForwarder: invalid signature'

_INSUFFICIENT_BALANCE_ERROR = 'PantosHub: insufficient balance of sender'

_TRANSACTION_ID = hexbytes.HexBytes(
    '0x53827743938a0344c56afdd1da6005a6182dd0c589db16c81ca99330cbdd6f59')

_PROVIDER_TIMEOUT = 101

_PAN_TOKEN_CONTRACT_ADDRESS = 'pan_token_contract_address'

_HUB_CONTRACT_ADDRESS = 'hub_contract_address'

_KEYSTORE_PATH = '/some/file/path'

_KEYSTORE_PASSWORD = 'some_password'

_PRIVATE_KEY = \
    'cbdff69e91a62f0ff96730ca260049f0a838fd1dfddacb0f979d0b1376b84e54'

_SERVICE_NODE_ADDRESS = '0xbBCBd295CD5B36385F6c8EF7AD49bDf84A78DB97'

_SERVICE_NODE_URL = 'servicenode.pantos.testurl'

_TRANSACTION_HASH = 'transaction_hash'

_DESTINATION_BLOCKCHAIN = Blockchain.BNB_CHAIN

_TRANSFER_INTERNAL_ID = 7

_TRANSFER_SENDER_ADDRESS = 'sender_address'

_TRANSFER_RECIPIENT_ADDRESS = 'recipient_address'

_TRASNFER_TOKEN_ADDRESS = 'transfer_token_address'

_TRANSFER_AMOUNT = 10**10

_TRANSFER_FEE = 11

_TRANSFER_NONCE = 777

_TRANSFER_VALID_UNTIL = 111

_TRANSFER_SIGNATURE = 'signature'

_TRANSFER_DESTIONATION_TOKEN_ADDRESS = 'destination_token'


@pytest.fixture(scope='module')
def web3_account():
    return Account.create('THIS IS A TEST')


@pytest.fixture(scope='module')
def transfer_internal_id():
    return _TRANSFER_INTERNAL_ID


@pytest.fixture(scope='module')
def transfer_sender_address():
    return _TRANSFER_SENDER_ADDRESS


@pytest.fixture(scope='module')
def transfer_recipient_address():
    return _TRANSFER_RECIPIENT_ADDRESS


@pytest.fixture(scope='module')
def transfer_token_address():
    return _TRASNFER_TOKEN_ADDRESS


@pytest.fixture(scope='module')
def transfer_amount():
    return _TRANSFER_AMOUNT


@pytest.fixture(scope='module')
def transfer_fee():
    return _TRANSFER_FEE


@pytest.fixture(scope='module')
def transfer_nonce():
    return _TRANSFER_NONCE


@pytest.fixture(scope='module')
def transfer_valid_until():
    return _TRANSFER_VALID_UNTIL


@pytest.fixture(scope='module')
def transfer_signature():
    return _TRANSFER_SIGNATURE


@pytest.fixture(scope='module')
def transfer_destination_token_address():
    return _TRANSFER_DESTIONATION_TOKEN_ADDRESS


@pytest.fixture(scope='module')
def transfer_submission_start_request(
        transfer_internal_id, transfer_sender_address,
        transfer_recipient_address, transfer_token_address, transfer_amount,
        transfer_fee, transfer_nonce, transfer_valid_until,
        transfer_signature):
    return BlockchainClient.TransferSubmissionStartRequest(
        transfer_internal_id, transfer_sender_address,
        transfer_recipient_address, transfer_token_address, transfer_amount,
        transfer_fee, transfer_nonce, transfer_valid_until, transfer_signature)


@pytest.fixture(scope='module')
def transfer_from_submission_start_request(
        transfer_internal_id, destination_blockchain, transfer_sender_address,
        transfer_recipient_address, transfer_token_address,
        transfer_destination_token_address, transfer_amount, transfer_fee,
        transfer_nonce, transfer_valid_until, transfer_signature):
    return BlockchainClient.TransferFromSubmissionStartRequest(
        transfer_internal_id, destination_blockchain, transfer_sender_address,
        transfer_recipient_address, transfer_token_address,
        transfer_destination_token_address, transfer_amount, transfer_fee,
        transfer_nonce, transfer_valid_until, transfer_signature)


@pytest.fixture(scope='module')
def provider_timeout():
    return _PROVIDER_TIMEOUT


@pytest.fixture(scope='module')
def pan_token_contract_address():
    return _PAN_TOKEN_CONTRACT_ADDRESS


@pytest.fixture(scope='module')
def hub_contract_address():
    return _HUB_CONTRACT_ADDRESS


@pytest.fixture(scope='module')
def service_node_url():
    return _SERVICE_NODE_URL


@pytest.fixture(scope='module')
def service_node_address():
    return _SERVICE_NODE_ADDRESS


@pytest.fixture(scope='module')
def destination_blockchain():
    return _DESTINATION_BLOCKCHAIN


@pytest.fixture(scope='module')
def transaction_hash():
    return _TRANSACTION_HASH


@pytest.fixture(scope='module')
def service_node_record(service_node_url):
    return [True, service_node_url, 0, 0, 0, 0]


@pytest.fixture(scope='module')
def w3():
    return web3.Web3(web3.EthereumTesterProvider())


@pytest.fixture(scope='module')
def node_connections(w3):
    node_connections = NodeConnections[web3.Web3]()
    node_connections.add_node_connection(w3)
    return node_connections


@pytest.fixture
def mock_get_blockchain_config():
    with unittest.mock.patch(
            'pantos.servicenode.blockchains.base.'
            'get_blockchain_config') as mock_get_blockchain_config_:
        yield mock_get_blockchain_config_


@pytest.fixture
def mock_get_blockchain_utilities():
    with unittest.mock.patch(
            'pantos.servicenode.blockchains.base.'
            'get_blockchain_utilities') as mock_get_blockchain_utilities_:
        yield mock_get_blockchain_utilities_


@pytest.fixture
def ethereum_client(mock_get_blockchain_config, mock_get_blockchain_utilities,
                    node_connections, service_node_address):
    mock_get_blockchain_utilities().decrypt_private_key.return_value = \
        _PRIVATE_KEY
    mock_get_blockchain_utilities().get_address.return_value = \
        service_node_address
    with unittest.mock.patch.object(BlockchainClient, '__init__',
                                    lambda self: None):
        with unittest.mock.patch.object(
                EthereumClient, '_EthereumClient__create_node_connections',
                return_value=node_connections):
            mock_get_blockchain_config.return_value = {
                'private_key': _KEYSTORE_PATH,
                'private_key_password': _KEYSTORE_PASSWORD
            }
            yield EthereumClient()


def test_get_blockchain_correct(ethereum_client):
    assert ethereum_client.get_blockchain() is Blockchain.ETHEREUM
    assert EthereumClient.get_blockchain() is Blockchain.ETHEREUM


def test_get_error_class_correct(ethereum_client):
    assert ethereum_client.get_error_class() is EthereumClientError
    assert EthereumClient.get_error_class() is EthereumClientError


def test_is_node_registered_correct(ethereum_client,
                                    mock_get_blockchain_config,
                                    mock_get_blockchain_utilities,
                                    provider_timeout, hub_contract_address,
                                    service_node_record):
    mock_get_blockchain_config.return_value = {
        'provider_timeout': provider_timeout,
        'hub': hub_contract_address
    }
    mock_get_blockchain_utilities().create_contract().functions.\
        getServiceNodeRecord().call().get.return_value = service_node_record

    is_node_registered = ethereum_client.is_node_registered()

    assert is_node_registered is True


def test_is_node_registered_contract_creation_error(
        ethereum_client, mock_get_blockchain_config,
        mock_get_blockchain_utilities, provider_timeout, hub_contract_address):
    mock_get_blockchain_config.return_value = {
        'provider_timeout': provider_timeout,
        'hub': hub_contract_address
    }
    mock_get_blockchain_utilities().create_contract.side_effect = Exception

    with pytest.raises(EthereumClientError):
        ethereum_client.is_node_registered()


def test_is_node_registered_error(ethereum_client, mock_get_blockchain_config):
    mock_get_blockchain_config.side_effect = Exception()

    with pytest.raises(EthereumClientError):
        ethereum_client.is_node_registered()


@unittest.mock.patch.object(EthereumClient, 'is_valid_address',
                            side_effect=web3.Web3.is_checksum_address)
def test_is_valid_recipient_address_checksum_true(mock_is_valid_address,
                                                  ethereum_client):
    recipient_address = "0x308eF9f94a642A31D9F9eA83f183544027A9742D"

    is_recipient_address_correct = ethereum_client.is_valid_recipient_address(
        recipient_address)

    assert is_recipient_address_correct is True


@unittest.mock.patch.object(EthereumClient, 'is_valid_address',
                            side_effect=web3.Web3.is_checksum_address)
def test_is_valid_recipient_address_checksum_false(mock_is_valid_address,
                                                   ethereum_client):
    recipient_address = "0x308ef9f94a642a31d9f9ea83f183544027a9742d"

    is_recipient_address_correct = ethereum_client.is_valid_recipient_address(
        recipient_address)

    assert is_recipient_address_correct is False


@unittest.mock.patch.object(EthereumClient, 'is_valid_address',
                            side_effect=web3.Web3.is_checksum_address)
def test_is_valid_recipient_address_0_address_false(mock_is_valid_address,
                                                    ethereum_client):
    recipient_address = "0x0000000000000000000000000000000000000000"

    is_recipient_address_correct = ethereum_client.is_valid_recipient_address(
        recipient_address)

    assert is_recipient_address_correct is False


def test_read_node_url_correct(ethereum_client, mock_get_blockchain_config,
                               provider_timeout, hub_contract_address,
                               mock_get_blockchain_utilities,
                               service_node_record):
    mock_get_blockchain_config.return_value = {
        'provider_timeout': provider_timeout,
        'hub': hub_contract_address
    }
    mock_get_blockchain_utilities().create_contract().functions.\
        getServiceNodeRecord().call().get.return_value = service_node_record

    service_node_url = ethereum_client.read_node_url()

    assert service_node_url == service_node_record[1]


def test_read_node_url_error(ethereum_client, mock_get_blockchain_config):
    mock_get_blockchain_config.side_effect = Exception()

    with pytest.raises(EthereumClientError):
        ethereum_client.read_node_url()


@pytest.mark.parametrize('node_stake', [0, 1])
@unittest.mock.patch.object(EthereumClient, '_start_transaction_submission',
                            return_value=uuid.uuid4())
def test_register_node_correct(mock_start_transaction_submission, node_stake,
                               ethereum_client, mock_get_blockchain_config,
                               hub_contract_address, service_node_url,
                               service_node_address):
    mock_get_blockchain_config.return_value = {'hub': hub_contract_address}

    ethereum_client.register_node(service_node_url, node_stake,
                                  service_node_address)

    assert mock_start_transaction_submission.call_count == node_stake + 1
    if node_stake > 0:
        approve_request = mock_start_transaction_submission.call_args_list[
            0].args[0]
        assert approve_request.versioned_contract_abi.contract_abi is \
            ContractAbi.PANTOS_TOKEN
        assert approve_request.function_args == (hub_contract_address,
                                                 node_stake)
    register_request = mock_start_transaction_submission.call_args_list[
        node_stake].args[0]
    assert register_request.versioned_contract_abi.contract_abi is \
        ContractAbi.PANTOS_HUB
    assert register_request.function_args == (service_node_address,
                                              service_node_url, node_stake,
                                              service_node_address)


@pytest.mark.parametrize('node_stake', [0, 1])
@unittest.mock.patch.object(EthereumClient, '_start_transaction_submission',
                            side_effect=EthereumUtilitiesError)
def test_register_node_error(mock_start_transaction_submission, node_stake,
                             ethereum_client, mock_get_blockchain_config,
                             hub_contract_address, service_node_url,
                             service_node_address):
    mock_get_blockchain_config.return_value = {'hub': hub_contract_address}

    with pytest.raises(EthereumClientError):
        ethereum_client.register_node(service_node_url, node_stake,
                                      service_node_address)


@unittest.mock.patch.object(EthereumClient, '_start_transaction_submission',
                            return_value=uuid.uuid4())
def test_unregister_node_correct(mock_start_transaction_submission,
                                 ethereum_client, service_node_address):
    ethereum_client.unregister_node()

    mock_start_transaction_submission.assert_called_once()
    unregister_request = mock_start_transaction_submission.call_args.args[0]
    assert unregister_request.versioned_contract_abi.contract_abi is \
        ContractAbi.PANTOS_HUB
    assert unregister_request.function_args == (service_node_address, )


@unittest.mock.patch.object(EthereumClient, '_start_transaction_submission',
                            side_effect=EthereumUtilitiesError)
def test_unregister_node_error(mock_start_transaction_submission,
                               ethereum_client):
    with pytest.raises(EthereumClientError):
        ethereum_client.unregister_node()


@unittest.mock.patch.object(EthereumClient, '_start_transaction_submission',
                            return_value=uuid.uuid4())
def test_update_node_url_correct(mock_start_transaction_submission,
                                 ethereum_client, service_node_url):
    ethereum_client.update_node_url(service_node_url)

    mock_start_transaction_submission.assert_called_once()
    update_request = mock_start_transaction_submission.call_args.args[0]
    assert update_request.versioned_contract_abi.contract_abi is \
        ContractAbi.PANTOS_HUB
    assert update_request.function_args == (service_node_url, )


@unittest.mock.patch.object(EthereumClient, '_start_transaction_submission',
                            side_effect=EthereumUtilitiesError)
def test_update_node_url_error(mock_start_transaction_submission,
                               ethereum_client, service_node_url):
    with pytest.raises(EthereumClientError):
        ethereum_client.update_node_url(service_node_url)


@unittest.mock.patch('pantos.servicenode.blockchains.ethereum.database_access')
@unittest.mock.patch.object(EthereumClient, '_create_hub_contract')
def test_start_transfer_submission_correct(mock_create_hub_contract,
                                           mock_database_access,
                                           ethereum_client,
                                           mock_get_blockchain_config, w3,
                                           transfer_submission_start_request,
                                           hub_contract_address):
    mock_get_blockchain_config.return_value = {
        'hub': hub_contract_address,
        'min_adaptable_fee_per_gas': 1000000000,
        'max_total_fee_per_gas': 50000000000,
        'adaptable_fee_increase_factor': 1.101,
        'blocks_until_resubmission': 10
    }
    blockchain_nonce = 2581
    internal_transaction_id = uuid.uuid4()
    mock_database_access.read_transfer_nonce.return_value = blockchain_nonce
    mock_start_transaction_submission = unittest.mock.MagicMock()
    mock_start_transaction_submission.return_value = internal_transaction_id

    with unittest.mock.patch.object(ethereum_client._get_utilities(),
                                    'start_transaction_submission',
                                    mock_start_transaction_submission):
        with unittest.mock.patch.object(w3.eth, 'get_transaction_count',
                                        return_value=blockchain_nonce):
            response_internal_transaction_id = ethereum_client.\
                start_transfer_submission(transfer_submission_start_request)

    assert response_internal_transaction_id == internal_transaction_id
    mock_database_access.update_transfer_nonce.assert_called_once_with(
        transfer_submission_start_request.internal_transfer_id,
        Blockchain.ETHEREUM, blockchain_nonce)
    mock_start_transaction_submission.assert_called_once()


@unittest.mock.patch('pantos.servicenode.blockchains.ethereum.database_access')
@unittest.mock.patch.object(EthereumClient, '_create_hub_contract')
def test_start_transfer_from_submission_correct(
        mock_create_hub_contract, mock_database_access, ethereum_client,
        mock_get_blockchain_config, w3, transfer_from_submission_start_request,
        hub_contract_address):
    mock_get_blockchain_config.return_value = {
        'hub': hub_contract_address,
        'min_adaptable_fee_per_gas': 1000000000,
        'max_total_fee_per_gas': 50000000000,
        'adaptable_fee_increase_factor': 1.101,
        'blocks_until_resubmission': 10
    }
    blockchain_nonce = 9214
    internal_transaction_id = uuid.uuid4()
    mock_database_access.read_transfer_nonce.return_value = blockchain_nonce
    mock_start_transaction_submission = unittest.mock.MagicMock()
    mock_start_transaction_submission.return_value = internal_transaction_id

    with unittest.mock.patch.object(ethereum_client._get_utilities(),
                                    'start_transaction_submission',
                                    mock_start_transaction_submission):
        with unittest.mock.patch.object(w3.eth, 'get_transaction_count',
                                        return_value=blockchain_nonce):
            response_internal_transaction_id = ethereum_client.\
                start_transfer_from_submission(
                    transfer_from_submission_start_request)

    assert response_internal_transaction_id == internal_transaction_id
    mock_database_access.update_transfer_nonce.assert_called_once_with(
        transfer_from_submission_start_request.internal_transfer_id,
        Blockchain.ETHEREUM, blockchain_nonce)
    mock_start_transaction_submission.assert_called_once()


@unittest.mock.patch.object(EthereumClient, '_create_hub_contract')
def test_start_transfer_submission_node_communication_error(
        mock_create_hub_contract, ethereum_client, w3,
        transfer_submission_start_request):
    error_message = 'some blockchain node error message'

    with unittest.mock.patch.object(w3.eth, 'get_transaction_count',
                                    side_effect=Exception(error_message)):
        with pytest.raises(EthereumClientError) as exception_info:
            ethereum_client.start_transfer_submission(
                transfer_submission_start_request)

    assert str(exception_info.value.__context__) == error_message
    assert (exception_info.value.details['request'] ==
            transfer_submission_start_request)


@unittest.mock.patch.object(EthereumClient, '_create_hub_contract')
def test_start_transfer_from_submission_node_communication_error(
        mock_create_hub_contract, ethereum_client, w3,
        transfer_from_submission_start_request):
    error_message = 'some blockchain node error message'

    with unittest.mock.patch.object(w3.eth, 'get_transaction_count',
                                    side_effect=Exception(error_message)):
        with pytest.raises(EthereumClientError) as exception_info:
            ethereum_client.start_transfer_from_submission(
                transfer_from_submission_start_request)

    assert str(exception_info.value.__context__) == error_message
    assert (exception_info.value.details['request'] ==
            transfer_from_submission_start_request)


@pytest.mark.parametrize(
    'transaction_error',
    [TransactionNonceTooLowError, TransactionUnderpricedError])
@unittest.mock.patch('pantos.servicenode.blockchains.ethereum.database_access')
@unittest.mock.patch.object(EthereumClient, '_create_hub_contract')
def test_start_transfer_submission_transaction_error(
        mock_create_hub_contract, mock_database_access, transaction_error,
        ethereum_client, mock_get_blockchain_config,
        transfer_submission_start_request, hub_contract_address):
    mock_get_blockchain_config.return_value = {
        'hub': hub_contract_address,
        'min_adaptable_fee_per_gas': 1000000000,
        'max_total_fee_per_gas': 50000000000,
        'adaptable_fee_increase_factor': 1.101,
        'blocks_until_resubmission': 10
    }

    with unittest.mock.patch.object(ethereum_client._get_utilities(),
                                    'start_transaction_submission',
                                    side_effect=transaction_error):
        with pytest.raises(EthereumClientError) as exception_info:
            ethereum_client.start_transfer_submission(
                transfer_submission_start_request)

    assert (exception_info.value.details['request'] ==
            transfer_submission_start_request)
    mock_database_access.reset_transfer_nonce.assert_called_once_with(
        transfer_submission_start_request.internal_transfer_id)


@pytest.mark.parametrize(
    'transaction_error',
    [TransactionNonceTooLowError, TransactionUnderpricedError])
@unittest.mock.patch('pantos.servicenode.blockchains.ethereum.database_access')
@unittest.mock.patch.object(EthereumClient, '_create_hub_contract')
def test_start_transfer_from_submission_transaction_error(
        mock_create_hub_contract, mock_database_access, transaction_error,
        ethereum_client, mock_get_blockchain_config,
        transfer_from_submission_start_request, hub_contract_address):
    mock_get_blockchain_config.return_value = {
        'hub': hub_contract_address,
        'min_adaptable_fee_per_gas': 1000000000,
        'max_total_fee_per_gas': 50000000000,
        'adaptable_fee_increase_factor': 1.101,
        'blocks_until_resubmission': 10
    }

    with unittest.mock.patch.object(ethereum_client._get_utilities(),
                                    'start_transaction_submission',
                                    side_effect=transaction_error):
        with pytest.raises(EthereumClientError) as exception_info:
            ethereum_client.start_transfer_from_submission(
                transfer_from_submission_start_request)

    assert (exception_info.value.details['request'] ==
            transfer_from_submission_start_request)
    mock_database_access.reset_transfer_nonce.assert_called_once_with(
        transfer_from_submission_start_request.internal_transfer_id)


@pytest.mark.parametrize(
    'verify_transfer_error',
    [(_INSUFFICIENT_BALANCE_ERROR, InsufficientBalanceError),
     (_INVALID_SIGNATURE_ERROR, InvalidSignatureError),
     ('some unknown error message', EthereumClientError)])
@unittest.mock.patch.object(EthereumClient, '_create_hub_contract')
def test_start_transfer_submission_verify_transfer_error(
        mock_create_hub_contract, verify_transfer_error, ethereum_client,
        transfer_submission_start_request):
    mock_create_hub_contract().get_function_by_name().side_effect = \
        web3.exceptions.ContractLogicError(verify_transfer_error[0])

    with pytest.raises(verify_transfer_error[1]):
        ethereum_client.start_transfer_submission(
            transfer_submission_start_request)


@pytest.mark.parametrize(
    'verify_transfer_error',
    [(_INSUFFICIENT_BALANCE_ERROR, InsufficientBalanceError),
     (_INVALID_SIGNATURE_ERROR, InvalidSignatureError),
     ('some unknown error message', EthereumClientError)])
@unittest.mock.patch.object(EthereumClient, '_create_hub_contract')
def test_start_transfer_from_submission_verify_transfer_error(
        mock_create_hub_contract, verify_transfer_error, ethereum_client,
        transfer_from_submission_start_request):
    mock_create_hub_contract().get_function_by_name().side_effect = \
        web3.exceptions.ContractLogicError(verify_transfer_error[0])

    with pytest.raises(verify_transfer_error[1]):
        ethereum_client.start_transfer_from_submission(
            transfer_from_submission_start_request)


@pytest.mark.parametrize(
    'transaction_receipt',
    [(_TRANSFER_TRANSACTION_RECEIPT, Blockchain.ETHEREUM),
     (_TRANSFER_FROM_TRANSACTION_RECEIPT, Blockchain.AVALANCHE)])
@unittest.mock.patch.object(EthereumClient, '_create_hub_contract')
def test_read_on_chain_transfer_id_correct(mock_create_hub_contract,
                                           transaction_receipt,
                                           ethereum_client, w3):
    transaction_id = transaction_receipt[0]['transactionHash'].hex()
    on_chain_transfer_id = 13573
    mock_hub_contract = mock_create_hub_contract()
    mock_hub_contract.events.Transfer().process_receipt().__getitem__(
    ).get.return_value = {
        'args': {
            'transferId': on_chain_transfer_id
        }
    }
    mock_hub_contract.events.TransferFrom().process_receipt().__getitem__(
    ).get.return_value = {
        'args': {
            'sourceTransferId': on_chain_transfer_id
        }
    }

    with unittest.mock.patch.object(w3.eth, 'get_transaction_receipt',
                                    return_value=transaction_receipt[0]):
        response_on_chain_transfer_id = \
            ethereum_client._read_on_chain_transfer_id(
                transaction_id, transaction_receipt[1])

    assert response_on_chain_transfer_id == on_chain_transfer_id


@unittest.mock.patch.object(EthereumClient, '_create_hub_contract')
def test_read_on_chain_transfer_id_error(mock_create_hub_contract,
                                         ethereum_client, w3):
    transaction_id = 'some_transaction_hash'
    destination_blockchain = Blockchain.CELO

    with unittest.mock.patch.object(w3.eth, 'get_transaction_receipt',
                                    side_effect=Exception):
        with pytest.raises(EthereumClientError) as exception_info:
            ethereum_client._read_on_chain_transfer_id(transaction_id,
                                                       destination_blockchain)

    assert exception_info.value.details['transaction_id'] == transaction_id
    assert (exception_info.value.details['destination_blockchain']
            is destination_blockchain)


@unittest.mock.patch.object(EthereumClient, '_get_utilities')
@unittest.mock.patch.object(EthereumClient, '_get_config',
                            return_value={'provider_timeout': None})
@unittest.mock.patch.object(EthereumClient, '__init__', lambda *args: None)
def test_create_web3_correct(mock_get_config, mock_get_utilities,
                             node_connections):
    mock_get_utilities(
    ).create_node_connections.return_value = node_connections
    assert EthereumClient()._EthereumClient__create_node_connections() \
        == node_connections


def test_is_unbonding_correct(ethereum_client, mock_get_blockchain_config,
                              provider_timeout, hub_contract_address,
                              mock_get_blockchain_utilities):
    mock_get_blockchain_config.return_value = {
        'provider_timeout': provider_timeout,
        'hub': hub_contract_address
    }
    mock_get_blockchain_utilities().create_contract().functions.\
        isServiceNodeInTheUnbondingPeriod().call().get.return_value = True

    result = ethereum_client.is_unbonding()

    assert result is True


def test_is_unbonding_error(ethereum_client, mock_get_blockchain_config):
    mock_get_blockchain_config.side_effect = Exception()

    with pytest.raises(EthereumClientError):
        ethereum_client.is_unbonding()


@unittest.mock.patch.object(EthereumClient, '_start_transaction_submission',
                            return_value=uuid.uuid4())
def test_cancel_unregistration_correct(mock_start_transaction_submission,
                                       ethereum_client, service_node_address):
    ethereum_client.cancel_unregistration()

    mock_start_transaction_submission.assert_called_once()
    cancel_request = mock_start_transaction_submission.call_args.args[0]
    assert cancel_request.versioned_contract_abi.contract_abi is \
        ContractAbi.PANTOS_HUB
    assert cancel_request.function_args == (service_node_address, )


@unittest.mock.patch.object(EthereumClient, '_start_transaction_submission',
                            side_effect=EthereumUtilitiesError)
def test_cancel_unregistration_error(mock_start_transaction_submission,
                                     ethereum_client):
    with pytest.raises(EthereumClientError):
        ethereum_client.cancel_unregistration()


@unittest.mock.patch('pantos.servicenode.blockchains.ethereum.time')
def test_get_validator_fee_factor_new_factor_correct(
        mocked_time, ethereum_client, mock_get_blockchain_config,
        provider_timeout, hub_contract_address, mock_get_blockchain_utilities):
    mocked_time.time.return_value = 10
    mock_get_blockchain_config.return_value = {
        'provider_timeout': provider_timeout,
        'hub': hub_contract_address
    }
    mock_get_blockchain_utilities().create_contract().functions.\
        getValidatorFeeRecord().call().get.return_value = [2, 4, 9]

    result = ethereum_client.get_validator_fee_factor(Blockchain.ETHEREUM)

    assert result == 4


@unittest.mock.patch('pantos.servicenode.blockchains.ethereum.time')
def test_get_validator_fee_factor_old_factor_correct(
        mocked_time, ethereum_client, mock_get_blockchain_config,
        provider_timeout, hub_contract_address, mock_get_blockchain_utilities):
    mocked_time.time.return_value = 10
    mock_get_blockchain_config.return_value = {
        'provider_timeout': provider_timeout,
        'hub': hub_contract_address
    }
    mock_get_blockchain_utilities().create_contract().functions.\
        getValidatorFeeRecord().call().get.return_value = [2, 4, 11]

    result = ethereum_client.get_validator_fee_factor(Blockchain.ETHEREUM)

    assert result == 2


def test_get_validator_fee_factor_error(ethereum_client,
                                        mock_get_blockchain_config):
    mock_get_blockchain_config.side_effect = Exception()

    with pytest.raises(EthereumClientError):
        ethereum_client.get_validator_fee_factor(Blockchain.ETHEREUM)
