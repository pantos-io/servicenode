"""Module for creating and initializing a Celery instance.

"""
import logging
import pathlib
import sys

import celery  # type: ignore
from pantos.common.logging import LogFile
from pantos.common.logging import LogFormat
from pantos.common.logging import initialize_logger

from pantos.servicenode.application import initialize_application
from pantos.servicenode.configuration import config
from pantos.servicenode.plugins import initialize_plugins

_TRANSFERS_QUEUE_NAME = 'transfers'
_BIDS_QUEUE_NAME = 'bids'


def is_celery_worker_process() -> bool:
    return (len(sys.argv) > 0 and sys.argv[0].endswith('celery')
            and 'worker' in sys.argv)


if is_celery_worker_process():
    initialize_application(False)  # pragma: no cover

celery_app = celery.Celery('pantos.servicenode',
                           broker=config['celery']['broker'],
                           backend=config['celery']['backend'],
                           include=[
                               'pantos.common.blockchains.tasks',
                               'pantos.servicenode.business.transfers',
                               'pantos.servicenode.business.plugins'
                           ])
"""Celery application instance."""

# Additional Celery configuration
celery_app.conf.update(
    result_expires=None,
    task_default_exchange='pantos.servicenode',
    task_default_queue='transfers',
    task_routes={
        'pantos.servicenode.business.plugins.execute_bid_plugin': {
            'queue': _BIDS_QUEUE_NAME
        },
        'pantos.servicenode.business.transfers.*': {
            'queue': _TRANSFERS_QUEUE_NAME
        },
        'pantos.common.blockchains.tasks.*': {
            'queue': _TRANSFERS_QUEUE_NAME
        }
    },
    task_track_started=True,
    worker_enable_remote_control=False)

if is_celery_worker_process():  # pragma: no cover
    # purge the bids queue at startup
    with celery_app.connection_for_write() as connection:
        connection.default_channel.queue_purge(_BIDS_QUEUE_NAME)
    initialize_plugins(start_worker=True)


@celery.signals.after_setup_task_logger.connect  # Celery task logger
@celery.signals.after_setup_logger.connect  # Celery logger
def setup_logger(logger: logging.Logger, *args, **kwargs):
    """Sent after the setup of every single task and Celery logger.
    Used to augment logging configuration.

    Parameters
    ----------
    logger: logging.Logger
        Logger object to be augmented.

    """
    log_format = LogFormat.from_name(config['celery']['log']['format'])
    standard_output = config['celery']['log']['console']['enabled']
    if not config['celery']['log']['file']['enabled']:
        log_file = None
    else:
        file_path = pathlib.Path(config['celery']['log']['file']['name'])
        max_bytes = config['celery']['log']['file']['max_bytes']
        backup_count = config['celery']['log']['file']['backup_count']
        log_file = LogFile(file_path, max_bytes, backup_count)
    debug = config['application']['debug']
    try:
        initialize_logger(logger, log_format, standard_output, log_file, debug)
    except Exception:
        logger.critical('unable to initialize logging', exc_info=True)
        sys.exit(1)
