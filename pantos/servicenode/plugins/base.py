import abc
import collections.abc
import dataclasses
import typing


class BidPluginError(Exception):
    """Base class for all exceptions in the bid plugin.

    """
    pass  # pragma: no cover


@dataclasses.dataclass
class Bid:
    """Represents a bid for a token transfer from a source blockchain to a
    destination blockchain.

    Attributes
    ----------
    source_blockchain_id : int
        The id of the source blockchain.
    destination_blockchain_id : int
        The id of the destination blockchain.
    fee : int
        The fee in Panini.
    execution_time : int
        The time in seconds it takes to execute the transfer.
    valid_until : int
        The timestamp in seconds until the bid is valid.

    """
    source_blockchain_id: int
    destination_blockchain_id: int
    fee: int
    execution_time: int
    valid_until: int


class BidPlugin(abc.ABC):
    @abc.abstractmethod
    def get_bids(
            self, source_blockchain_id: int, destination_blockchain_id: int,
            **kwargs: typing.Any) \
            -> typing.Tuple[collections.abc.Iterable[Bid], int]:
        """Calculates bid fees for a token transfer from a source blockchain
        to a destination blockchain.

        Parameters
        ----------
        source_blockchain_id : int
            The id of the source blockchain.
        destination_blockchain_id : int
            The id of the destination blockchain.
        **kwargs : typing.Any
            Additional keyword arguments.

        Returns
        ------
        Tuple[collections.abc.Iterable[Bid], int]
            A tuple containing a list of bids and the delay in seconds until
            the next bid calculation.

        Raises
        ------
        BidPluginError
            Raised if a bid for a given source_blockchain_id and
            destination_blockchain_id doesn't exist.

        """
        pass  # pragma: no cover

    @abc.abstractmethod
    def accept_bid(self, bid: Bid, **kwargs: typing.Any) -> bool:
        """Determines if a given bid should be accepted by the service node or
        not. This method should be kept as cheap and fast as possible.

        Parameters
        ----------
        bid : Bid
            A bid to be checked.
        **kwargs : typing.Any
            Additional keyword arguments.

        Returns
        ------
        bool
            True if the bid should be accepted, False otherwise.

        """
        pass  # pragma: no cover
