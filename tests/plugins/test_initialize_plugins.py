import unittest.mock

import pytest
from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.plugins import initialize_plugins


@pytest.fixture
def patched_execute_bid_plugin(mocker):
    celery_mock = mocker.MagicMock(name="celery_mock")
    delay_mock = celery_mock.delay

    _module = mocker.MagicMock(name="execute_bid_plugin_mock")
    _module.execute_bid_plugin = celery_mock
    mocker.patch.dict('sys.modules',
                      {"pantos.servicenode.business.plugins": _module})

    yield delay_mock


@pytest.mark.parametrize('start_worker', [True, False])
@pytest.mark.parametrize('registered', [True, False])
@pytest.mark.parametrize('active', [True, False])
@unittest.mock.patch('pantos.servicenode.plugins.get_blockchain_config')
@unittest.mock.patch('pantos.servicenode.plugins._import_bid_plugin')
def test_initialize_plugins_correct(mocked_import_bid_plugin,
                                    mocked_get_blockchain_config,
                                    patched_execute_bid_plugin, active,
                                    registered, start_worker):
    mocked_get_blockchain_config.return_value = {
        'active': active,
        'registered': registered
    }
    initialize_plugins(start_worker)

    call_count = (len(Blockchain)
                  if active and registered and start_worker else 0)
    assert patched_execute_bid_plugin.call_count == call_count
