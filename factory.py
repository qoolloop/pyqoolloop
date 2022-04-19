
from textwrap import wrap
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Type,
    TypeVar,
    Union,
)

from .decorators import class_decorator


_TargetClass = TypeVar('_TargetClass')


class RegistryFactory(Generic[_TargetClass]):
    """
    A factory that creates instances of different classes depending on the 
    arguments.

    The parameter `_TargetClass` specifies the superclass of all classes to be 
    registered.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, type] = {}


    @class_decorator
    def register(
        self, argument: Union[None, str, type] = None
    ) -> Callable[[Type[_TargetClass]], Type[_TargetClass]]:
        """
        Decorator to register class to be created.

        The decorated class needs to have an initializer with the following
        signature:
          def __init__(self, parameters: Dict[str, Any]) -> None:
              :param parameters: A `dict` with parameters for the initializer.

        :param name: Name for the class that is to be specified for creation.
          If omitted, the name of the class will be used.

        Parentheses for this decorator can be omitted.
        """

        def _wrapper(target: Type[_TargetClass]) -> Type[_TargetClass]:
            key_name = target.__name__ if name is None else name

            assert key_name not in self._registry, \
                f"Name ({key_name}) already registered."

            self._registry[key_name] = target
            return target
        
        if isinstance(argument, type):
            target = argument
            name = None
            return _wrapper(target)

        name = argument
        return _wrapper


    def create(self, name: str, arguments: Dict[str, Any]) -> _TargetClass:
        """
        Create an instance of a class registered to this registry.

        :param name: Name for the class specified with `register()`.
        :param arguments: Key/value pairs to be passed to the initializer as
          arguments.
        """
        target = self._registry[name]
        return target(**arguments)
