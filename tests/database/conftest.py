"""Shared fixtures for all pantos.servicenode.database package tests.

"""
import pytest
import sqlalchemy  # type: ignore
import sqlalchemy.orm  # type: ignore
from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.database.enums import TransferStatus
from pantos.servicenode.database.models import Base
from pantos.servicenode.database.models import Bid
from pantos.servicenode.database.models import Blockchain as Blockchain_
from pantos.servicenode.database.models import ForwarderContract
from pantos.servicenode.database.models import HubContract
from pantos.servicenode.database.models import TokenContract
from pantos.servicenode.database.models import Transfer
from pantos.servicenode.database.models import \
    TransferStatus as TransferStatus_


def populate_transfer_database(session, source_blockchain_ids, statuses,
                               nonces):
    token_contract = TokenContract(blockchain_id=0, address='')
    forwarder_contract = ForwarderContract(blockchain_id=0, address='')
    hub_contract = HubContract(blockchain_id=0, address='')
    session.add(hub_contract)
    session.flush()
    session.add(token_contract)
    session.add(forwarder_contract)
    session.flush()
    transfer_ids = []
    for source_blockchain_id, nonce, status in zip(source_blockchain_ids,
                                                   nonces, statuses):
        transfer = Transfer(source_blockchain_id=source_blockchain_id,
                            destination_blockchain_id=0, sender_address='',
                            recipient_address='',
                            source_token_contract_id=token_contract.id,
                            destination_token_contract_id=token_contract.id,
                            amount=0, fee=0, signature='',
                            hub_contract_id=hub_contract.id,
                            forwarder_contract_id=forwarder_contract.id,
                            nonce=nonce, status_id=status)
        session.add(transfer)
        session.flush()
        transfer_ids.append(transfer.id)
    session.commit()
    return transfer_ids


def initialize_database_models(session):
    """Initialize the database models with appropriate values.

    """
    for blockchain in sorted(Blockchain):
        session.execute(
            sqlalchemy.insert(Blockchain_).values(id=blockchain.value,
                                                  name=blockchain.name))
    for transfer_status in sorted(TransferStatus):
        session.execute(
            sqlalchemy.insert(TransferStatus_).values(
                id=transfer_status.value, name=transfer_status.name))

    session.commit()


def tear_down_all_models(session):
    """Delete all rows in all tables.

    """
    session.execute(sqlalchemy.delete(Transfer))
    session.execute(sqlalchemy.delete(TransferStatus_))
    session.execute(sqlalchemy.delete(Bid))
    session.execute(sqlalchemy.delete(ForwarderContract))
    session.execute(sqlalchemy.delete(HubContract))
    session.execute(sqlalchemy.delete(TokenContract))
    session.execute(sqlalchemy.delete(Blockchain_))

    session.commit()


@pytest.fixture(scope='session')
def embedded_db_engine():
    """Provides the engine of an embedded database.

    """
    sql_engine = sqlalchemy.create_engine('sqlite:///')  # in memory!
    with sql_engine.connect() as connection:
        connection.execute(sqlalchemy.text("PRAGMA foreign_keys=ON;"))
    return sql_engine


@pytest.fixture(scope='session')
def embedded_db_session_maker(embedded_db_engine):
    """Provides a session maker of an embedded database,
    with all the models created.

    """
    transfers_table: sqlalchemy.sql.schema.Table = Base.metadata.tables[
        'transfers']
    for constraint in transfers_table.constraints:
        if constraint.name == \
                'uq_transfers_source_blockchain_id_nonce_status_id':
            constraint.deferrable = None
    Blockchain_.__table__.create(embedded_db_engine)
    TokenContract.__table__.create(embedded_db_engine)
    HubContract.__table__.create(embedded_db_engine)
    ForwarderContract.__table__.create(embedded_db_engine)
    Bid.__table__.create(embedded_db_engine)
    TransferStatus_.__table__.create(embedded_db_engine)
    Transfer.__table__.create(embedded_db_engine)
    return sqlalchemy.orm.sessionmaker(bind=embedded_db_engine)


@pytest.fixture()
def db_initialized_session(embedded_db_session_maker):
    """Provides an initialized session of the database.

    """
    initialize_database_models(embedded_db_session_maker())
    yield embedded_db_session_maker()
    tear_down_all_models(embedded_db_session_maker())


@pytest.fixture()
def db_clean_session(embedded_db_session_maker):
    """Provides a session of the database.

    """
    yield embedded_db_session_maker()
    tear_down_all_models(embedded_db_session_maker())


@pytest.fixture(scope='session')
def postgres_db_engine():
    """Provides the engine of an postgres database.

    """
    sql_engine = sqlalchemy.create_engine(
        'postgresql://pantos-service-node:kP13yU9f@localhost/'
        'pantos-service-node-test')
    return sql_engine


@pytest.fixture(scope='session')
def postgres_db_session_maker(postgres_db_engine):
    Base.metadata.create_all(postgres_db_engine)
    return sqlalchemy.orm.sessionmaker(bind=postgres_db_engine)


@pytest.fixture()
def postgres_db_initialized_session(postgres_db_session_maker):
    """Provides a session maker of an postgres database,
    with all the models created.

    """
    initialize_database_models(postgres_db_session_maker())
    yield postgres_db_session_maker()
    tear_down_all_models(postgres_db_session_maker())
