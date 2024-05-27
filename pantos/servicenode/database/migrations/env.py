import typing

import alembic
import sqlalchemy  # type: ignore
import sqlalchemy.pool  # type: ignore

from pantos.servicenode.configuration import config
from pantos.servicenode.configuration import load_config
from pantos.servicenode.database.models import Base

target_metadata = Base.metadata
alembic_config = alembic.context.config
load_config(reload=False)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    alembic.context.configure(url=config['database']['url'],
                              target_metadata=target_metadata,
                              literal_binds=True,
                              dialect_opts={"paramstyle": "named"})

    with alembic.context.begin_transaction():
        alembic.context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    alembic_ini_config: typing.Dict[str, str] = typing.cast(
        typing.Dict[str, str],
        alembic_config.get_section(
            alembic_config.config_ini_section)) if alembic_config.get_section(
                alembic_config.config_ini_section) is not None else {}
    connectable = sqlalchemy.engine_from_config(
        alembic_ini_config, url=config['database']['url'],
        prefix="sqlalchemy.", poolclass=sqlalchemy.pool.NullPool)

    with connectable.connect() as connection:
        alembic.context.configure(connection=connection,
                                  target_metadata=target_metadata)

        with alembic.context.begin_transaction():
            alembic.context.run_migrations()


if alembic.context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
