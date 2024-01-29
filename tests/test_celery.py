import unittest.mock

import pytest

from pantos.common.logging import LogFormat


@pytest.mark.parametrize('file_enabled', [True, False])
@pytest.mark.parametrize('console_enabled', [True, False])
@pytest.mark.parametrize('log_format',
                         [log_format for log_format in LogFormat])
@unittest.mock.patch('pantos.servicenode.celery.initialize_logger')
@unittest.mock.patch('pantos.servicenode.celery.config')
def test_setup_logger_correct(mocked_config, mocked_initialize_logger,
                              log_format, console_enabled, file_enabled):
    from pantos.servicenode.celery import setup_logger
    mocked_logger = unittest.mock.Mock()
    mocked_config_dict = {
        'application': {
            'debug': True
        },
        'celery': {
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
    mocked_config.__getitem__.side_effect = mocked_config_dict.__getitem__

    setup_logger(mocked_logger)

    assert mocked_initialize_logger.call_count == 1


@unittest.mock.patch('pantos.servicenode.celery.initialize_logger',
                     side_effect=Exception)
@unittest.mock.patch('pantos.servicenode.celery.config')
def test_setup_logger_initialize_logger_exception(mocked_config,
                                                  mocked_initialize_logger):
    from pantos.servicenode.celery import setup_logger
    mocked_logger = unittest.mock.Mock()
    mocked_config_dict = {
        'application': {
            'debug': True
        },
        'celery': {
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
    mocked_config.__getitem__.side_effect = mocked_config_dict.__getitem__

    with pytest.raises(SystemExit):
        setup_logger(mocked_logger)
