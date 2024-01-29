"""Base classes for all business logic interactors and errors.

"""
import abc

from pantos.servicenode.exceptions import ServiceNodeError


class InteractorError(ServiceNodeError):
    """Base exception class for all interactor errors.

    """
    pass


class Interactor(abc.ABC):
    """Base class for all interactors.

    """
    pass
