"""Business logic for managing the service node itself.

"""
import logging
import urllib.parse

from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.blockchains.base import BlockchainClient
from pantos.servicenode.blockchains.factory import get_blockchain_client
from pantos.servicenode.business.base import Interactor
from pantos.servicenode.business.base import InteractorError
from pantos.servicenode.configuration import config
from pantos.servicenode.configuration import get_blockchain_config

_VALID_NODE_URL_SCHEMES = ['http', 'https']

_logger = logging.getLogger(__name__)
"""Logger for this module."""


class NodeInteractorError(InteractorError):
    """Exception class for all node interactor errors.

    """
    pass


class NodeInteractor(Interactor):
    """Interactor for managing the service node itself.

    """
    @classmethod
    def get_error_class(cls) -> type[InteractorError]:
        # Docstring inherited
        return NodeInteractorError

    def update_node_registrations(self) -> None:
        """Update the service node registrations on all supported
        blockchains.

        Raises
        ------
        InvalidUrlError
            If the configured service node URL is invalid.
        InvalidAmountError
            If the configured service node deposit is less than the
            Pantos Hub's minimum service node deposit or greater than
            the service node's own PAN token balance.
        InvalidBlockchainAddressError
            If the configured withdrawal address is invalid.
        NodeInteractorError
            If a service node registration cannot be updated for any
            other reason.

        """
        for blockchain in Blockchain:
            _logger.info('updating the service node registration on '
                         '{}'.format(blockchain.name))
            try:
                blockchain_config = get_blockchain_config(blockchain)
                if not blockchain_config['active']:
                    continue
                to_be_registered = blockchain_config['registered']
                blockchain_client = get_blockchain_client(blockchain)
                is_registered = blockchain_client.is_node_registered()
                if to_be_registered and is_registered:
                    old_node_url = blockchain_client.read_node_url()
                    new_node_url = config['application']['url']
                    if old_node_url != new_node_url:
                        self.__validate_node_url(new_node_url)
                        blockchain_client.update_node_url(new_node_url)
                elif to_be_registered:
                    is_unbonding = blockchain_client.is_unbonding()
                    if is_unbonding:
                        # Service node was unregistered but the deposit
                        # has not been withdrawn yet
                        blockchain_client.cancel_unregistration()
                    else:
                        # Not yet registered
                        node_url = config['application']['url']
                        node_deposit = blockchain_config['deposit']
                        withdrawal_address = blockchain_config[
                            'withdrawal_address']
                        self.__validate_node_url(node_url)
                        self.__validate_node_deposit(blockchain_client,
                                                     node_deposit)
                        self.__validate_withdrawal_address(
                            blockchain_client, withdrawal_address)
                        blockchain_client.register_node(
                            node_url, node_deposit, withdrawal_address)
                elif is_registered:
                    # Not to be registered anymore
                    blockchain_client.unregister_node()
                # Do nothing if neither registered nor to be registered
            except NodeInteractorError:
                raise
            except Exception:
                raise self._create_error(
                    'unable to update a service node registration',
                    blockchain=blockchain)

    def __validate_node_deposit(self, blockchain_client: BlockchainClient,
                                node_deposit: int) -> None:
        minimum_deposit = blockchain_client.read_minimum_deposit()
        own_pan_balance = blockchain_client.read_own_pan_balance()
        if node_deposit < minimum_deposit or node_deposit > own_pan_balance:
            raise self._create_invalid_amount_error(
                node_deposit=node_deposit, minimum_deposit=minimum_deposit,
                own_pan_balance=own_pan_balance)

    def __validate_node_url(self, node_url: str) -> None:
        try:
            parse_result = urllib.parse.urlparse(node_url)
        except ValueError:
            raise self._create_invalid_url_error(node_url=node_url)
        is_scheme_valid = parse_result.scheme in _VALID_NODE_URL_SCHEMES
        is_netloc_valid = len(parse_result.netloc) > 0
        if not is_scheme_valid or not is_netloc_valid:
            raise self._create_invalid_url_error(node_url=node_url)

    def __validate_withdrawal_address(self,
                                      blockchain_client: BlockchainClient,
                                      withdrawal_address: str) -> None:
        if not blockchain_client.is_valid_address(withdrawal_address):
            raise self._create_invalid_blockchain_address_error(
                withdrawal_address=withdrawal_address)
