"""
Declares features for implementing decorators.

.. note:: Cannot decorate fixtures or test functions directly in py.test.
  Arguments(=fixtures) don't get passed in. Please define another function to
  be called from the function of interest.
"""

from collections.abc import Callable
from functools import (
    wraps,
)
import inspect
from typing import (
    Any,
    Generic,
    Protocol,
    TypeVar,
    cast,
    overload,
)

# https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators
TargetReturnT = TypeVar('TargetReturnT')
"""Return type"""

TargetFunctionT = TypeVar(
    'TargetFunctionT', bound=Callable[..., Any]
)  # TargetReturnT])
"""Type for decorated function"""
# FUTURE: Currently (mypy 0.800) not possible to declare generic `TypeVar`
# https://github.com/python/mypy/issues/8278
# Would need to use Callable[..., TargetReturnT] directly.

TargetClassT = TypeVar('TargetClassT', bound=object)
"""Type for decorated class. It's type is `type[TargetClassT]`."""

TargetClassT_contra = TypeVar('TargetClassT_contra', bound=object, contravariant=True)
"""Contravariant type for decorated class"""

TargetT = TypeVar('TargetT', Callable[..., Any], type)
"""Type for decorated function or class"""


class TargetFunctionWrapper(Protocol[TargetReturnT]):
    """
    Generic type for function that calls the decorated function.

    :param TargetReturnT: Return type of the decorated function.
    """

    # Callable[[TargetFunctionT, ...], TargetReturnT]
    def __call__(  # noqa: D102  # D105 doesn't seem to work here
        self, target: Callable[..., TargetReturnT], *vals: Any, **kwargs: Any
    ) -> TargetReturnT: ...


class TargetMethodWrapper(Protocol, Generic[TargetReturnT, TargetClassT_contra]):
    """
    Generic type for function that calls the decorated method.

    :param TargetReturnT: Return type of the decorated method.
    """

    # Callable[[TargetFunctionT, ...], TargetReturnT]
    def __call__(  # noqa: D102  # D105 doesn't seem to work here
        self,
        target: Callable[..., TargetReturnT],
        instance: TargetClassT_contra,
        cls: type[TargetClassT_contra],
        *vals: Any,
        **kwargs: Any,
    ) -> TargetReturnT: ...


class GenericDecorator:
    r"""
    A convenience class for creating decorators.

    Decorators created with this can decorate functions and methods.
    If they decorate classes, it will have the same effect as decorating
    each method. Only methods listed in `__dict__` of the class will be
    decorated.

    See implementation of decorators in this module.

    :param wrapper_for_function:
        |   (callable(target, \*args, \**kwargs))
        | Function to be called when decorating a regular function or method.
        | `target` will have the following signature:
        |   callable(\*args, \**kwargs)

    :param wrapper_for_instancemethod:
        |   (callable(target, instance, cls, \*args, \**kwargs))
        | Function to be called when decorating an instance method.
        | `target` will have the following signature:
        |   callable(\*args, \**kwargs)
        | If `None`, `wrapper_for_function()` will be called with
        | appropriate arguments.

    :param wrapper_for_staticmethod:
        |   (callable(target, instance, cls, \*args, \**kwargs))
        | Function to be called when decorating a static method.
        | `target` will have the following signature:
        |   callable(\*args, \**kwargs)
        | If `None`, `wrapper_for_function()` will be called with
        | appropriate arguments.

    :param wrapper_for_classmethod:
        |   (callable(target, instance, cls, \*args, \**kwargs))
        | Function to be called when decorating a class method.
        | `target` will have the following signature:
        |   callable(\*args, \**kwargs)
        | If `None`, `wrapper_for_function()` will be called with
        | appropriate arguments.

    .. note::
        `wrapper_for_instancemethod`, `wrapper_for_staticmethod` and
        `wrapper_for_classmethod` are only used for class decorators.
    """

    # FUTURE: Type hints probably aren't what they're supposed to be,
    # especially with the use of `TypeVar`
    def __init__(
        self,
        wrapper_for_function: TargetFunctionWrapper[TargetReturnT],
        wrapper_for_instancemethod: (
            TargetMethodWrapper[TargetReturnT, TargetClassT] | None
        ) = None,
        wrapper_for_staticmethod: (
            TargetMethodWrapper[TargetReturnT, TargetClassT] | None
        ) = None,
        wrapper_for_classmethod: (
            TargetMethodWrapper[TargetReturnT, TargetClassT] | None
        ) = None,
    ) -> None:
        # Attempt to use this class also as a context manager (for use with
        # `with` statements) has been abandoned, because:
        # - It is not possible to write loops with context managers.

        # Attempt to use this class also as a generator (for use with `for`
        # loops instead of `with` statements) has been abandoned, because:
        # - Exception handling with generators is error-prone.
        #   (Need to use throw()
        #    https://www.python.org/dev/peps/pep-0342/#id9 )
        # - try-catch is necessary to relay caught exceptions to the generator,
        #   but the boilerplate is cumbersome, and can be concisely written
        #   by extracting a function and decorating it.

        def default_wrapper(
            target: Callable[..., TargetReturnT],
            instance: TargetClassT,  # noqa: ARG001
            cls: type[TargetClassT],  # noqa: ARG001
            *args: Any,
            **kwargs: Any,
        ) -> TargetReturnT:
            return wrapper_for_function(target, *args, **kwargs)

        self.wrapper_for_function = wrapper_for_function
        self.wrapper_for_instancemethod: TargetMethodWrapper[
            TargetReturnT, TargetClassT
        ] = wrapper_for_instancemethod or default_wrapper
        self.wrapper_for_staticmethod: TargetMethodWrapper[
            TargetReturnT, TargetClassT
        ] = wrapper_for_staticmethod or default_wrapper
        self.wrapper_for_classmethod: TargetMethodWrapper[
            TargetReturnT, TargetClassT
        ] = wrapper_for_classmethod or default_wrapper

    def _make_class_decorator(  # noqa: C901
        self,
        target_class: type[TargetClassT],
    ) -> type[TargetClassT]:
        decorator_self = self

        class Descriptor(Protocol):
            """Protocol for descriptor."""

            def __get__(
                self, instance: TargetClassT, owner: type[TargetClassT]
            ) -> TargetFunctionWrapper[Any]: ...  # TargetReturnT

        class DescriptorForAllMethods:
            """Descriptor super class."""

            def __init__(
                self,
                method: Descriptor,
                wrapper: TargetMethodWrapper[Any, TargetClassT],  # TargetReturnT
            ) -> None:
                self.method = method
                self.wrapper = wrapper

            def __get__(
                self, instance: TargetClassT, owner: type[TargetClassT]
            ) -> TargetFunctionWrapper[Any]:  # TargetReturnT
                def call_wrapper(
                    *args: Any, **kwargs: Any
                ) -> Any:  # TargetReturnT  # noqa: ANN401
                    return self.wrapper(function, instance, owner, *args, **kwargs)

                # TargetFunction[TargetReturnT]
                function = self.method.__get__(instance, owner)
                return call_wrapper

        class DescriptorForInstanceMethod(DescriptorForAllMethods):
            """Descriptor to be used for instance method."""

            def __init__(
                self,
                method: Descriptor,
            ) -> None:
                super().__init__(
                    method,
                    cast(
                        TargetMethodWrapper[Any, TargetClassT],
                        decorator_self.wrapper_for_instancemethod,
                    ),
                )

        class DescriptorForStaticmethod(DescriptorForAllMethods):
            """Descriptor to be used for staticmethod."""

            def __init__(
                self,
                # FUTURE:  Adding [TargetReturnT] doesn't run yet.
                method: staticmethod,  # type: ignore[type-arg]
            ) -> None:
                super().__init__(
                    # `staticmethod` is descriptor
                    method,  # type: ignore[pylance, unused-ignore]  # v2024.2.1
                    cast(
                        TargetMethodWrapper[Any, TargetClassT],
                        decorator_self.wrapper_for_staticmethod,
                    ),
                )

        class DescriptorForClassmethod(DescriptorForAllMethods):
            """Descriptor to be used for classmethod."""

            def __init__(
                self,
                # FUTURE:  Adding [TargetReturnT] doesn't run yet.
                method: classmethod,  # type: ignore[type-arg]
            ) -> None:
                super().__init__(
                    # `classmethod` is descriptor
                    method,  # type: ignore[pylance, unused-ignore] # v2024.2.1
                    cast(
                        TargetMethodWrapper[Any, TargetClassT],
                        decorator_self.wrapper_for_classmethod,
                    ),
                )

        for name, value in target_class.__dict__.items():
            # not `ismethod()` because not bound
            if inspect.isfunction(value):
                descriptor_method = DescriptorForInstanceMethod(
                    # `FunctionType` is descriptor
                    value  # type: ignore[pylance, unused-ignore] # v2024.2.1
                )
                setattr(target_class, name, descriptor_method)

            elif isinstance(value, staticmethod):
                descriptor_static = DescriptorForStaticmethod(value)
                setattr(target_class, name, descriptor_static)

            elif isinstance(value, classmethod):
                descriptor_class = DescriptorForClassmethod(value)
                setattr(target_class, name, descriptor_class)
            # endif

        return target_class

    @overload
    def __call__(self, target: None) -> Callable[[TargetT], TargetT]: ...

    @overload
    def __call__(self, target: TargetFunctionT) -> TargetFunctionT: ...

    @overload
    def __call__(self, target: type[TargetClassT]) -> type[TargetClassT]: ...

    def __call__(
        self,
        target: Callable[..., TargetReturnT] | type[TargetClassT] | None = None,
    ) -> TargetFunctionT | type[TargetClassT] | Callable[[TargetT], TargetT]:
        """
        Return decorated function or function that decorates a function.

        Return this function itself (`self.__call__`) for decorators
        with arguments.
        Return `self(target)` when there are no arguments.
        """

        @wraps(target)  # type: ignore[arg-type]  # mypy: 1.8
        def factory_for_target(
            *args: Any, **kwargs: Any
        ) -> Any:  # TargetReturnT:  # noqa: ANN401
            return cast(  # cast from another TargetReturnT
                Any,  # TargetReturnT,
                decorator_self.wrapper_for_function(
                    cast(Any, target),
                    *args,
                    **kwargs,  # cast to another TargetReturnT
                ),
            )

        if target is None:
            # https://stackoverflow.com/q/653368/2400328
            # @synchronized_on_instance(...) with parentheses
            return self

        decorator_self = self

        if isinstance(target, type):
            # type[TargetClassT]

            return self._make_class_decorator(cast(type[TargetClassT], target))

        if isinstance(target, staticmethod):
            # https://stackoverflow.com/a/5345526/2400328
            raise AssertionError("Put decorator after @staticmethod")  # noqa: TRY004

        if isinstance(target, classmethod):
            raise AssertionError("Put decorator after @classmethod")  # noqa: TRY004

        if callable(target):
            return factory_for_target  # type: ignore[pylance, unused-ignore] # v2024.2.1

        msg = f"Unsupported target of type: {type(target)!r}\n"
        raise AssertionError(msg)
