"""Module that defines database-specific enumerations.

"""
import enum
import typing

from pantos.common.entities import ServiceNodeTransferStatus

_NEW_NONCE_ASSIGNED_OFFSET: typing.Final[int] = 100

assert max(ServiceNodeTransferStatus).value < _NEW_NONCE_ASSIGNED_OFFSET


class TransferStatus(enum.IntEnum):
    """Enumeration of possible transfer status values.

    """
    ACCEPTED = ServiceNodeTransferStatus.ACCEPTED.value
    FAILED = ServiceNodeTransferStatus.FAILED.value
    SUBMITTED = ServiceNodeTransferStatus.SUBMITTED.value
    REVERTED = ServiceNodeTransferStatus.REVERTED.value
    CONFIRMED = ServiceNodeTransferStatus.CONFIRMED.value
    ACCEPTED_NEW_NONCE_ASSIGNED = (ServiceNodeTransferStatus.ACCEPTED.value +
                                   _NEW_NONCE_ASSIGNED_OFFSET)

    def to_public_status(self) -> 'TransferStatus':
        """Convert a transfer status to its public counterpart.

        Returns
        -------
        TransferStatus
            The public transfer status.

        """
        return (self if self.value < _NEW_NONCE_ASSIGNED_OFFSET else
                TransferStatus(self.value - _NEW_NONCE_ASSIGNED_OFFSET))
