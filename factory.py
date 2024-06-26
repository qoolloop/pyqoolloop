"""Defines classes related to the Factory pattern."""

from types import NoneType
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)

from .decorators import class_decorator, function_decorator

_TargetClassT = TypeVar('_TargetClassT')


class RegistryFactory(Generic[_TargetClassT]):
    """
    A factory that creates instances of different classes based on strings assigned.

    The classes are registered using using `@registry.register`, where
    `registry` is an instance of `RegistryFactory`.

    The parameter `_TargetClassT` specifies the superclass of all classes to be
    registered.
    #FUTURE: However, mypy 1.10.0 cannot catch wrong classes being registered. yet.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, Type[_TargetClassT]] = {}

    @overload
    def register(
        self, argument: Optional[str] = None
    ) -> Callable[[Type[_TargetClassT]], Type[_TargetClassT]]: ...

    @overload
    def register(self, argument: Type[_TargetClassT]) -> Type[_TargetClassT]: ...

    @class_decorator
    def register(
        self, argument: Union[None, str, type] = None
    ) -> Union[
        Callable[[Type[_TargetClassT]], Type[_TargetClassT]], Type[_TargetClassT]
    ]:
        """
        Decorate class to register.

        :param name: Name for the class that is to be specified for creation.
          If omitted, the name of the class will be used.

        Parentheses for this decorator can be omitted.
        """

        def _wrapper(target: Type[_TargetClassT]) -> Type[_TargetClassT]:
            key_name = target.__name__ if name is None else name

            assert (
                key_name not in self._registry
            ), f"Name ({key_name}) already registered."

            self._registry[key_name] = target
            return target

        if isinstance(argument, type):
            target = argument
            name = None
            return _wrapper(target)

        name = argument
        return _wrapper

    def create(
        self, name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> _TargetClassT:
        """
        Create an instance of a class registered to this registry.

        :param name: Name for the class specified with `register()`.
        :param arguments: Key/value pairs to be passed to the initializer as
          arguments. `None` for no arguments.
        :raises: `KeyError`: `name` doesn't exist.
        """
        if arguments is None:
            arguments = {}

        target = self._registry[name]
        return target(**arguments)


_TargetSignature = TypeVar('_TargetSignature')


class FunctionRegistryFactory(Generic[_TargetSignature]):
    """
    A factory that creates instances of calls to functions based on strings assigned.

    The functions/methods are registered using using `@registry.register`, where
    `registry` is an instance of `FunctionRegistryFactory`.

    The parameter `_TargetSignature` specifies the signature of functions/methods to be
    registered.
    """

    def __init__(self) -> None:
        self._registry: Dict[str, _TargetSignature] = {}

    @overload
    def register(  # type: ignore[overload-overlap]
        self, argument: Optional[str] = None
    ) -> Callable[[_TargetSignature], _TargetSignature]: ...

    @overload
    def register(self, argument: _TargetSignature) -> _TargetSignature: ...

    @function_decorator
    def register(
        self, argument: Union[None, str, _TargetSignature] = None
    ) -> Union[Callable[[_TargetSignature], _TargetSignature], _TargetSignature]:
        """
        Decorate function/method to register.

        :param name: Name for the callable that is to be specified for creation.
          If omitted, the name of the function/method will be used.

        Parentheses for this decorator can be omitted.
        """

        def _wrapper(target: _TargetSignature) -> _TargetSignature:
            key_name = target.__name__ if name is None else name  # type: ignore[attr-defined]

            assert (
                key_name not in self._registry
            ), f"Name ({key_name}) already registered."

            self._registry[key_name] = target
            return target

        if isinstance(argument, (str, NoneType)):
            name = argument
            return _wrapper

        target = argument
        name = None
        return _wrapper(target)

    def create(self, name: str) -> _TargetSignature:
        """
        Return callable registered to this registry.

        :param name: Name for the class specified with `register()`.
        :raises: `KeyError`: `name` doesn't exist.
        """
        return self._registry[name]
