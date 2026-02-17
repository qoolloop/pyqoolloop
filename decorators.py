"""
Declares convenient decorators.

.. note:: Cannot decorate fixtures or test functions directly in py.test.
  Arguments(=fixtures) don't get passed in. Please define another function to
  be called from the function of interest.
"""

from collections import OrderedDict
from collections.abc import Callable, Iterable
import copy
import datetime
from functools import partial, wraps
import inspect
import logging
import threading
import time
from typing import (
    Any,
    cast,
    overload,
)

from .genericdecorator import (
    GenericDecorator,
    TargetClassT,
    TargetFunctionT,
    TargetReturnT,
    TargetT,
)


def _through_method(
    target: Callable[..., TargetReturnT],
    instance: TargetClassT,  # noqa: ARG001
    cls: type[TargetClassT],  # noqa: ARG001
    *args: Any,
    **kwargs: Any,
) -> TargetReturnT:
    return target(*args, **kwargs)


def _through_function(
    target: Callable[..., TargetReturnT],
    *args: Any,
    **kwargs: Any,
) -> TargetReturnT:
    return target(*args, **kwargs)


# FUTURE: Add examples for each decorator.


def function_decorator(target: TargetFunctionT) -> TargetFunctionT:
    """
    Decorate a decorator that decorates functions.

    Does nothing, just annotates.
    """
    return target


def class_decorator(target: TargetFunctionT) -> TargetFunctionT:
    """
    Decorate a decorator that decorates classes.

    Does nothing, just annotates.
    """
    return target


def generic_decorator(target: TargetFunctionT) -> TargetFunctionT:
    """
    Decorate a decorator that decorates both classes and functions.

    Does nothing, just annotates.
    """
    return target


@generic_decorator
def log_calls(
    logger: logging.Logger, *, level: int = logging.INFO, log_result: bool = True
) -> GenericDecorator:
    """
    Log calls to the decorated function.

    Can also decorate classes to log calls to all its methods.

    :param logger: object to log to
    :param level: the level for logging
    :param log_result: whether to log the returned value of the decorated function
    """

    def log_function(
        target: Callable[..., TargetReturnT],
        *args: Any,
        **kwargs: Any,
    ) -> TargetReturnT:
        stack_level = 3

        logger.log(
            level,
            "%s args: %r %r",
            target.__name__,
            args,
            kwargs,
            stacklevel=stack_level,
        )

        result = target(*args, **kwargs)

        if log_result:
            logger.log(
                level, "%s result: %r", target.__name__, result, stacklevel=stack_level
            )

        return result

    decorator = GenericDecorator(log_function)
    return decorator


@generic_decorator
def log_calls_on_exception(
    logger: logging.Logger, *, log_exception: bool = True
) -> GenericDecorator:
    """
    Log calls to the decorated function, when exceptions are raised.

    Can also decorate classes to log calls to all its methods.

    :param logger: object to log to
    :param log_exception: True, to log stacktrace and exception
    """

    def log_function(
        target: Callable[..., TargetReturnT],
        *args: Any,
        **kwargs: Any,
    ) -> TargetReturnT:
        stack_level = 3

        try:
            result = target(*args, **kwargs)

        except BaseException:
            if log_exception:
                logger.exception("Exception", stacklevel=stack_level)

            else:
                logger.error(  # noqa: TRY400
                    "%s args: %r %r",
                    target.__name__,
                    args,
                    kwargs,
                    stacklevel=stack_level,
                )

            raise

        return result

    decorator = GenericDecorator(log_function)
    return decorator


@overload
def pass_args(target: TargetFunctionT) -> TargetFunctionT: ...


@overload
def pass_args(target: type[TargetClassT]) -> type[TargetClassT]: ...


@generic_decorator
def pass_args(
    target: TargetT,
) -> TargetT:
    """
    Call the decorated function with an additional argument named `kwargs`.

    Can also decorate classes so that each method gets the extra argument.

    `kwargs` will be a `dict` having all the arguments set by the caller.

    Useful for logging during debugging.

    No arguments
    """

    def passer_function(
        target: Callable[..., TargetReturnT],
        *args: Any,
        **kwargs: Any,
    ) -> TargetReturnT:
        composed_kwargs = copy.copy(kwargs)

        arg_names = inspect.signature(target).parameters
        composed_kwargs.update(zip(arg_names, args, strict=False))

        result = target(*args, kwargs=composed_kwargs, **kwargs)
        return result

    decorator = GenericDecorator(passer_function)
    return decorator(target)


# not constant
raise_exception_for_deprecated = False


@generic_decorator
def deprecated(
    logger: logging.Logger,
    message: str | None = None,
    *,
    raise_exception: bool | None = None,
) -> GenericDecorator:
    """
    Deprecate a decorated function or class.

    :param logger: Where to log message.
    :param message: Additional message to log.
    :param raise_exception: `True`, to raise exception when function (of class)
      is called.

    .. note:: This decorator doesn't work with `@overrides`, but this shouldn't be a
      problem, because the parent method should be deprecated.
    """

    def log_function(
        target: Callable[..., TargetReturnT],
        *args: Any,
        **kwargs: Any,
    ) -> TargetReturnT:
        message_tuple = (
            "deprecated function called: %r (%r)%s%s",
            target.__name__,
            target.__module__,
            "\n" if message else "",
            message or "",
        )

        logger.warning(*message_tuple)

        if raise_exception or (
            (raise_exception is None) and raise_exception_for_deprecated
        ):
            raise DeprecationWarning(message_tuple[0] % message_tuple[1:])

        result = target(*args, **kwargs)
        return result

    decorator = GenericDecorator(log_function)
    return decorator


@function_decorator
def retry(
    attempts: int,
    exceptions: type[Exception] | tuple[type[Exception], ...],
    *,
    interval_secs: float = 0.0,
    extra_argument: bool = False,
) -> Callable[
    [Callable[..., TargetReturnT]],
    Callable[..., TargetReturnT],
]:  # extra argument may be added to signature
    # FUTURE: Add type hint for `attempts` argument to decorated function
    # c.f. https://stackoverflow.com/a/47060298/2400328
    # c.f. https://www.python.org/dev/peps/pep-0612/
    """
    Add retry attempts to decorated function triggered with exceptions.

    :param attempts: Maximum number of times the function should be run
    :param exceptions: Rerun the function if these exceptions are raised
    :param interval_secs: Interval between attempts in seconds.
    :param extra_argument: If `True`, an argument named `attempts` is added to
      the function, which overrides the `attempts` value specified by the
      decorator
    """

    def decorator(
        target: Callable[..., TargetReturnT],
    ) -> Callable[..., TargetReturnT]:
        @wraps(target)
        def retry_function(
            *args: Any,
            **kwargs: Any,
        ) -> TargetReturnT:
            if extra_argument and ('attempts' in kwargs):
                actual_attempts = kwargs['attempts']
                del kwargs['attempts']

            else:
                actual_attempts = attempts

            for iteration in range(actual_attempts):
                try:
                    return target(*args, **kwargs)

                except exceptions:  # noqa: PERF203
                    if iteration < actual_attempts - 1:
                        time.sleep(interval_secs)

                    else:
                        raise
                    # endif
                # endtry

            # exception is not available outside except clause in Python 3
            # https://cosmicpercolator.com/2016/01/13/exception-leaks-in-python-2-and-3/
            raise AssertionError("Unexpected execution")

        return retry_function

    return decorator


@overload
def synchronized_on_function(
    target: None = None,
    /,
    *,
    lock_field: str = '__lock',
    dont_synchronize: bool = False,
) -> Callable[[TargetFunctionT], TargetFunctionT]:
    # Callable[[type[TargetClassT]], type[TargetClassT]],  # Doesn't work mypy 1.11.1
    ...


@overload
def synchronized_on_function(
    target: TargetFunctionT,
    /,
    *,
    lock_field: str = '__lock',
    dont_synchronize: bool = False,
) -> TargetFunctionT: ...


@overload
def synchronized_on_function(
    target: type[TargetClassT],
    /,
    *,
    lock_field: str = '__lock',
    dont_synchronize: bool = False,
) -> type[TargetClassT]: ...


@generic_decorator
def synchronized_on_function(
    target: TargetT | None = None,
    /,
    *,
    lock_field: str = '__lock',
    dont_synchronize: bool = False,
) -> TargetT | Callable[[TargetT], TargetT]:
    """
    Add synchronization lock to decorated function.

    Can also be used to decorate classes, so that a lock is added to each of
    its methods.

    Used to decorate function that needs thread locking for access

    When called for the first time, this decorator creates a field on
    the function object named `lock_field`, which holds the lock
    instance for synchronization.

    :param lock_field: The name of the field that holds the lock.
    :param dont_synchronize: If `True`, synchronization will not be performed.
      To be used when synchronization needs to be turned on/off depending on
      a variable value. c.f. `@cache`
    """

    def _call_function(
        target: Callable[..., TargetReturnT],
        *args: Any,
        **kwargs: Any,
    ) -> TargetReturnT:
        lock_holder = target

        lock = getattr(lock_holder, lock_field, None)
        if lock is None:
            lock = threading.RLock()
            setattr(lock_holder, lock_field, lock)

        with lock:
            result = target(*args, **kwargs)

        return result

    if target:
        assert not dont_synchronize
        return partial(_call_function, target)

    call_function = _call_function if not dont_synchronize else _through_function

    # FUTURE: A little inefficient when dont_synchronize=True
    decorator = GenericDecorator(
        call_function,
        wrapper_for_staticmethod=_through_method,
        wrapper_for_classmethod=_through_method,
    )
    return decorator(target)


@overload
def synchronized_on_instance(
    target: None = None,
    /,
    *,
    lock_field: str = '__lock',
) -> Callable[[TargetFunctionT], TargetFunctionT]:
    ...
    # Callable[[type[TargetClassT]], type[TargetClassT]],  # Doesn't work mypy 1.11.1


@overload
def synchronized_on_instance(
    target: TargetFunctionT,
    /,
    *,
    lock_field: str = '__lock',
) -> TargetFunctionT: ...


@overload
def synchronized_on_instance(
    target: type[TargetClassT],
    /,
    *,
    lock_field: str = '__lock',
) -> type[TargetClassT]: ...


@generic_decorator
def synchronized_on_instance(
    target: TargetT | None = None,
    /,
    *,
    lock_field: str = '__lock',
) -> TargetT | Callable[[TargetT], TargetT]:
    """
    Add a synchronization lock for calls to the decorated instance method.

    Can also be used to decorate classes to add a synchronization lock to
    methods of the decorated class.

    Used to decorate instance methods and classes that need thread locking
    for access

    When called for the first time for an instance, this decorator creates
    a field on the class instance named `lock_field`, which holds the
    lock instance for synchronization.

    :param lock_field: The name of the field that holds the lock.

    .. note::
      `@staticmethod` and `@classmethod` not supported. If put on classes,
      `@staticmethod` and `@classmethod` will be ignored.
    """

    def _call(
        target: Any,  # TargetFunctionT,  # noqa: ANN401
        lock_holder: object,  # TargetClassT,
        *args: Any,
        **kwargs: Any,
    ) -> Any:  # TargetReturnT:  # noqa: ANN401
        lock = getattr(lock_holder, lock_field, None)
        if lock is None:
            lock = threading.RLock()
            setattr(lock_holder, lock_field, lock)

        with lock:
            result = target(*args, **kwargs)

        return result

    def _call_when_decorating_method(
        target: Any,  # noqa: ANN401
        *args: Any,
        **kwargs: Any,  # TargetFunctionT,
    ) -> Any:  # TargetReturnT:  # noqa: ANN401
        lock_holder = args[0]  # `self`
        return _call(target, lock_holder, *args, **kwargs)

    def _call_when_decorating_class(
        target: Any,  # TargetFunctionT,  # noqa: ANN401
        instance: TargetClassT,
        cls: type[TargetClassT],  # noqa: ARG001
        *args: Any,
        **kwargs: Any,
    ) -> Any:  # TargetReturnT:  # noqa: ANN401
        lock_holder = instance
        return _call(target, lock_holder, *args, **kwargs)

    decorator = GenericDecorator(
        _call_when_decorating_method,
        wrapper_for_instancemethod=_call_when_decorating_class,
        wrapper_for_staticmethod=_through_method,
        wrapper_for_classmethod=_through_method,
    )
    return decorator(target)


# FUTURE:
# def synchronized_on_class(
#         __target: Optional[type[TargetClassT]] = None,
#         *,
#         lock_field: str = '__lock'
# ) -> Union[type[TargetClassT], Callable[[type[TargetClassT]], type[TargetClassT]]]:
# Not sure whether locks should be on each subclass or use one for all
# subclasses -> Should be one for all subclasses, because of how the
# topmost class needs synchronization.
#     ...


def _get_signature_values(
    target: Callable[..., TargetReturnT],
    args: Iterable[Any],
    kwargs: dict[str, Any],
    exclude_kw: Iterable[str] = (),
) -> OrderedDict[str, Any]:
    def _bind_arguments(
        target: Callable[..., TargetReturnT],
        args: Iterable[Any],
        kwargs: dict[str, Any],
    ) -> OrderedDict[str, Any]:
        signature = inspect.signature(target)
        bind = signature.bind(*args, **kwargs)
        bind.apply_defaults()
        return bind.arguments

    def _exclude(arguments: OrderedDict[str, Any], exclude_kw: Iterable[str]) -> None:
        for each in exclude_kw:
            del arguments[each]
        # endfor

    arguments = _bind_arguments(target, args, kwargs)
    arguments[''] = hash(target)
    _exclude(arguments, exclude_kw)
    return arguments


def cache(
    _target: None = None,
    /,
    *,
    expire_time_secs: float,
    max_entries: int | None = None,
    dont_synchronize: bool = False,
    exclude_kw: Iterable[str] = (),
) -> Callable[[TargetT], TargetT]:
    """
    Cache returned values of the decorated function.

    Can also decorate classes to cache returned values for each method.

    :param expire_time_secs: Keep value for less than this period (seconds)
    :param max_entries: Don't keep more than this number of entries.
      If a class is decorated, one cache is held for all methods in the class.
    :param dont_synchronize: `True`, if thread safety is not necessary
    :param exclude_kw: Iterable of argument names to exclude from arguments
      to identify cache data. Cached data is retrieved by taking the previous
      return value from a call to the target function with the same argument
      values except those assigned to argument names in `exclude_kw`.

    .. note:: Argument values for the target function must be hashable.
      Decorate each method, if a separate cache is needed for each method.
    """
    # holds tuples (<time>, <value>)
    cache_storage: OrderedDict[
        frozenset[tuple[str, Any]], tuple[datetime.datetime, Any]
    ] = OrderedDict()

    @synchronized_on_function(dont_synchronize=dont_synchronize)
    def _cached_function(
        target: Callable[..., TargetReturnT],
        *args: Any,
        **kwargs: Any,
    ) -> TargetReturnT:
        # Note that synchronization is on `_cached_function()`, not each target
        # function. This is necessary for guarding the cache, but is too much
        # for each target function. More concretely, if `cache` decorates
        # a class, one `cache` is used for all the methods.

        now = datetime.datetime.now(tz=datetime.timezone.utc)

        arguments = _get_signature_values(target, args, kwargs, exclude_kw)
        # https://stackoverflow.com/a/39440252/2400328
        key = frozenset(arguments.items())
        if key in cache_storage:
            stored_time, stored_value = cache_storage[key]

            if (now - stored_time).total_seconds() < expire_time_secs:
                return cast(TargetReturnT, stored_value)

            del cache_storage[key]

        if max_entries and (len(cache_storage) >= max_entries):
            cache_storage.popitem(last=False)

        value: TargetReturnT = target(*args, **kwargs)

        cache_storage[key] = (now, value)

        return value

    decorator = GenericDecorator(_cached_function)
    return decorator(_target)


@function_decorator
def extend_with_method(
    extended_class: type[TargetClassT],
    /,
) -> Callable[[TargetFunctionT], TargetFunctionT]:
    """
    Add decorated function as an instance method to a class.

    :param extended_class: Class to add method to.

    .. note:: The function needs to have `self` as the first argument.
    """
    # FUTURE: `override=False` Don't allow overrides

    def _decorator(target: TargetFunctionT) -> TargetFunctionT:
        setattr(extended_class, target.__name__, target)
        return target

    return _decorator


@function_decorator
def extend_with_static_method(
    extended_class: type[TargetClassT],
    /,
) -> Callable[[TargetFunctionT], TargetFunctionT]:
    """
    Add decorated function as a static method to a class.

    :param extended_class: Class to add method to.

    .. note:: (function) The decorated function does not need `self` or `cls`
      as arguments.
    """
    # FUTURE: `override=False`

    def _decorator(target: TargetFunctionT) -> TargetFunctionT:
        setattr(extended_class, target.__name__, staticmethod(target))
        return target

    return _decorator


@function_decorator
def extend_with_class_method(
    extended_class: type[TargetClassT],
    /,
) -> Callable[[TargetFunctionT], TargetFunctionT]:
    """
    Add decorated function as a class method to a class.

    :param extended_class: Class to add method to.

    .. note:: The decorated function needs to have `cls` as the first
      argument.
    """
    # FUTURE: `override=False`

    def _decorator(target: TargetFunctionT) -> TargetFunctionT:
        setattr(extended_class, target.__name__, classmethod(target))
        return target

    return _decorator


@class_decorator
def extension(
    extended_class: type[object],
    /,
) -> Callable[[type[TargetClassT]], type[TargetClassT]]:
    # FUTURE: Allow adding superclasses in extension class, including the extended \
    # class
    """
    Add all the methods in the decorated class to another class.

    :param extended_class: Class to add methods to.

    .. note:: The decorated class can have regular methods as well as
      `@classmethod` and `@staticmethod`.

    .. note:: Pylance treats class extensions as not accessed. (v2023.12.1)
    """

    def _decorator(extension_class: type[TargetClassT]) -> type[TargetClassT]:
        assert isinstance(extension_class, type), (
            "@extension is only for decorating classes"
        )

        for name, value in extension_class.__dict__.items():
            # not `ismethod()` because not bound
            if inspect.isfunction(value) or isinstance(
                value, (classmethod, staticmethod)
            ):
                setattr(extended_class, name, value)

        return extension_class

    return _decorator
