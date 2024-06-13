"""Module for loading, validating, and accessing the Service Node's
configuration.

"""
import itertools
import typing

from pantos.common.blockchains.base import MIN_ADAPTABLE_FEE_INCREASE_FACTOR
from pantos.common.blockchains.enums import Blockchain
from pantos.common.configuration import Config
from pantos.common.logging import LogFormat

_DEFAULT_FILE_NAME: typing.Final[str] = 'service-node-config.yml'
"""Default configuration file name."""

config = Config(_DEFAULT_FILE_NAME)
"""Singleton object holding the configuration values."""

_VALIDATION_SCHEMA_BLOCKCHAIN = {
    'type': 'dict',
    'schema': {
        'active': {
            'type': 'boolean',
            'default': True
        },
        'registered': {
            'type': 'boolean',
            'default': True
        },
        'unstaking_address': {
            'type': 'string',
            'required': True,
            'empty': False
        },
        'private_key': {
            'type': 'string',
            'required': True,
            'empty': False,
            'coerce': 'load_if_file'
        },
        'private_key_password': {
            'type': 'string',
            'required': True,
            'empty': False
        },
        'provider': {
            'type': 'string',
            'required': True
        },
        'fallback_providers': {
            'type': 'list',
            'required': False,
            'schema': {
                'type': 'string',
            }
        },
        'provider_timeout': {
            'type': 'integer',
            'nullable': True,
            'default': None
        },
        'average_block_time': {
            'type': 'integer',
            'required': True
        },
        'chain_id': {
            'type': 'integer',
            'required': True
        },
        'hub': {
            'type': 'string',
            'required': True
        },
        'forwarder': {
            'type': 'string',
            'required': True
        },
        'pan_token': {
            'type': 'string',
            'required': True
        },
        'confirmations': {
            'type': 'integer',
            'required': True
        },
        'min_adaptable_fee_per_gas': {
            'type': 'integer',
            'required': True
        },
        'max_total_fee_per_gas': {
            'type': 'integer'
        },
        'adaptable_fee_increase_factor': {
            'type': 'float',
            'min': MIN_ADAPTABLE_FEE_INCREASE_FACTOR,
            'required': True
        },
        'blocks_until_resubmission': {
            'type': 'integer',
            'required': True
        },
        'stake': {
            'type': 'integer',
            'required': True
        }
    }
}
"""Schema for validating a blockchain entry in the configuration file."""

_VALIDATION_SCHEMA_LOG = {
    'type': 'dict',
    'schema': {
        'format': {
            'type': 'string',
            'required': True,
            'allowed': [log_format.name.lower() for log_format in LogFormat]
        },
        'console': {
            'type': 'dict',
            'required': True,
            'schema': {
                'enabled': {
                    'type': 'boolean',
                    'required': True
                }
            }
        },
        'file': {
            'type': 'dict',
            'required': True,
            'schema': {
                'enabled': {
                    'type': 'boolean',
                    'required': True
                },
                'name': {
                    'type': 'string',
                    'required': True,
                    'empty': False
                },
                'max_bytes': {
                    'type': 'integer',
                    'required': True
                },
                'backup_count': {
                    'type': 'integer',
                    'required': True
                }
            }
        }
    }
}
"""Schema for validating a log entry in the configuration file."""

_VALIDATION_SCHEMA = {
    'application': {
        'type': 'dict',
        'schema': {
            'debug': {
                'type': 'boolean',
                'default': False
            },
            'host': {
                'type': 'string',
                'empty': False,
                'required': True
            },
            'port': {
                'type': 'integer',
                'min': 0,
                'required': True
            },
            'ssl_certificate': {
                'type': 'string',
                'dependencies': 'ssl_private_key',
                'empty': False
            },
            'ssl_private_key': {
                'type': 'string',
                'dependencies': 'ssl_certificate',
                'empty': False
            },
            'url': {
                'type': 'string',
                'required': True,
                'empty': False
            },
            'log': _VALIDATION_SCHEMA_LOG
        }
    },
    'database': {
        'type': 'dict',
        'schema': {
            'url': {
                'type': 'string',
                'required': True,
                'empty': False
            },
            'pool_size': {
                'type': 'integer',
                'required': True
            },
            'max_overflow': {
                'type': 'integer',
                'required': True
            },
            'echo': {
                'type': 'boolean',
                'default': False
            },
            'alembic_config': {
                'type': 'string',
                'required': True,
                'empty': False
            },
            'apply_migrations': {
                'type': 'boolean',
                'default': False,
            }
        }
    },
    'celery': {
        'type': 'dict',
        'schema': {
            'broker': {
                'type': 'string',
                'required': True,
                'empty': False
            },
            'backend': {
                'type': 'string',
                'required': True,
                'empty': False
            },
            'log': _VALIDATION_SCHEMA_LOG
        }
    },
    'signer': {
        'type': 'dict',
        'schema': {
            'pem': {
                'type': 'string',
                'required': True,
                'coerce': 'load_if_file'
            },
            'pem_password': {
                'type': 'string',
                'required': True
            }
        }
    },
    'plugins': {
        'type': 'dict',
        'schema': {
            'bids': {
                'type': 'dict',
                'schema': {
                    'class': {
                        'type': 'string',
                    },
                    'arguments': {
                        'type': 'dict',
                        'valuesrules': {
                            'type': 'string'
                        },
                    }
                }
            },
        },
    },
    'tasks': {
        'type': 'dict',
        'schema': {
            'confirm_transfer': {
                'type': 'dict',
                'schema': {
                    'interval': {
                        'type': 'integer',
                        'required': True
                    },
                    'retry_interval_after_error': {
                        'type': 'integer',
                        'required': True
                    }
                }
            },
            'execute_transfer': {
                'type': 'dict',
                'schema': {
                    'retry_interval_after_error': {
                        'type': 'integer',
                        'required': True
                    }
                }
            }
        }
    },
    'blockchains': {
        'type': 'dict',
        'schema': dict(
            zip([b.name.lower() for b in Blockchain],
                itertools.repeat(_VALIDATION_SCHEMA_BLOCKCHAIN)))
    }
}
"""Schema for validating the configuration file."""


def get_blockchain_config(blockchain: Blockchain) -> \
        typing.Dict[str, typing.Any]:
    """Get a blockchain-specific configuration dictionary.

    Parameters
    ----------
    blockchain : Blockchain
        The blockchain to get the configuration for.

    Returns
    -------
    dict
        The blockchain-specific configuration.

    """
    return config['blockchains'][blockchain.name.lower()]


def get_signer_config() -> typing.Dict[str, typing.Any]:
    """Get the signer information, like path to pem file and
    password.

    Returns
    -------
    dict
        The signer specific configuration.

    """
    return config['signer']


def get_plugin_config() -> typing.Dict[str, typing.Any]:
    """Get the plugins information.

    Returns
    -------
    dict
        The plugins specific configuration.

    """
    return config['plugins']


def load_config(file_path: typing.Optional[str] = None,
                reload: bool = True) -> None:
    """Load the configuration from a configuration file.

    Parameters
    ----------
    file_path : str or None
        The path to the configuration file (typical configuration file
        locations are searched if none is specified).
    reload : bool
        If True, the configuration is also loaded if it was already
        loaded before.

    Raises
    ------
    pantos.common.configuration.ConfigError
        If the configuration cannot be loaded (e.g. due to an invalid
        configuration file).

    See Also
    --------
    Config.load

    """
    if reload or not config.is_loaded():
        config.load(_VALIDATION_SCHEMA, file_path)
