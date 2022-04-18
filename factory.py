
from textwrap import wrap
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Optional,
    TypeVar,
)

from .decorators import class_decorator


TargetClass = TypeVar('TargetClass', bound=type)


class RegistryFactory(Generic[TargetClass]):
    """
    A factory that creates instances of different classes depending on the 
    arguments.

    The parameter `T` specifies the superclass of all classes to be registered.
    It can be `None`, if none is to be specified.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, type] = {}


    @class_decorator
    def register(
        self, name: Optional[str] = None
    ) -> Callable[[TargetClass], TargetClass]:
        """
        Decorator to register class to be created.

        The decorated class needs to have an initializer with the following
        signature:
          def __init__(self, parameters: Dict[str, Any]) -> None:
              :param parameters: A `dict` with parameters for the initializer.

        :param name: Name for the class that is to be specified for creation.
          If `None', the name of the class will be used.
        """

        def _wrapper(target: TargetClass) -> TargetClass:
            self._registry[name] = target
            return target
        

        assert name not in self._registry, f"Name ({name}) already registered."
        return _wrapper


    def create(self, name: str, parameters: Dict[str, Any]) -> TargetClass:
        """
        Create an instance of a class registered to this registry.

        :param name: Name for the class specified with `register()`.
        """
        target = self._registry[name]
        return target(parameters)
