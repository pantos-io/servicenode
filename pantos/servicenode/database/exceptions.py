"""Module that defines database-specific exceptions.

"""
import typing

from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.exceptions import ServiceNodeError


class DatabaseError(ServiceNodeError):
    """Base exception class for all database errors.

    """
    pass


class SenderNonceNotUniqueError(DatabaseError):
    """Error that is raised when an already existing sender nonce is
    requested to be added again for a specific blockchain and sender
    address.

    """
    def __init__(self, blockchain: Blockchain, sender_address: str,
                 sender_nonce: int, **kwargs: typing.Any):
        """Construct an error instance.

        Parameters
        ----------
        blockchain : Blockchain
            The affected blockchain.
        sender_address : str
            The blockchain address of the sender.
        sender_nonce : int
            The non-unique sender nonce.
        **kwargs : dict
            Additional information about the error as keyword arguments.

        """
        super().__init__('sender nonce not unique', blockchain=blockchain,
                         sender_address=sender_address,
                         sender_nonce=sender_nonce, **kwargs)
