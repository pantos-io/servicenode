import importlib

from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.configuration import get_blockchain_config
from pantos.servicenode.configuration import get_plugin_config
from pantos.servicenode.plugins.base import BidPlugin

_DEFAULT_PLUGIN = 'pantos.servicenode.plugins.bids.ConfigFileBidPlugin'
"""Default plugin to use if no plugin is configured."""

_bid_plugin: BidPlugin | None = None


def get_bid_plugin():
    """Get the bid plugin.

    Returns
    -------
    BidPlugin
        The initialized bid plugin.

    """
    return _bid_plugin


def initialize_plugins(start_worker: bool):
    """Initialize the plugins by loading the code from the specified location
    in the configuration.

    Parameters
    ----------
    start_worker : bool
        Whether to start the celery worker for the bid plugin.

    """
    # Imported here to prevent a circular import
    from pantos.servicenode.business.plugins import execute_bid_plugin
    global _bid_plugin

    _bid_plugin = _import_bid_plugin()
    if start_worker:
        for source_blockchain in Blockchain:
            source_blockchain_config = get_blockchain_config(source_blockchain)
            active = source_blockchain_config['active']
            registered = source_blockchain_config['registered']
            if not active or not registered:
                continue
            execute_bid_plugin.delay(source_blockchain)


def _import_bid_plugin() -> BidPlugin:
    plugin_config = get_plugin_config()
    if plugin_config['bids']['class']:
        class_config = plugin_config['bids']['class'].split('.')
    else:
        class_config = _DEFAULT_PLUGIN.split('.')
    module_name = '.'.join(class_config[:-1])
    class_name = class_config[-1]
    module = importlib.import_module(module_name)
    class_ = getattr(module, class_name)
    return class_()
