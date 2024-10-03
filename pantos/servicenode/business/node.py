"""Business logic for managing the service node itself.

"""
import logging

from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.blockchains.factory import get_blockchain_client
from pantos.servicenode.business.base import Interactor
from pantos.servicenode.business.base import InteractorError
from pantos.servicenode.configuration import config
from pantos.servicenode.configuration import get_blockchain_config

_logger = logging.getLogger(__name__)
"""Logger for this module."""


class NodeInteractorError(InteractorError):
    """Exception class for all node interactor errors.

    """
    pass


class NodeInteractor(Interactor):
    """Interactor for managing the service node itself.

    """
    def update_node_registrations(self) -> None:
        """Update the service node registrations on all supported
        blockchains.

        Raises
        ------
        NodeInteractorError
            If a service node registration cannot be updated.

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
                        blockchain_client.update_node_url(new_node_url)
                elif to_be_registered:
                    is_unbonding = blockchain_client.is_unbonding()
                    if is_unbonding:
                        # Service node was unregistered but the deposit
                        # has not been withdrawn yet
                        blockchain_client.cancel_unregistration()
                    else:
                        # Not yet registered
                        withdrawal_address = blockchain_config[
                            'withdrawal_address']
                        node_url = config['application']['url']
                        node_deposit = blockchain_config['deposit']
                        blockchain_client.register_node(
                            node_url, node_deposit, withdrawal_address)
                elif is_registered:
                    # Not to be registered anymore
                    blockchain_client.unregister_node()
                # Do nothing if neither registered nor to be registered
            except Exception:
                raise NodeInteractorError(
                    'unable to update the service node registration on '
                    '{}'.format(blockchain.name))
