"""Package for managing and accessing the database.

"""
import typing

import sqlalchemy  # type: ignore
import sqlalchemy.exc  # type: ignore
import sqlalchemy.orm  # type: ignore

from pantos.common.blockchains.enums import Blockchain
from pantos.servicenode.configuration import config
from pantos.servicenode.database.enums import TransferStatus
from pantos.servicenode.database.exceptions import DatabaseError
from pantos.servicenode.database.models import Blockchain as Blockchain_
from pantos.servicenode.database.models import \
    TransferStatus as TransferStatus_

_session_maker: typing.Optional[sqlalchemy.orm.sessionmaker] = None


def get_session_maker() -> sqlalchemy.orm.sessionmaker:
    """Get the session maker for making sessions for managing
    persistence operations for ORM-mapped objects.

    Returns
    -------
    sqlalchemy.orm.sessionmaker
        The session maker.

    Raises
    ------
    DatabaseError
        If the database package has not been initialized.

    """
    if _session_maker is None:
        raise DatabaseError('database package not yet initialized')
    return _session_maker


def get_session() -> sqlalchemy.orm.Session:
    """Get a session for managing persistence operations for ORM-mapped
    objects.

    Returns
    -------
    sqlalchemy.orm.Session
        The session.

    Raises
    ------
    DatabaseError
        If the database package has not been initialized.

    """
    return get_session_maker()()


def initialize_package() -> None:
    sql_engine = sqlalchemy.create_engine(
        config['database']['url'], pool_size=config['database']['pool_size'],
        max_overflow=config['database']['max_overflow'], pool_pre_ping=True,
        echo=config['database']['echo'])
    global _session_maker
    _session_maker = sqlalchemy.orm.sessionmaker(bind=sql_engine)
    # Initialize the tables
    with _session_maker.begin() as session:
        # Blockchain table
        max_blockchain_id = \
            session.query(sqlalchemy.func.max(Blockchain_.id)).first()[0]
        for blockchain in sorted(Blockchain):
            if (max_blockchain_id is None
                    or max_blockchain_id < blockchain.value):
                session.add(
                    Blockchain_(id=blockchain.value, name=blockchain.name))
        # Transfer status table
        max_transfer_status_id = \
            session.query(sqlalchemy.func.max(TransferStatus_.id)).first()[0]
        for transfer_status in sorted(TransferStatus):
            if (max_transfer_status_id is None
                    or max_transfer_status_id < transfer_status.value):
                session.add(
                    TransferStatus_(id=transfer_status.value,
                                    name=transfer_status.name))
