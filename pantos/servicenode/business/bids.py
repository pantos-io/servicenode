"""Business logic for managing service node bids.

"""
import logging

from pantos.common.blockchains.enums import Blockchain
from pantos.common.signer import get_signer

from pantos.servicenode.business.base import Interactor
from pantos.servicenode.business.base import InteractorError
from pantos.servicenode.configuration import get_signer_config
from pantos.servicenode.database import access as database_access

_logger = logging.getLogger(__name__)


class BidInteractorError(InteractorError):
    """Exception class for all bid interactor errors.

    """
    pass


class BidInteractor(Interactor):
    """Interactor for managing service node bids.

    """
    def get_current_bids(
            self, source_blockchain_id: int,
            destination_blockchain_id: int) -> list[dict[str, int | str]]:
        """Get the current bids for a given source and destination
        blockchain.

        Parameters
        ----------
        source_blockchain_id : int
            The ID of the source blockchain.
        destination_blockchain_id : int
            The ID of the destination blockchain.

        Returns
        -------
        list of dict
            The list of current bids.

        Raises
        ------
        BidInteractorError
            If the bids cannot be read from the database.

        """
        try:
            _logger.info(
                'reading bids from database', extra={
                    'source_blockchain': Blockchain(source_blockchain_id),
                    'destination_blockchain': Blockchain(
                        destination_blockchain_id)
                })
            raw_bids = database_access.read_bids(source_blockchain_id,
                                                 destination_blockchain_id)
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
                'unable to get the current bids',
                source_blockchain_id=source_blockchain_id,
                destination_blockchain_id=destination_blockchain_id)
        return bids
