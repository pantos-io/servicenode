import unittest.mock

from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.configuration import _DEFAULT_FILE_NAME
from pantos.servicenode.configuration import Config
from pantos.servicenode.configuration import get_blockchain_config
from pantos.servicenode.configuration import get_blockchains_rpc_nodes
from pantos.servicenode.configuration import get_plugin_config
from pantos.servicenode.configuration import get_signer_config
from pantos.servicenode.configuration import load_config


def test_load_config_correct():
    config_mock = Config(_DEFAULT_FILE_NAME)

    with unittest.mock.patch('pantos.servicenode.configuration.config',
                             config_mock):
        load_config(reload=False)

        assert config_mock.is_loaded() is True


def test_config_not_loaded():
    config_mock = Config(_DEFAULT_FILE_NAME)

    with unittest.mock.patch('pantos.servicenode.configuration.config',
                             config_mock):
        assert config_mock.is_loaded() is False


@unittest.mock.patch('pantos.servicenode.configuration.config')
def test_get_blockchain_config_correct(mocked_config):
    config = get_blockchain_config(Blockchain.ETHEREUM)

    assert config == mocked_config.__getitem__().__getitem__()


@unittest.mock.patch('pantos.servicenode.configuration.config')
def test_get_signer_config_correct(mocked_config):
    config = get_signer_config()

    assert config == mocked_config.__getitem__()


@unittest.mock.patch('pantos.servicenode.configuration.config')
def test_get_plugin_config_correct(mocked_config):
    config = get_plugin_config()

    assert config == mocked_config.__getitem__()


@unittest.mock.patch('pantos.servicenode.configuration.get_blockchain_config')
def test_get_blockchain_rpc_nodes_no_active_blockchains_correct(
        mocked_get_blockchain_config):
    mocked_get_blockchain_config.return_value = {'active': False}

    assert {} == get_blockchains_rpc_nodes()


@unittest.mock.patch('pantos.servicenode.configuration.get_blockchain_config')
def test_get_blockchain_rpc_nodes_correct(mocked_get_blockchain_config):
    provider = 'https://some.provider'
    timeout = 10
    expected_rpc_nodes = {
        blockchain: ([provider], 10.0)
        for blockchain in Blockchain
    }
    mocked_get_blockchain_config.return_value = {
        'active': True,
        'provider': provider,
        'provider_timeout': timeout
    }

    assert expected_rpc_nodes == get_blockchains_rpc_nodes()


@unittest.mock.patch('pantos.servicenode.configuration.get_blockchain_config')
def test_get_blockchain_rpc_nodes_with_fallback_providers_correct(
        mocked_get_blockchain_config):
    provider = 'https://some.provider'
    timeout = 10
    fallback_providers = ['https://some.fallback.provider']
    expected_rpc_nodes = {
        blockchain: ([provider] + fallback_providers, 10.0)
        for blockchain in Blockchain
    }
    mocked_get_blockchain_config.return_value = {
        'active': True,
        'provider': provider,
        'provider_timeout': timeout,
        'fallback_providers': fallback_providers
    }

    assert expected_rpc_nodes == get_blockchains_rpc_nodes()
