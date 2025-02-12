import unittest.mock

import pytest
from pantos.common.logging import LogFormat

from pantos.servicenode.application import create_application
from pantos.servicenode.application import initialize_application
from pantos.servicenode.business.node import NodeInteractor


@pytest.mark.parametrize('file_enabled', [True, False])
@pytest.mark.parametrize('console_enabled', [True, False])
@pytest.mark.parametrize('log_format',
                         [log_format for log_format in LogFormat])
@unittest.mock.patch(
    'pantos.servicenode.application.check_protocol_version_compatibility')
@unittest.mock.patch(
    'pantos.servicenode.application.initialize_blockchain_clients')
@unittest.mock.patch(
    'pantos.servicenode.application.initialize_database_package')
@unittest.mock.patch('pantos.servicenode.application.get_signer_config')
@unittest.mock.patch('pantos.servicenode.application.get_signer')
@unittest.mock.patch('pantos.servicenode.application.initialize_logger')
@unittest.mock.patch('pantos.servicenode.application.load_config')
@unittest.mock.patch('pantos.servicenode.application.config')
def test_initialize_application_correct(
        mock_config, mock_load_config, mock_initialize_logger, mock_get_signer,
        mock_get_signer_config, mock_initialize_database,
        mock_initialize_blockchain_clients,
        mock_check_protocol_version_compatibility, log_format, console_enabled,
        file_enabled):
    mock_config_dict = {
        'application': {
            'debug': True,
            'log': {
                'format': log_format.name.lower(),
                'console': {
                    'enabled': console_enabled
                },
                'file': {
                    'enabled': file_enabled,
                    'name': '',
                    'max_bytes': 0,
                    'backup_count': 0
                }
            }
        }
    }

    mock_config.__getitem__.side_effect = mock_config_dict.__getitem__

    initialize_application()

    assert mock_load_config.call_count == 1
    assert mock_initialize_logger.call_count == 1
    assert mock_initialize_database.call_count == 1
    assert mock_initialize_blockchain_clients.call_count == 1
    mock_check_protocol_version_compatibility.assert_called_once()
    mock_load_config.assert_called_with(reload=False)


@unittest.mock.patch('pantos.servicenode.application.logging.basicConfig')
@unittest.mock.patch('pantos.servicenode.application.load_config',
                     side_effect=Exception())
def test_initialize_application_raises_exception(mock_load_config,
                                                 mock_basic_config):
    with pytest.raises(SystemExit):
        initialize_application()


@unittest.mock.patch(
    'pantos.servicenode.application.initialize_blockchain_clients',
    side_effect=Exception)
@unittest.mock.patch(
    'pantos.servicenode.application.initialize_database_package')
@unittest.mock.patch('pantos.servicenode.application.initialize_logger')
@unittest.mock.patch('pantos.servicenode.application.logging')
@unittest.mock.patch('pantos.servicenode.application.load_config')
@unittest.mock.patch('pantos.servicenode.application.config')
def test_initialize_application_blockchain_clients_init_raises_exception(
        mock_config, mock_load_config, mock_logging, mock_initialize_logger,
        mock_initialize_database, mock_initialize_blockchain_clients):
    mock_config_dict = {
        'application': {
            'debug': True,
            'log': {
                'format': LogFormat.JSON.name.lower(),
                'console': {
                    'enabled': True
                },
                'file': {
                    'enabled': True,
                    'name': '',
                    'max_bytes': 0,
                    'backup_count': 0
                }
            }
        }
    }
    mock_config.__getitem__.side_effect = mock_config_dict.__getitem__

    with pytest.raises(SystemExit):
        initialize_application()


@unittest.mock.patch(
    'pantos.servicenode.application.initialize_database_package',
    side_effect=Exception)
@unittest.mock.patch('pantos.servicenode.application.initialize_logger')
@unittest.mock.patch('pantos.servicenode.application.logging')
@unittest.mock.patch('pantos.servicenode.application.load_config')
@unittest.mock.patch('pantos.servicenode.application.config')
def test_initialize_application_db_init_raises_exception(
        mock_config, mock_load_config, mock_logging, mock_initialize_logger,
        mock_initialize_database):
    mock_config_dict = {
        'application': {
            'debug': True,
            'log': {
                'format': LogFormat.JSON.name.lower(),
                'console': {
                    'enabled': True
                },
                'file': {
                    'enabled': True,
                    'name': '',
                    'max_bytes': 0,
                    'backup_count': 0
                }
            },
        }
    }
    mock_config.__getitem__.side_effect = mock_config_dict.__getitem__

    with pytest.raises(SystemExit):
        initialize_application()


@unittest.mock.patch('pantos.servicenode.application.initialize_logger',
                     side_effect=Exception)
@unittest.mock.patch('pantos.servicenode.application.logging.basicConfig')
@unittest.mock.patch('pantos.servicenode.application.load_config')
@unittest.mock.patch('pantos.servicenode.application.config')
def test_initialize_application_initialize_logger_exception(
        mock_config, mock_load_config, mock_basic_config,
        mock_initialize_logger):
    mock_config_dict = {
        'application': {
            'debug': True,
            'log': {
                'format': LogFormat.JSON.name.lower(),
                'console': {
                    'enabled': True
                },
                'file': {
                    'enabled': True,
                    'name': '',
                    'max_bytes': 0,
                    'backup_count': 0
                }
            }
        }
    }
    mock_config.__getitem__.side_effect = mock_config_dict.__getitem__

    with pytest.raises(SystemExit):
        initialize_application()


@unittest.mock.patch.object(NodeInteractor, 'update_node_registrations')
@unittest.mock.patch('pantos.servicenode.application.initialize_application')
@unittest.mock.patch('pantos.servicenode.application.initialize_plugins')
@unittest.mock.patch('pantos.servicenode.restapi.flask_app')
@unittest.mock.patch('pantos.servicenode.configuration.config')
def test_create_application_correct(mock_config, mock_flask_app,
                                    mock_initialized_plugins,
                                    mock_initialize_application,
                                    mock_update_bid_registration):
    returned_flask_app = create_application()

    mock_initialize_application.assert_called_once_with(True)
    mock_update_bid_registration.assert_called_once_with()
    assert returned_flask_app == mock_flask_app


@unittest.mock.patch.object(NodeInteractor, 'update_node_registrations',
                            side_effect=Exception)
@unittest.mock.patch('pantos.servicenode.application.initialize_application')
@unittest.mock.patch('pantos.servicenode.restapi.flask_app')
@unittest.mock.patch('pantos.servicenode.configuration.config')
def test_create_application_unable_to_update_node_registration(
        mock_config, mock_flask_app, mock_initialize_application,
        mock_update_node_registration):
    with pytest.raises(SystemExit):
        create_application()
