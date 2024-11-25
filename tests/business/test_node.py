import typing
import unittest.mock

import pytest
from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.blockchains.base import BlockchainClientError
from pantos.servicenode.business import node as node_module
from pantos.servicenode.business.base import InvalidAmountError
from pantos.servicenode.business.base import InvalidBlockchainAddressError
from pantos.servicenode.business.base import InvalidUrlError
from pantos.servicenode.business.node import NodeInteractor
from pantos.servicenode.business.node import NodeInteractorError

_CONFIG_NODE_URL = 'https://config.node.url/'

_DEFAULT_NODE_URL = 'https://default.node.url/'

_DEFAULT_WITHDRAWAL_ADDRESS = '0x165A78accc6233466979AD311af606F4714da475'

_CONFIG_WITHDRAWAL_ADDRESS = '0xceb95Cb81e4f71c8Fc426a84fA29F2ac552AD752'

_DEFAULT_MINIMUM_DEPOSIT = 10000000000000

_CONFIG_DEPOSIT = _DEFAULT_MINIMUM_DEPOSIT

_DEFAULT_OWN_PAN_BALANCE = _DEFAULT_MINIMUM_DEPOSIT


class MockBlockchainClientError(BlockchainClientError):
    def __init__(self):
        super().__init__('')


class MockBlockchainClient:
    def __init__(self, node_registered, is_unbonding, raise_error,
                 minimum_deposit=None, own_pan_balance=None):
        self.node_registered = node_registered
        self.unbonding = is_unbonding
        self.node_url = _DEFAULT_NODE_URL
        self.withdrawal_address = _DEFAULT_WITHDRAWAL_ADDRESS
        self.raise_error = raise_error
        self.minimum_deposit = (minimum_deposit if minimum_deposit is not None
                                else _DEFAULT_MINIMUM_DEPOSIT)
        self.own_pan_balance = (own_pan_balance if own_pan_balance is not None
                                else _DEFAULT_OWN_PAN_BALANCE)

    def is_node_registered(self):
        if self.raise_error:
            raise MockBlockchainClientError
        return self.node_registered

    def is_valid_address(self, address):
        if self.raise_error:
            raise MockBlockchainClientError
        return len(address) > 0

    def read_minimum_deposit(self):
        if self.raise_error:
            raise MockBlockchainClientError
        return self.minimum_deposit

    def read_node_url(self):
        if self.raise_error:
            raise MockBlockchainClientError
        assert self.node_registered
        return self.node_url

    def read_own_pan_balance(self):
        if self.raise_error:
            raise MockBlockchainClientError
        return self.own_pan_balance

    def register_node(self, node_url, node_deposit, withdrawal_address):
        if self.raise_error:
            raise MockBlockchainClientError
        assert not self.node_registered
        assert isinstance(node_url, str)
        assert len(node_url) > 0
        assert isinstance(node_deposit, int)
        assert node_deposit >= self.minimum_deposit
        self.node_registered = True
        self.node_url = node_url
        self.withdrawal_address = withdrawal_address

    def unregister_node(self):
        if self.raise_error:
            raise MockBlockchainClientError
        assert self.node_registered
        self.node_registered = False

    def update_node_url(self, node_url):
        if self.raise_error:
            raise MockBlockchainClientError
        assert self.node_registered
        assert isinstance(node_url, str)
        assert len(node_url) > 0
        assert node_url != self.node_url
        self.node_url = node_url

    def is_unbonding(self):
        if self.raise_error:
            raise MockBlockchainClientError
        return self.unbonding

    def cancel_unregistration(self):
        if self.raise_error:
            raise MockBlockchainClientError
        self.node_registered = True


@pytest.fixture(autouse=True)
def mock_blockchain_client(request, monkeypatch):
    is_registered_marker = request.node.get_closest_marker('is_registered')
    is_registered = ([] if is_registered_marker is None else
                     is_registered_marker.args[0])
    unbonding_marker = request.node.get_closest_marker('unbonding')
    unbonding = [] if unbonding_marker is None else unbonding_marker.args[0]
    error_marker = request.node.get_closest_marker('error')
    minimum_deposit_marker = request.node.get_closest_marker('minimum_deposit')
    minimum_deposit = (None if minimum_deposit_marker is None else
                       minimum_deposit_marker.args[0])
    own_pan_balance_marker = request.node.get_closest_marker('own_pan_balance')
    own_pan_balance = (None if own_pan_balance_marker is None else
                       own_pan_balance_marker.args[0])
    blockchain_clients: dict[Blockchain, MockBlockchainClient] = {}

    def mock_get_blockchain_client(blockchain):
        try:
            return blockchain_clients[blockchain]
        except KeyError:
            blockchain_client = MockBlockchainClient(
                blockchain in is_registered, blockchain in unbonding,
                error_marker is not None, minimum_deposit=minimum_deposit,
                own_pan_balance=own_pan_balance)
            blockchain_clients[blockchain] = blockchain_client
            return blockchain_client

    monkeypatch.setattr(node_module, 'get_blockchain_client',
                        mock_get_blockchain_client)


@pytest.fixture(autouse=True)
def mock_config(request, monkeypatch):
    to_be_registered_marker = request.node.get_closest_marker(
        'to_be_registered')
    to_be_registered = ([] if to_be_registered_marker is None else
                        to_be_registered_marker.args[0])
    node_url_marker = request.node.get_closest_marker('node_url')
    node_url = (_CONFIG_NODE_URL
                if node_url_marker is None else node_url_marker.args[0])
    withdrawal_address_marker = request.node.get_closest_marker(
        'withdrawal_address')
    withdrawal_address = (_CONFIG_WITHDRAWAL_ADDRESS
                          if withdrawal_address_marker is None else
                          withdrawal_address_marker.args[0])
    config: dict[str, typing.Any] = {}
    config['application'] = {}
    config['application']['url'] = node_url
    config['blockchains'] = {}
    for blockchain in Blockchain:
        blockchain_name = blockchain.name.lower()
        config['blockchains'][blockchain_name] = {}
        config['blockchains'][blockchain_name]['active'] = True
        config['blockchains'][blockchain_name]['registered'] = (
            blockchain in to_be_registered)
        config['blockchains'][blockchain_name]['deposit'] = _CONFIG_DEPOSIT
        config['blockchains'][blockchain_name][
            'withdrawal_address'] = withdrawal_address

    def mock_get_blockchain_config(blockchain):
        return config['blockchains'][blockchain.name.lower()]

    monkeypatch.setattr(node_module, 'config', config)
    monkeypatch.setattr(node_module, 'get_blockchain_config',
                        mock_get_blockchain_config)


@pytest.fixture(scope='module')
def node_interactor():
    return NodeInteractor()


def update_node_registrations_no_error(request, node_interactor):
    node_interactor.update_node_registrations()
    to_be_registered_marker = request.node.get_closest_marker(
        'to_be_registered')
    to_be_registered = ([] if to_be_registered_marker is None else
                        to_be_registered_marker.args[0])
    unbonding_marker = request.node.get_closest_marker('unbonding')
    unbonding = [] if unbonding_marker is None else unbonding_marker.args[0]
    get_blockchain_client = getattr(node_module, 'get_blockchain_client')
    for blockchain in Blockchain:
        blockchain_client = get_blockchain_client(blockchain)
        if blockchain in to_be_registered:
            assert blockchain_client.node_registered
            if blockchain in unbonding:
                assert blockchain_client.node_url == _DEFAULT_NODE_URL
            else:
                assert blockchain_client.node_url == _CONFIG_NODE_URL
        else:
            assert not blockchain_client.node_registered
            assert blockchain_client.node_url == _DEFAULT_NODE_URL
            assert (blockchain_client.withdrawal_address ==
                    _DEFAULT_WITHDRAWAL_ADDRESS)


@pytest.mark.to_be_registered(list(Blockchain))
@pytest.mark.is_registered(list(Blockchain))
def test_update_node_registrations_all_active_all_registered(
        request, node_interactor):
    update_node_registrations_no_error(request, node_interactor)


@pytest.mark.to_be_registered(list(Blockchain))
@pytest.mark.unbonding(list(Blockchain))
def test_update_node_registrations_all_active_none_registered_all_unbonding(
        request, node_interactor):
    update_node_registrations_no_error(request, node_interactor)


@pytest.mark.to_be_registered(list(Blockchain))
def test_update_node_registrations_all_active_none_registered(
        request, node_interactor):
    update_node_registrations_no_error(request, node_interactor)


@pytest.mark.is_registered(list(Blockchain))
def test_update_node_registrations_none_active_all_registered(
        request, node_interactor):
    update_node_registrations_no_error(request, node_interactor)


def test_update_node_registrations_none_active_none_registered(
        request, node_interactor):
    update_node_registrations_no_error(request, node_interactor)


@pytest.mark.to_be_registered([Blockchain.AVALANCHE, Blockchain.ETHEREUM])
@pytest.mark.is_registered(list(Blockchain))
def test_update_node_registrations_some_active_all_registered(
        request, node_interactor):
    update_node_registrations_no_error(request, node_interactor)


@pytest.mark.to_be_registered(list(Blockchain))
@pytest.mark.is_registered([Blockchain.SONIC, Blockchain.POLYGON])
def test_update_node_registrations_all_active_some_registered(
        request, node_interactor):
    update_node_registrations_no_error(request, node_interactor)


@pytest.mark.is_registered([Blockchain.ETHEREUM, Blockchain.SOLANA])
def test_update_node_registrations_none_active_some_registered(
        request, node_interactor):
    update_node_registrations_no_error(request, node_interactor)


@pytest.mark.to_be_registered(
    [Blockchain.BNB_CHAIN, Blockchain.ETHEREUM, Blockchain.SOLANA])
@pytest.mark.is_registered(
    [Blockchain.AVALANCHE, Blockchain.BNB_CHAIN, Blockchain.CRONOS])
def test_update_node_registrations_some_active_some_registered_overlapping(
        request, node_interactor):
    update_node_registrations_no_error(request, node_interactor)


@pytest.mark.to_be_registered(
    [Blockchain.AVALANCHE, Blockchain.BNB_CHAIN, Blockchain.POLYGON])
@pytest.mark.is_registered(
    [Blockchain.CELO, Blockchain.ETHEREUM, Blockchain.SOLANA])
def test_update_node_registrations_some_active_some_registered_non_overlapping(
        request, node_interactor):
    update_node_registrations_no_error(request, node_interactor)


@pytest.mark.to_be_registered(list(Blockchain))
@pytest.mark.node_url('ftp://some.url')
def test_update_node_registrations_invalid_node_url_error(node_interactor):
    with pytest.raises(InvalidUrlError) as exception_info:
        node_interactor.update_node_registrations()

    assert isinstance(exception_info.value, NodeInteractorError)


@pytest.mark.to_be_registered(list(Blockchain))
@pytest.mark.is_registered(list(Blockchain))
@pytest.mark.node_url('nourl')
def test_update_node_registrations_invalid_node_url_update_error(
        node_interactor):
    with pytest.raises(InvalidUrlError) as exception_info:
        node_interactor.update_node_registrations()

    assert isinstance(exception_info.value, NodeInteractorError)


@pytest.mark.to_be_registered(list(Blockchain))
@unittest.mock.patch('urllib.parse.urlparse', side_effect=ValueError)
def test_update_node_registrations_invalid_node_url_urlparse_error(
        mock_urlparse, node_interactor):
    with pytest.raises(InvalidUrlError) as exception_info:
        node_interactor.update_node_registrations()

    assert isinstance(exception_info.value, NodeInteractorError)


@pytest.mark.to_be_registered(list(Blockchain))
@pytest.mark.minimum_deposit(_CONFIG_DEPOSIT + 1)
def test_update_node_registrations_invalid_deposit_error(node_interactor):
    with pytest.raises(InvalidAmountError) as exception_info:
        node_interactor.update_node_registrations()

    assert isinstance(exception_info.value, NodeInteractorError)


@pytest.mark.to_be_registered(list(Blockchain))
@pytest.mark.own_pan_balance(_CONFIG_DEPOSIT - 1)
def test_update_node_registrations_invalid_balance_error(node_interactor):
    with pytest.raises(InvalidAmountError) as exception_info:
        node_interactor.update_node_registrations()

    assert isinstance(exception_info.value, NodeInteractorError)


@pytest.mark.to_be_registered(list(Blockchain))
@pytest.mark.withdrawal_address('')
def test_update_node_registrations_invalid_withdrawal_address_error(
        node_interactor):
    with pytest.raises(InvalidBlockchainAddressError) as exception_info:
        node_interactor.update_node_registrations()

    assert isinstance(exception_info.value, NodeInteractorError)


@pytest.mark.to_be_registered(list(Blockchain))
@pytest.mark.error
def test_update_node_registrations_error(node_interactor):
    with pytest.raises(NodeInteractorError):
        node_interactor.update_node_registrations()


@unittest.mock.patch('pantos.servicenode.business.node.get_blockchain_client')
@unittest.mock.patch('pantos.servicenode.business.node.get_blockchain_config')
def test_update_node_registrations_inactive_blockchain_non_working_node(
        mocked_get_blockchain_config, mocked_get_blockchain_client,
        node_interactor):
    mocked_get_blockchain_config().__getitem__.return_value = False
    mocked_get_blockchain_client.side_effect = BlockchainClientError('')

    node_interactor.update_node_registrations()
