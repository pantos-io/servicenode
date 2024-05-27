"""Business logic for managing service node bids.

"""
import dataclasses
import logging
import typing

from pantos.common.blockchains.enums import Blockchain
from pantos.common.signer import get_signer

from pantos.servicenode.business.base import Interactor
from pantos.servicenode.business.base import InteractorError
from pantos.servicenode.configuration import get_signer_config
from pantos.servicenode.database import access as database_access

_logger = logging.getLogger(__name__)
"""Logger for this module."""


class BidInteractorError(InteractorError):
    """Exception class for all bid interactor errors.

    """
    pass


class BidInteractor(Interactor):
    """Interactor for managing service node bids.

    """

    @dataclasses.dataclass
    class Bid:
        """Data for a transfer bid.

        Attributes
        ----------
        execution_time : int
            The execution time in seconds of the bid for how long it takes
            to process a token transfer.
        valid_until : int
            The time in seconds since the epoch till when the bid is valid.
        fee : int
            The fee in Pan for processing a token transfer.
        signature : str
            The signature of the bid data, including the source blockchain id
            and the destination blockchain id.
        """
        execution_time: int
        valid_until: int
        fee: int
        signature: str

    def get_cross_blockchain_bids(
            self, source_blockchain_id: int, destination_blockchain_id: int) \
            -> typing.List[typing.Dict[str, typing.Any]]:
        """Get all cross-blockchain bids for the given source and destination
        blockchain ID.

        Parameters
        ----------
        source_blockchain_id : int
            The id of the source blockchain.
        destination_blockchain_id : int
            The id of the destination blockchain.

        Returns
        -------
        list of dict of str, any
            A list of cross-blockchain bids.

        Raises
        ------
        BidInteractorError
            If the cross-blockchain bids cannot be read from the
            database.

        """
        try:
            _logger.info('Reading cross-blockchain bids from database')
            raw_bids = database_access.read_cross_blockchain_bids(
                source_blockchain_id, destination_blockchain_id)
            bids = []
            signer_config = get_signer_config()
            signer = get_signer(signer_config['pem'],
                                signer_config['pem_password'])
            for bid in raw_bids:
                bid_message = signer.build_message('', int(bid.fee),
                                                   int(bid.valid_until),
                                                   source_blockchain_id,
                                                   destination_blockchain_id,
                                                   int(bid.execution_time))
                signature = signer.sign_message(bid_message)
                bids.append({
                    'fee': int(bid.fee),
                    'execution_time': int(bid.execution_time),
                    'valid_until': int(bid.valid_until),
                    'signature': signature
                })
        except Exception:
            raise BidInteractorError(
                'unable to read cross-blockchain bids from '
                f"{Blockchain(source_blockchain_id)} to "
                f"{Blockchain(destination_blockchain_id)} from database")
        return bids
