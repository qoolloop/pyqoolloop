"""
Declares convenient decorators.

.. note:: Cannot decorate fixtures or test functions directly in py.test.
  Arguments(=fixtures) don't get passed in. Please define another function to
  be called from the function of interest.
"""

from collections import OrderedDict
import copy
import datetime
import inspect
import logging
import threading
import time
from typing import (
    Any,
    Callable,
    cast,
    Dict,
    FrozenSet,
    Iterable,
    Optional,
    overload,
    Union,
    Tuple,
    Type,
)

from .genericdecorator import (
    GenericDecorator,
    Target,
    TargetClass,
    TargetFunction,
    TargetFunctionWrapper,
    TargetReturnType,
)


def _through_method(
        target: Callable[..., TargetReturnType],  # TargetFunction,
        instance: TargetClass,  # pylint: disable=unused-argument
        cls: Type[TargetClass],  # pylint: disable=unused-argument
        *args: Any,
        **kwargs: Any
) -> TargetReturnType:
    return target(*args, **kwargs)


def _through_function(
        target: Callable[..., TargetReturnType],  # TargetFunction,
        *args: Any,
        **kwargs: Any
) -> TargetReturnType:
    return target(*args, **kwargs)


def log_calls(
        logger: logging.Logger, log_result: bool = True
) -> GenericDecorator:
    """
    Decorator to log calls to functions

    Can be used on classes to log calls to all its methods.

    :param logger: object to log to
    """

    def log_function(
            target: Callable[..., TargetReturnType],  # TargetFunction,
            *args: Any,
            **kwargs: Any
    ) -> TargetReturnType:
        logger.info("%s args: %r %r" %
                    (target.__name__, args, kwargs))

        result = target(*args, **kwargs)

        if log_result:
            logger.info("%s result: %r" % (target.__name__, result))
            
        return result


    decorator = GenericDecorator(log_function)
    return decorator


def log_calls_on_exception(
        logger: logging.Logger, log_exception: bool = True
) -> GenericDecorator:
    """
    Decorator to log calls to functions, when exceptions are raised

    Can be used on classes to log calls to all its methods.

    :param logger: object to log to
    :param log_exception: True, to log stacktrace and exception
    """

    def log_function(
            target: Callable[..., TargetReturnType],  # TargetFunction,
            *args: Any,
            **kwargs: Any
    ) -> TargetReturnType:
        try:
            result = target(*args, **kwargs)

        except BaseException:
            logger.info("%s args: %r %r" %
                        (target.__name__, args, kwargs))

            if log_exception:
                logger.exception("Exception")

            raise

        return result


    decorator = GenericDecorator(log_function)
    return decorator


# Type hint for `kwargs` is not necessary yet with mypy 0.800
def pass_args(
        target: Target
) -> Target:
    """
    Decorator that passes arguments to the function as a dict as an additional
    argument named `kwargs`

    Useful for logging during debugging.

    No arguments
    """

    def passer_function(
            target: Callable[..., TargetReturnType],  # TargetFunction,
            *args: Any,
            **kwargs: Any
    ) -> TargetReturnType:
        composed_kwargs = copy.copy(kwargs)
        
        arg_names = inspect.signature(target).parameters
        composed_kwargs.update(zip(arg_names, args))
        
        result = target(*args, kwargs=composed_kwargs, **kwargs)
        return result

    
    decorator = GenericDecorator(passer_function)
    return decorator(target)


# not constant
raise_exception_for_deprecated = False  # pylint: disable=invalid-name


def deprecated(
        logger: logging.Logger,
        message: Optional[str] = None,
        raise_exception: Optional[bool] = None
) -> GenericDecorator:
    """
    Used to decorate deprecated functions and classes

    :param logger: Where to log message.
    :param message: Additional message to log.
    :param raise_exception: `True`, to raise exception when function (of class)
      is called.
    """

    def log_function(
            target: Callable[..., TargetReturnType],  # TargetFunction,
            *args: Any,
            **kwargs: Any
    ) -> TargetReturnType:
        message_str = "deprecated function called: %r (%r)" % \
            (target.__name__, target.__module__)

        if message is not None:
            message_str += "\n" + message
        
        logger.warning(message_str)  #TODO: lazy string

        if raise_exception or \
           ((raise_exception is None) and raise_exception_for_deprecated):
            raise DeprecationWarning(message_str)

        result = target(*args, **kwargs)
        return result

    
    decorator = GenericDecorator(log_function)
    return decorator


#TODO: type hint for `attempts` argument added to decorated function
# c.f. https://stackoverflow.com/a/47060298/2400328
# c.f. https://www.python.org/dev/peps/pep-0612/
def retry(
        attempts: int,
        exceptions: Union[
            Type[BaseException], Tuple[Type[BaseException], ...]],
        interval_secs: float = 0.0,
        extra_argument: bool = False
) -> Callable[
    [Callable[..., TargetReturnType]],
    Callable[..., TargetReturnType]
]:  # extra argument may be added to signature
    """
    Used to decorate functions that should be retried if certain exceptions are
    raised

    :param attempts: Maximum number of times the function should be run
    :param exceptions: Rerun the function if these exceptions are raised
    :param interval_secs: Interval between attempts in seconds.
    :param extra_argument: If `True`, an argument named `attempts` is added to
      the function, which overrides the `attempts` value specified by the
      decorator
    """

    def retry_function(
            target: Callable[..., TargetReturnType],  # TargetFunction,
            *args: Any,
            **kwargs: Any) -> TargetReturnType:

        if extra_argument and ('attempts' in kwargs):
            actual_attempts = kwargs['attempts']
            del kwargs['attempts']

        else:
            actual_attempts = attempts
        
        for iteration in range(actual_attempts):
            try:
                return target(*args, **kwargs)

            except exceptions:
                if iteration < actual_attempts - 1:
                    time.sleep(interval_secs)

                else:
                    raise
                # endif
            # endtry

        # exception is not available outside except clause in Python 3
        # https://cosmicpercolator.com/2016/01/13/exception-leaks-in-python-2-and-3/
        raise AssertionError("Unexpected execution")

    
    decorator = GenericDecorator(retry_function)
    return decorator


@overload
def synchronized_on_function(
        __target: TargetFunction,
        *,
        lock_field: str = '__lock',
        dont_synchronize: bool = False
) -> TargetFunction:
    ...

    
@overload
def synchronized_on_function(
        __target: None = None,
        *,
        lock_field: str = '__lock',
        dont_synchronize: bool = False
) -> Callable[[TargetFunction], TargetFunction]:
    # FunctionWrapperFactory[TargetFunction]:
    ...


def synchronized_on_function(
        __target: Optional[Callable[..., TargetReturnType]] = None,  # Optional[TargetFunction]
        *,
        lock_field: str = '__lock',
        dont_synchronize: bool = False  #TODO: Why necessary?
) -> Callable[..., Any]:
# Union[TargetFunction, FunctionWrapperFactory[TargetFunction]]:
#FUTURE: Union doesn't work (mypy 0.800)
# https://github.com/python/mypy/issues/3644
    """
    Used to decorate function that needs thread locking for access

    When called for the first time, this decorator creates a field on
    the function object named by `lock_field`, which holds the lock
    instance for synchronization.

    :param lock_field: The name of the field that holds the lock.
    :param dont_synchronize: If `True`, synchronization will not be performed.
    """
    def _call_function(
            target: Callable[..., TargetReturnType],  # TargetFunction,
            *args: Any,
            **kwargs: Any
    ) -> TargetReturnType:

        lock_holder = target

        lock = getattr(lock_holder, lock_field, None)
        if lock is None:
            lock = threading.RLock()
            setattr(lock_holder, lock_field, lock)

        with lock:
            result = target(*args, **kwargs)

        return result


    if __target and not dont_synchronize:
        return __target
        
    call_function: TargetFunctionWrapper[TargetReturnType] = (
        _call_function if not dont_synchronize
        else _through_function)

    #FUTURE: A little inefficient when dont_synchronize=True
    decorator = GenericDecorator(
        call_function,
        wrapper_for_staticmethod=_through_method,
        wrapper_for_classmethod=_through_method)
    return decorator(__target)


@overload
def synchronized_on_instance(
        __target: None = None, *, lock_field: str = '__lock'
) -> Callable[[Target], Target]:
    # Union[
    #     Callable[[TargetFunction], TargetFunction],
    #     # FunctionWrapperFactory[TargetFunction],
    #     Callable[[Type[TargetClass]], Type[TargetClass]],
    #     # ClassWrapperFactory[TargetClass]
    # ]:
    ...
    

@overload
def synchronized_on_instance(
        __target: Target,
        *,
        lock_field: str = '__lock'
) -> Target:
    ...
    

def synchronized_on_instance(
        __target: Optional[Target] = None,
        *,
        lock_field: str = '__lock'
) -> Any:
# ) -> Union[
#     TargetFunction,
#     Type[TargetClass],
#     FunctionWrapperFactory[TargetFunction],
#     ClassWrapperFactory[TargetClass]
# ]:
#FUTURE: Unions don't work with `TypeVar` (mypy 0.800)
# https://github.com/python/mypy/issues/3644
    """
    Used to decorate instance methods and classes that need thread locking
    for access

    When called for the first time for an instance, this decorator creates
    a field on self named by `lock_field`, which holds the lock instance for
    synchronization.

    :param lock_field: The name of the field that holds the lock.

    .. note::
      `@staticmethod` and `@classmethod` not supported. If put on classes,
      `@staticmethod` and `@classmethod` will be ignored.
    """
    def _call(
            target: Any,  # TargetFunction,
            lock_holder: TargetClass,
            *args: Any,
            **kwargs: Any
    ) -> Any:  # TargetReturnType:
        lock = getattr(lock_holder, lock_field, None)
        if lock is None:
            lock = threading.RLock()
            setattr(lock_holder, lock_field, lock)

        with lock:
            result = target(*args, **kwargs)

        return result


    def _call_when_decorating_method(
            target: Any,  # TargetFunction,
            *args: Any,
            **kwargs: Any
    ) -> Any:  # TargetReturnType:
        lock_holder = args[0]  # `self`
        return _call(target, lock_holder, *args, **kwargs)
    

    def _call_when_decorating_class(
            target: Any,  # TargetFunction,
            instance: TargetClass,
            cls: Type[TargetClass],  # pylint: disable=unused-argument
            *args: Any,
            **kwargs: Any
    ) -> Any:  # TargetReturnType:
        lock_holder = instance
        return _call(target, lock_holder, *args, **kwargs)


    decorator = GenericDecorator(
        _call_when_decorating_method,
        wrapper_for_instancemethod=_call_when_decorating_class,
        wrapper_for_staticmethod=_through_method,
        wrapper_for_classmethod=_through_method)
    return decorator(__target)


#FUTURE:
# def synchronized_on_class(
#         __target: Optional[Type[TargetClass]] = None,
#         *,
#         lock_field: str = '__lock'
# ) -> Union[Type[TargetClass], ClassWrapperFactory[TargetClass]]:
    # Not sure whether locks should be on each subclass or use one for all
    # subclasses -> Should be one for all subclasses, because of how the
    # topmost class needs synchronization.
    #     ...


def _get_signature_values(
        target: Callable[..., TargetReturnType],  # TargetFunction
        args: Iterable[Any],
        kwargs: Dict[str, Any],
        exclude_kw: Iterable[str] = ()
) -> OrderedDict[str, Any]:

    def _bind_arguments(
            target: Callable[..., TargetReturnType],  # TargetFunction,
            args: Iterable[Any],
            kwargs: Dict[str, Any]
    ) -> OrderedDict[str, Any]:
        signature = inspect.signature(target)
        bind = signature.bind(*args, **kwargs)
        bind.apply_defaults()
        return bind.arguments


    def _exclude(
            arguments: OrderedDict[str, Any], exclude_kw: Iterable[str]
    ) -> None:
        for each in exclude_kw:
            del arguments[each]
        # endfor
        

    arguments = _bind_arguments(target, args, kwargs)
    arguments[''] = hash(target)
    _exclude(arguments, exclude_kw)
    return arguments


@overload
def expire_cache(
        __target: TargetFunction,
        *,
        expire_time_secs: float,
        max_entries: Optional[int] = None,
        dont_synchronize: bool = False,
        exclude_kw: Iterable[str] = ()
) -> TargetFunction:
    ...


@overload
def expire_cache(
        __target: None = None,
        *,
        expire_time_secs: float,
        max_entries: Optional[int] = None,
        dont_synchronize: bool = False,
        exclude_kw: Iterable[str] = ()
) -> Callable[[TargetFunction], TargetFunction]:
    # FunctionWrapperFactory[TargetFunction]:
    ...


#TODO: rename `cache` after removing `@keep_cache`
def expire_cache(
    __target: Optional[TargetFunction] = None,
    *,
    expire_time_secs: float,
    max_entries: Optional[int] = None,
    dont_synchronize: bool = False,
    exclude_kw: Iterable[str] = ()
) -> Callable[..., Any]:
# Union[TargetFunction, FunctionWrapperFactory[TargetFunction]]:
#FUTURE: Unions don't work with `TypeVar`. (mypy 0.800)
# https://github.com/python/mypy/issues/3644
    """
    Decorator to cache returned values of a function that are held for at most
    a specified amount of time since the first call
    
    :param expire_time_secs: Keep value for less than this period (seconds)
    :param max_entries: Don't keep more than this number of entries
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
    cache: OrderedDict[
        FrozenSet[Tuple[str, Any]], Tuple[datetime.datetime, Any]
    ] = OrderedDict()


    # Note that synchronization is on `_cached_function()`, not each target
    # function. This is necessary for guarding the cache, but is too much
    # for each target function. More concretely, if `expire_cache` decorates
    # a class, one `cache` is used for all the methods.
    @synchronized_on_function(dont_synchronize=dont_synchronize)
    def _cached_function(
            target: Callable[..., TargetReturnType],  # TargetFunction,
            *args: Any,
            **kwargs: Any
    ) -> TargetReturnType:

        now = datetime.datetime.utcnow()
        
        arguments = _get_signature_values(target, args, kwargs, exclude_kw)
        # https://stackoverflow.com/a/39440252/2400328
        key = frozenset(arguments.items())
        if key in cache:
            stored_time, stored_value = cache[key]

            if (now - stored_time).total_seconds() < expire_time_secs:
                return cast(TargetReturnType, stored_value)

            del cache[key]

        if max_entries and (len(cache) >= max_entries):
            cache.popitem(last=False)

        value: TargetReturnType = target(*args, **kwargs)

        cache[key] = (now, value)

        return value


    decorator = GenericDecorator(_cached_function)
    return decorator(__target)


def extend_with_method(
        __extended_class: Type[TargetClass]
) -> Callable[[TargetFunction], TargetFunction]:
    # FunctionWrapperFactory[TargetFunction]:
    """
    Decorator to add a global function as a method to a class

    :param __extended_class: Class to add method to.

    .. note:: The function needs to have `self` as the first argument.
    """
    #FUTURE: `override=False`

    def _decorator(target: TargetFunction) -> TargetFunction:
        setattr(
            __extended_class,
            target.__name__,
            target)
        return target
        

    return _decorator


def extend_with_static_method(
        __extended_class: Type[TargetClass]
) -> Callable[[TargetFunction], TargetFunction]:
    # FunctionWrapperFactory[TargetFunction]:
    """
    Decorator to add a global function as a static method to a class

    :param __extended_class: Class to add method to.

    .. note:: (function) The decorated function does not need `self` or `cls`
      as arguments.
    """
    #FUTURE: `override=False`

    def _decorator(target: TargetFunction) -> TargetFunction:
        setattr(
            __extended_class,
            target.__name__,
            staticmethod(target))
        return target
        

    return _decorator


def extend_with_class_method(
        __extended_class: Type[TargetClass]
) -> Callable[[TargetFunction], TargetFunction]:
    # FunctionWrapperFactory[TargetFunction]:
    """
    Decorator to add a function as a class method to a class

    :param __extended_class: Class to add method to.

    .. note:: The decorated function needs to have `cls` as the first
      argument.
    """
    #FUTURE: `override=False`

    def _decorator(target: TargetFunction) -> TargetFunction:
        setattr(
            __extended_class,
            target.__name__,
            classmethod(target))
        return target
        

    return _decorator


def extension(
        __extended_class: Type[object]
) -> Callable[[Type[TargetClass]], Type[TargetClass]]:
    # ClassWrapperFactory[TargetClass]:
    """
    Decorator to add all the methods in a class to another class

    :param __extended_class: Class to add methods to.

    .. note:: The decorated class can have regular methods as well as
      `@classmethod` and `@staticmethod`.
    """

    def _decorator(extension_class: Type[TargetClass]) -> Type[TargetClass]:
        assert isinstance(extension_class, type), \
            "@extension is only for decorating classes"
        
        for name, value in extension_class.__dict__.items():
            # not `ismethod()` because not bound
            if inspect.isfunction(value) \
               or isinstance(value, (classmethod, staticmethod)):
                setattr(
                    __extended_class,
                    name,
                    value)

        return extension_class

    return _decorator
