"""Base classes for all business logic interactors and errors.

"""
import typing

from pantos.common.exceptions import ErrorCreator

from pantos.servicenode.exceptions import ServiceNodeError


class InteractorError(ServiceNodeError):
    """Base exception class for all interactor errors.

    """
    pass


class InvalidAmountError(InteractorError):
    """Exception to be raised if an amount is invalid.

    """
    def __init__(self, **kwargs: typing.Any):
        # Docstring inherited
        super().__init__('invalid amount', **kwargs)


class InvalidBlockchainAddressError(InteractorError):
    """Exception to be raised if a blockchain address is invalid.

    """
    def __init__(self, **kwargs: typing.Any):
        # Docstring inherited
        super().__init__('invalid blockchain address', **kwargs)


class InvalidUrlError(InteractorError):
    """Exception to be raised if a URL is invalid.

    """
    def __init__(self, **kwargs: typing.Any):
        # Docstring inherited
        super().__init__('invalid URL', **kwargs)


class Interactor(ErrorCreator[InteractorError]):
    """Base class for all interactors.

    """
    def _create_invalid_amount_error(self,
                                     **kwargs: typing.Any) -> InteractorError:
        return self._create_error(specialized_error_class=InvalidAmountError,
                                  **kwargs)

    def _create_invalid_blockchain_address_error(
            self, **kwargs: typing.Any) -> InteractorError:
        return self._create_error(
            specialized_error_class=InvalidBlockchainAddressError, **kwargs)

    def _create_invalid_url_error(self,
                                  **kwargs: typing.Any) -> InteractorError:
        return self._create_error(specialized_error_class=InvalidUrlError,
                                  **kwargs)
