"""
Declares features for implementing decorators.

.. note:: Cannot decorate fixtures or test functions directly in py.test.
  Arguments(=fixtures) don't get passed in. Please define another function to
  be called from the function of interest.
"""

from functools import (
    wraps,
)
import inspect
from typing import (
    Any,
    Callable,
    cast,
    Optional,
    overload,
    Protocol,
    Union,
    Type,
    TypeVar,
)

from mypy_extensions import (
    Arg,
    KwArg,
    VarArg,
)


# https://mypy.readthedocs.io/en/stable/generics.html#declaring-decorators
TargetReturnT = TypeVar('TargetReturnT')
"""Return type"""

TargetFunction = TypeVar(
    'TargetFunction', bound=Callable[..., Any])  # TargetReturnType])
"""Type for decorated function"""
#FUTURE: Currently (mypy 0.800) not possible to declare generic `TypeVar`
# https://github.com/python/mypy/issues/8278
# Would need to use Callable[..., TargetReturnType] directly.

TargetClass = TypeVar('TargetClass', bound=object)
"""Type for decorated class"""

Target = TypeVar('Target', Callable[..., Any], Type[object])
"""Type for decorated function or class"""

TargetFunctionWrapper = Callable[
    [Arg(Callable[..., TargetReturnT], 'target'), VarArg(), KwArg()],
    TargetReturnT]  # Callable[[TargetFunction, ...], TargetReturnType]
"""
Generic type for function that calls the decorated function

:param TargetReturnType: Return type of the decorated function.
"""

TargetMethodWrapper = Callable[
    [
        Arg(Callable[..., TargetReturnT], 'target'),
        Arg(TargetClass, 'instance'),
        Arg(Type[TargetClass], 'cls'),
        VarArg(),
        KwArg()
    ],
    TargetReturnT]  # Callable[[TargetFunction, ...], TargetReturnType]
"""
Generic type for function that calls the decorated method

:param TargetReturnType: Return type of the decorated method.
"""

# Alias currently doesn't work https://github.com/python/mypy/issues/8273
FunctionWrapperFactory = Callable[[TargetFunction], TargetFunction]
"""
Type for function that returns a wrapper for a decorated function.

To be used if the wrapped function has the same signature as the target
function.

:param TargetFunction: Type for function that is being decorated.
"""

ClassWrapperFactory = Callable[[Type[TargetClass]], Type[TargetClass]]
"""
Type for function that returns a wrapper for a decorated class.

To be used if the wrapped class has the same methods as the target class.

:param TargetClass: Type for class that is being decorated.
"""


class GenericDecorator:
    """
    A convenience class for creating decorators.

    Decorators created with this can decorate functions and methods.
    If they decorate classes, it will have the same effect as decorating
    each method. Only methods listed in `__dict__` of the class will be
    decorated.

    See implementation of decorators in this module.
    """

    #FUTURE: Type hints probably aren't what they're supposed to be,
    # especially with the use of `TypeVar`
    def __init__(
            self,
            wrapper_for_function: TargetFunctionWrapper[TargetReturnT],
            wrapper_for_instancemethod: Optional[
                TargetMethodWrapper[
                    TargetReturnT, TargetClass]] = None,
            wrapper_for_staticmethod: Optional[
                TargetMethodWrapper[
                    TargetReturnT, TargetClass]] = None,
            wrapper_for_classmethod: Optional[
                TargetMethodWrapper[
                    TargetReturnT, TargetClass]] = None
    ) -> None:
        # noqa: D205,D400,D415
        r"""
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
                target: Callable[..., TargetReturnT],  # TargetFunction,
                instance: TargetClass,  # pylint: disable=unused-argument
                cls: Type[TargetClass],  # pylint: disable=unused-argument
                *args: Any,
                **kwargs: Any
        ) -> TargetReturnT:
            return wrapper_for_function(target, *args, **kwargs)


        self.wrapper_for_function = wrapper_for_function
        self.wrapper_for_instancemethod = wrapper_for_instancemethod or \
            default_wrapper
        self.wrapper_for_staticmethod = wrapper_for_staticmethod or \
            default_wrapper
        self.wrapper_for_classmethod = wrapper_for_classmethod or \
            default_wrapper


    @overload
    def __call__(
            self, target: None
    ) -> Union[
        FunctionWrapperFactory[TargetFunction],
        ClassWrapperFactory[TargetClass]
    ]:
        ...


    @overload
    def __call__(
            self, target: Target) -> Target:
        ...


    def __call__(
            self,
            target: Optional[Target] = None
    ) -> Any:
        #FUTURE: Unions don't work with `TypeVar` (mypy 0.800)
        # https://github.com/python/mypy/issues/3644  # noqa: disable=E265
        # ) -> Union[
        #     TargetFunction,
        #     Type[TargetClass],
        #     FunctionWrapperFactory[TargetFunction],
        #     ClassWrapperFactory[TargetClass]
        # ]:
        """
        Return decorated function or function that decorates a function.

        Return this function itself (`self.__call__`) for decorators
        with arguments.
        Return `self(target)` when there are no arguments.
        """

        def _make_class_decorator(
                target_class: Type[TargetClass]) -> Type[TargetClass]:

            class Descriptor(Protocol):
                """Protocol for descriptor."""

                def __get__(
                        self, instance: TargetClass, owner: Type[TargetClass]
                ) -> TargetFunctionWrapper[TargetReturnT]:
                    ...


            class DescriptorForAllMethods:
                """Descriptor super class."""

                def __init__(
                        self,
                        method: Descriptor,
                        wrapper: TargetMethodWrapper[
                            TargetReturnT, TargetClass]
                ) -> None:
                    self.method = method
                    self.wrapper = wrapper


                def __get__(
                        self, instance: TargetClass, owner: Type[TargetClass]
                ) -> TargetFunctionWrapper[TargetReturnT]:

                    def call_wrapper(
                            *args: Any, **kwargs: Any
                    ) -> TargetReturnT:

                        return self.wrapper(
                            function, instance, owner, *args, **kwargs)

                    # TargetFunction[TargetReturnType]
                    function: Callable[..., TargetReturnT] \
                        = self.method.__get__(instance, owner)
                    return call_wrapper


            class DescriptorForInstanceMethod(DescriptorForAllMethods):
                # pylint: disable=too-few-public-methods
                """Descriptor to be used for instance method."""

                def __init__(
                        self, method: Descriptor,
                ) -> None:
                    super().__init__(
                        method, decorator_self.wrapper_for_instancemethod)


            class DescriptorForStaticmethod(DescriptorForAllMethods):
                # pylint: disable=too-few-public-methods
                """Descriptor to be used for staticmethod."""

                def __init__(
                    self,
                    #FUTURE:  Adding [TargetReturnType] doesn't run yet.
                    method: staticmethod  # type: ignore[type-arg]
                ) -> None:
                    super().__init__(
                        method, decorator_self.wrapper_for_staticmethod)


            class DescriptorForClassmethod(DescriptorForAllMethods):
                # pylint: disable=too-few-public-methods
                """Descriptor to be used for classmethod."""

                def __init__(
                    self,
                    #FUTURE:  Adding [TargetReturnType] doesn't run yet.
                    method: classmethod  # type: ignore[type-arg]
                ) -> None:
                    super().__init__(
                        method, decorator_self.wrapper_for_classmethod)


            for name, value in target_class.__dict__.items():
                # not `ismethod()` because not bound
                if inspect.isfunction(value):
                    descriptor_method = DescriptorForInstanceMethod(value)
                    setattr(target_class, name, descriptor_method)

                elif isinstance(value, staticmethod):
                    descriptor_static = DescriptorForStaticmethod(value)
                    setattr(target_class, name, descriptor_static)

                elif isinstance(value, classmethod):
                    descriptor_class = DescriptorForClassmethod(value)
                    setattr(target_class, name, descriptor_class)
                # endif

            return target_class


        @wraps(cast(Callable[..., TargetReturnT], target))
        def factory_for_target(*args: Any, **kwargs: Any) -> TargetReturnT:
            return cast(  # cast from another TargetReturnType
                TargetReturnT,
                decorator_self.wrapper_for_function(
                    cast(Any, target),  # cast to another TargetReturnType
                    *args,
                    **kwargs)
            )


        if target is None:
            # https://stackoverflow.com/q/653368/2400328
            # @synchronized_on_instance(...) with parentheses
            return self

        decorator_self = self

        if isinstance(target, type):  # pylint: disable=no-else-return
            # Type[TargetClass]
            return _make_class_decorator(target)

        elif callable(target):
            return factory_for_target

        elif isinstance(target, staticmethod):
            # https://stackoverflow.com/a/5345526/2400328
            raise AssertionError("Put decorator after @staticmethod")

        elif isinstance(target, classmethod):
            raise AssertionError("Put decorator after @classmethod")

        else:
            raise AssertionError(
                f"Unsupported target of type: {type(target)!r}\n"
                "(You could have forgotten argument to decorator.)")

        # endif
