"""Module that defines the database models.

"""
import datetime
import typing

import sqlalchemy  # type: ignore
import sqlalchemy.orm  # type: ignore

UNIQUE_SENDER_NONCE_CONSTRAINT = 'unique_sender_nonce'
"""Name of the unique sender nonce constraint."""

Base: typing.Any = sqlalchemy.orm.declarative_base()
"""SQLAlchemy base class for declarative class definitions."""


class Blockchain(Base):
    """Model class for the "blockchains" database table. Each instance
    represents a blockchain supported by Pantos.

    Attributes
    ----------
    id : sqlalchemy.Column
        The unique blockchain ID (primary key, equal to the Blockchain
        enum value).
    name : sqlalchemy.Column
        The blockchain's name (equal to the Blockchain enum name).

    """
    __tablename__ = 'blockchains'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    hub_contracts = sqlalchemy.orm.relationship('HubContract',
                                                back_populates='blockchain')
    forwarder_contracts = sqlalchemy.orm.relationship(
        'ForwarderContract', back_populates='blockchain')
    token_contracts = sqlalchemy.orm.relationship('TokenContract',
                                                  back_populates='blockchain')


class HubContract(Base):
    """Model class for the "hub_contracts" database table. Each instance
    represents a Pantos Hub contract deployed on a blockchain. It can be
    either the current or an old version of the Pantos Hub contract on
    its blockchain.

    Attributes
    ----------
    id : sqlalchemy.Column
        The unique hub contract ID (primary key).
    blockchain_id : sqlalchemy.Column
        The unique blockchain ID (foreign key).
    address : sqlalchemy.Column
        The unique address of the contract on its blockchain.

    """
    __tablename__ = 'hub_contracts'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    blockchain_id = sqlalchemy.Column(sqlalchemy.Integer,
                                      sqlalchemy.ForeignKey('blockchains.id'),
                                      nullable=False)
    address = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    blockchain = sqlalchemy.orm.relationship('Blockchain',
                                             back_populates='hub_contracts')
    __table_args__ = (sqlalchemy.UniqueConstraint(blockchain_id, address), )


class ForwarderContract(Base):
    """Model class for the "forwarder_contracts" database table. Each
    instance represents a Pantos Forwarder contract deployed on a
    blockchain. It can be either the current or an old version of the
    Pantos Forwarder contract on its blockchain.

    Attributes
    ----------
    id : sqlalchemy.Column
        The unique forwarder contract ID (primary key).
    blockchain_id : sqlalchemy.Column
        The unique blockchain ID (foreign key).
    address : sqlalchemy.Column
        The unique address of the contract on its blockchain.

    """
    __tablename__ = 'forwarder_contracts'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    blockchain_id = sqlalchemy.Column(sqlalchemy.Integer,
                                      sqlalchemy.ForeignKey('blockchains.id'),
                                      nullable=False)
    address = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    blockchain = sqlalchemy.orm.relationship(
        'Blockchain', back_populates='forwarder_contracts')
    __table_args__ = (sqlalchemy.UniqueConstraint(blockchain_id, address), )


class TokenContract(Base):
    """Model class for the "token_contracts" database table. Each
    instance represents a token contract deployed on a supported
    blockchain and registered at the Pantos Hub.

    Attributes
    ----------
    id : sqlalchemy.Column
        The unique token contract ID (primary key).
    blockchain_id : sqlalchemy.Column
        The unique blockchain ID (foreign key).
    address : sqlalchemy.Column
        The unique address of the contract on its blockchain.

    """
    __tablename__ = 'token_contracts'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    blockchain_id = sqlalchemy.Column(sqlalchemy.Integer,
                                      sqlalchemy.ForeignKey('blockchains.id'),
                                      nullable=False)
    address = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    blockchain = sqlalchemy.orm.relationship('Blockchain',
                                             back_populates='token_contracts')
    __table_args__ = (sqlalchemy.schema.Index(
        'ux_token_contracts_blockchain_id_address', blockchain_id, address,
        unique=True), )


class Bid(Base):
    """Model class for the "bids" database table. Each instance
    represents a service node bid registered at the Pantos Hub of a
    supported source blockchain.

    Attributes
    ----------
    id : sqlalchemy.Column
        The blockchain-independent unique ID of the bid (primary key).
    source_blockchain_id : sqlalchemy.Column
        The unique ID of the source blockchain (foreign key).
    destination_blockchain_id : sqlalchemy.Column
        The unique ID of the destination blockchain (foreign key).
    execution_time : sqlalchemy.Column
        The maximum execution time of a transfer on the source
        blockchain (in seconds).
    valid_until : sqlalchemy.Column
        The maximum time a bid is valid and therefore accepted by the
        service node (in seconds).
    fee : sqlalchemy.Column
        The fee for a transfer (in PAN).

    """
    __tablename__ = 'bids'
    source_blockchain_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey('blockchains.id'),
        nullable=False, primary_key=True)
    destination_blockchain_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey('blockchains.id'),
        nullable=False, primary_key=True)
    execution_time = sqlalchemy.Column(sqlalchemy.Integer, nullable=False,
                                       primary_key=True)
    valid_until = sqlalchemy.Column(sqlalchemy.Integer, nullable=False)
    fee = sqlalchemy.Column(
        # Large enough for a 256-bit unsigned integer
        sqlalchemy.Numeric(precision=78, scale=0),
        nullable=False)

    source_blockchain = sqlalchemy.orm.relationship(
        'Blockchain', foreign_keys=[source_blockchain_id])
    destination_blockchain = sqlalchemy.orm.relationship(
        'Blockchain', foreign_keys=[destination_blockchain_id])


class TransferStatus(Base):
    """Model class for the "transfer_status" database table. Each
    instance represents a possible status of Pantos transfers.

    Attributes
    ----------
    id : sqlalchemy.Column
        The unique transfer status ID (primary key, equal to the
        TransferStatus enum value).
    name : sqlalchemy.Column
        The transfer status's name (equal to the TransferStatus enum
        name).

    """
    __tablename__ = 'transfer_status'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.Text, nullable=False)


class Transfer(Base):
    """Model class for the "transfers" database table. Each instance
    represents a (possibly cross-chain) Pantos token transfer.

    Attributes
    ----------
    id : sqlalchemy.Column
        The blockchain-independent unique ID of the transfer (primary
        key).
    source_blockchain_id : sqlalchemy.Column
        The unique ID of the source blockchain (foreign key).
    destination_blockchain_id : sqlalchemy.Column
        The unique ID of the destination blockchain (foreign key).
    sender_address : sqlalchemy.Column
        The address of the sender on the source blockchain.
    recipient_address : sqlalchemy.Column
        The address of the recipient on the destination blockchain.
    source_token_contract_id : sqlalchemy.Column
        The unique token contract ID of the token on the source
        blockchain (foreign key).
    destination_token_contract_id : sqlalchemy.Column
        The unique token contract ID of the token on the destination
        blockchain (foreign key).
    amount : sqlalchemy.Column
        The amount of tokens sent by the sender to the recipient.
    fee : sqlalchemy.Column
        The fee paid by the sender for the transfer.
    sender_nonce : sqlalchemy.Column
        The nonce of the sender at the Pantos Forwarder contract of the
        source blockchain.
    signature : sqlalchemy.Column
        The signature of the sender for the transfer.
    hub_contract_id : sqlalchemy.Column
        The unique ID of the Pantos Hub contract on the source
        blockchain (foreign key).
    forwarder_contract_id : sqlalchemy.Column
        The unique ID of the Pantos Forwarder contract on the source
        blockchain (foreign key).
    task_id : sqlalchemy.Column
        The unique ID of the Celery transfer task.
    on_chain_transfer_id : sqlalchemy.Column
        The unique transfer ID assigned by the Pantos Hub contract of
        the source blockchain.
    transaction_id : sqlalchemy.Column
        The unique transaction ID/hash of the source blockchain for the
        transfer.
    nonce : sqlalchemy.Column
        The nonce used for the transaction on the blockchain (NULL if
        the transaction has not been sent yet, or if transaction is
        failed and the nonce has been reused in another transaction).
    status_id : sqlalchemy.Column
        The ID of the transfer status (foreign key).
    created : sqlalchemy.Column
        The timestamp when the transfer request was received.
    updated : sqlalchemy.Column
        The timestamp when the transfer was last updated.

    """
    __tablename__ = 'transfers'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    source_blockchain_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey('blockchains.id'),
        nullable=False)
    destination_blockchain_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey('blockchains.id'),
        nullable=False)
    sender_address = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    recipient_address = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    source_token_contract_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey('token_contracts.id'),
        nullable=False)
    destination_token_contract_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey('token_contracts.id'),
        nullable=False)
    amount = sqlalchemy.Column(
        # Large enough for a 256-bit unsigned integer
        sqlalchemy.Numeric(precision=78, scale=0),
        nullable=False)
    fee = sqlalchemy.Column(
        # Large enough for a 256-bit unsigned integer
        sqlalchemy.Numeric(precision=78, scale=0),
        nullable=False)
    sender_nonce = sqlalchemy.Column(
        # Large enough for a 256-bit unsigned integer
        sqlalchemy.Numeric(precision=78, scale=0))
    signature = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    hub_contract_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey('hub_contracts.id'),
        nullable=False)
    forwarder_contract_id = sqlalchemy.Column(
        sqlalchemy.Integer, sqlalchemy.ForeignKey('forwarder_contracts.id'),
        nullable=False)
    task_id = sqlalchemy.Column(sqlalchemy.Text, unique=True)
    on_chain_transfer_id = sqlalchemy.Column(
        # Large enough for a 256-bit unsigned integer
        sqlalchemy.Numeric(precision=78, scale=0))
    transaction_id = sqlalchemy.Column(sqlalchemy.Text)
    nonce = sqlalchemy.Column(sqlalchemy.BigInteger)
    status_id = sqlalchemy.Column(sqlalchemy.Integer,
                                  sqlalchemy.ForeignKey('transfer_status.id'),
                                  nullable=False)
    created = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False,
                                default=datetime.datetime.utcnow)
    updated = sqlalchemy.Column(sqlalchemy.DateTime)
    source_blockchain = sqlalchemy.orm.relationship(
        'Blockchain',
        primaryjoin='Transfer.source_blockchain_id==Blockchain.id')
    destination_blockchain = sqlalchemy.orm.relationship(
        'Blockchain',
        primaryjoin='Transfer.destination_blockchain_id==Blockchain.id')
    source_token_contract = sqlalchemy.orm.relationship(
        'TokenContract',
        primaryjoin='Transfer.source_token_contract_id==TokenContract.id',
        lazy='joined')
    destination_token_contract = sqlalchemy.orm.relationship(
        'TokenContract',
        primaryjoin='Transfer.destination_token_contract_id==TokenContract.id',
        lazy='joined')
    hub_contract = sqlalchemy.orm.relationship('HubContract')
    forwarder_contract = sqlalchemy.orm.relationship('ForwarderContract')
    status = sqlalchemy.orm.relationship('TransferStatus')
    __table_args__ = (
        sqlalchemy.UniqueConstraint(forwarder_contract_id, sender_address,
                                    sender_nonce,
                                    name=UNIQUE_SENDER_NONCE_CONSTRAINT),
        sqlalchemy.UniqueConstraint(hub_contract_id, on_chain_transfer_id),
        sqlalchemy.UniqueConstraint(source_blockchain_id, transaction_id),
        sqlalchemy.UniqueConstraint(
            source_blockchain_id, nonce, status_id, deferrable=True,
            name='uq_transfers_source_blockchain_id_nonce_status_id'),
        sqlalchemy.schema.Index(
            'ix_transfers_source_blockchain_id_nonce_status_id',
            source_blockchain_id, nonce.desc(), status_id),
    )
