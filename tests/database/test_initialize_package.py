import unittest.mock

import pytest
import sqlalchemy  # type: ignore
import sqlalchemy.exc  # type: ignore

from pantos.common.blockchains.enums import Blockchain
from pantos.servicenode.database import get_session
from pantos.servicenode.database import get_session_maker
from pantos.servicenode.database import initialize_package
from pantos.servicenode.database.enums import TransferStatus
from pantos.servicenode.database.exceptions import DatabaseError
from pantos.servicenode.database.models import Blockchain as Blockchain_
from pantos.servicenode.database.models import \
    TransferStatus as TransferStatus_


@unittest.mock.patch('pantos.servicenode.database.Blockchain', Blockchain)
@unittest.mock.patch('pantos.servicenode.database.config')
@unittest.mock.patch('pantos.servicenode.database.sqlalchemy.create_engine')
def test_initialize_package_blockchain_correct(mocked_create_engine,
                                               mocked_config,
                                               embedded_db_engine,
                                               db_clean_session):
    mocked_create_engine.return_value = embedded_db_engine
    mocked_config_dict = {
        'database': {
            'url': '',
            'echo': '',
            'pool_size': '',
            'max_overflow': '',
            'alembic_config': '',
            'apply_migrations': ''
        }
    }
    mocked_config.__getitem__.side_effect = mocked_config_dict.__getitem__
    blockchains = [blockchain for blockchain in sorted(Blockchain)]

    initialize_package()
    blockchains_in_db = db_clean_session.execute(
        sqlalchemy.select(Blockchain_)).fetchall()

    assert len(blockchains_in_db) == len(blockchains)
    for (blockchain_in_db, blockchain) in zip(blockchains_in_db, blockchains):
        assert blockchain.value == blockchain_in_db[0].id
        assert blockchain.name == blockchain_in_db[0].name


@unittest.mock.patch('pantos.servicenode.database.TransferStatus',
                     TransferStatus)
@unittest.mock.patch('pantos.servicenode.database.config')
@unittest.mock.patch('pantos.servicenode.database.sqlalchemy.create_engine')
def test_initialize_package_transfer_status_correct(mocked_create_engine,
                                                    mocked_config,
                                                    embedded_db_engine,
                                                    db_clean_session):
    mocked_create_engine.return_value = embedded_db_engine
    mocked_config_dict = {
        'database': {
            'url': '',
            'echo': '',
            'pool_size': '',
            'max_overflow': '',
            'alembic_config': '',
            'apply_migrations': ''
        }
    }
    mocked_config.__getitem__.side_effect = mocked_config_dict.__getitem__
    transfer_statuses = [
        transfer_status for transfer_status in sorted(TransferStatus)
    ]

    initialize_package()
    transfer_statuses_in_db = db_clean_session.execute(
        sqlalchemy.select(TransferStatus_)).fetchall()

    assert len(transfer_statuses_in_db) == len(transfer_statuses)
    for (transfer_status_in_db,
         transfer_status) in zip(transfer_statuses_in_db, transfer_statuses):
        assert transfer_status.value == transfer_status_in_db[0].id
        assert transfer_status.name == transfer_status_in_db[0].name


@unittest.mock.patch('pantos.servicenode.database.sqlalchemy.func.max',
                     side_effect=Exception)
@unittest.mock.patch('pantos.servicenode.database.config')
@unittest.mock.patch('pantos.servicenode.database.sqlalchemy.create_engine')
def test_initialize_package_raises_error(mocked_create_engine, mocked_config,
                                         mock_sorted):
    mocked_config_dict = {
        'database': {
            'url': '',
            'echo': '',
            'pool_size': '',
            'max_overflow': ''
        }
    }
    mocked_config.__getitem__.side_effect = mocked_config_dict.__getitem__

    with pytest.raises(Exception):
        initialize_package()


@unittest.mock.patch('pantos.servicenode.database._session_maker', 'session')
def test_get_session_maker_correct():
    session = get_session_maker()

    assert session == 'session'


@unittest.mock.patch('pantos.servicenode.database.get_session_maker')
def test_get_session_correct(mocked_get_session_maker):
    mocked_get_session_maker().return_value = 'session'

    session = get_session()

    assert session == 'session'


@unittest.mock.patch('pantos.servicenode.database._session_maker', None)
def test_get_session_maker_database_error():
    with pytest.raises(DatabaseError):
        get_session_maker()
