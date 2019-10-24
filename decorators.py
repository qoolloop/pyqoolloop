from builtins import range
from collections import OrderedDict
import copy
import datetime
import funcsigs
from functools import (
    wraps,
)
import inspect
import threading
import time


"""
Cannot decorate fixtures or test functions directly in py.test.
Arguments(=fixtures) don't get passed in. Please define another function to
be called from the function of interest.
"""

#TODO: Drop support for Python 2


def _through_classmethod(target, cls, *args, **kwargs):
    return target(*args, **kwargs)


def _through_staticmethod(target, *args, **kwargs):
    return target(*args, **kwargs)


class FunctionDecorator:

    def __init__(self, called_function,
                 function_for_staticmethod=None,
                 function_for_classmethod=None):
        """
        A convenience class for creating decorators

        Decorators created with this can decorate functions and methods.
        If they decorate classes, it will have the same effect as decorating
        each method. Only methods listed in __dict__ of the class will be
        decorated.

        Arguments:
          called_function -- (callable(target, *args, **kwargs))
            target -- callable(*args, **kwargs)
          function_for_staticmethod -- (callable(target, cls, *args, **kwargs))
            target -- callable(*args, **kwargs)
          function_for_classmethod -- (callable(target, cls, *args, **kwargs))
            target -- callable(*args, **kwargs)

        Notes:
          function_for_staticmethod and function_for_classmethod are only
          used for class decorators
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

        def default_function(target, cls, *args, **kwargs):
            return called_function(target, *args, **kwargs)

        
        self.called_function = called_function
        self.function_for_staticmethod = function_for_staticmethod or \
            default_function
        self.function_for_classmethod = function_for_classmethod or \
            default_function


    def generic_decorator(self, target):

        @wraps(target)
        def called_function(*args, **kwargs):
            return decorator_self.called_function(target, *args, **kwargs)


        def _make_class_decorator(target_class):

            class DescriptorForStaticmethod(object):

                def __init__(self, method):
                    self.method = method


                def __get__(self, instance, owner):

                    def called_function(*args, **kwargs):
                        function = self.method.__get__(instance, owner)
                        return decorator_self.function_for_staticmethod(
                            function, owner, *args, **kwargs)

                    return called_function


            class DescriptorForClassmethod(object):

                def __init__(self, method):
                    self.method = method


                def __get__(self, instance, owner):

                    def called_function(*args, **kwargs):
                        function = self.method.__get__(instance, owner)
                        return decorator_self.function_for_classmethod(
                            function, owner, *args, **kwargs)

                    return called_function


            for name, value in target_class.__dict__.items():
                if inspect.isfunction(value):
                    # These are actually methods
                    setattr(target_class, name, self.generic_decorator(value))

                elif isinstance(value, staticmethod):
                    descriptor = DescriptorForStaticmethod(value)
                    setattr(target_class, name, descriptor)

                elif isinstance(value, classmethod):
                    descriptor = DescriptorForClassmethod(value)
                    setattr(target_class, name, descriptor)
                # endif

            return target_class
            

        if target is None:
            # https://stackoverflow.com/q/653368/2400328
            # @synchronized_on_instance(...) with parentheses
            return self.generic_decorator

        decorator_self = self

        if isinstance(target, type):
            return _make_class_decorator(target)

        elif callable(target):
            return called_function

        elif isinstance(target, staticmethod):
            # https://stackoverflow.com/a/5345526/2400328
            assert False, "Put decorator after @staticmethod"

        elif isinstance(target, classmethod):
            assert False, "Put decorator after @classmethod"

        else:
            assert False, \
                "Unsupported target of type: %r\n" % type(target) + \
                "(You could have forgotten argument to decorator.)"
        # endif


def log_calls(logger, log_result=True):
    """
    Decorator to log calls to functions

    Can be used on classes to log calls to all its methods.

    Argument:
    logger -- (logging.Logger) object to log to
    """

    def log_function(target, *args, **kwargs):
        logger.info("%s args: %r %r" %
                    (target.__name__, args, kwargs))

        result = target(*args, **kwargs)

        if log_result:
            logger.info("%s result: %r" % (target.__name__, result))
            
        return result


    decorator = FunctionDecorator(log_function)
    return decorator.generic_decorator


def log_calls_on_exception(logger, log_exception=True):
    """
    Decorator to log calls to functions, when exceptions are raised

    Can be used on classes to log calls to all its methods.

    Argument:
    logger -- (logging.Logger) object to log to
    log_exception -- (bool) True, to log stacktrace and exception
    disable -- (bool) True, to disable logging. To be used in test cases.
    """

    def log_function(target, *args, **kwargs):
        try:
            result = target(*args, **kwargs)

        except Exception as e:
            logger.info("%s args: %r %r" %
                        (target.__name__, args, kwargs))

            if log_exception:
                logger.exception("Exception")

            raise

        return result


    decorator = FunctionDecorator(log_function)
    return decorator.generic_decorator


def pass_args(target):
    """
    Decorator that passes arguments to the function as a dict as an additional
    argument named `kwargs`

    Useful for logging during debugging.

    No arguments
    """

    def passer_function(target, *args, **kwargs):
        composed_kwargs = copy.copy(kwargs)
        
        arg_names = funcsigs.signature(target).parameters
        composed_kwargs.update(zip(arg_names, args))
        
        result = target(*args, kwargs=composed_kwargs, **kwargs)
        return result

    
    decorator = FunctionDecorator(passer_function)
    return decorator.generic_decorator(target)


raise_exception_for_deprecated = False


def deprecated(logger, message=None, raise_exception=None):
    """
    Used to decorate deprecated functions and classes

    Arguments:
    logger -- (Logger) where to log message
    message -- (str) additional message to log
    raise_exception -- (bool) True, to raise exception when function (of class)
      is called
    """

    def log_function(target, *args, **kwargs):
        message_str = "deprecated function called: %r (%r)" % \
            (target.__name__, target.__module__)

        if message is not None:
            message_str += "\n" + message
        
        logger.warning(message_str)

        if raise_exception or \
           ((raise_exception is None) and raise_exception_for_deprecated):
            raise DeprecationWarning(message_str)

        result = target(*args, **kwargs)
        return result

    
    decorator = FunctionDecorator(log_function)
    return decorator.generic_decorator


def retry(retries, exceptions, interval_secs=0, extra_argument=False):
    """
    Used to decorate functions that should be retried if certain exceptions are
    raised

    Arguments:
    retries -- (int) maximum number of times the function should be run
    exceptions -- ((list of) Exception) rerun the function if these
      exceptions are raised
    extra_argument -- (bool) if True, an argument named `retries` is added to
      the function, which overrides the `retries` value specified by the
      decorator
    """

    def retry_function(target, *args, **kwargs):

        if extra_argument and ('retries' in kwargs):
            actual_retries = kwargs['retries']
            del kwargs['retries']

        else:
            actual_retries = retries
        
        for iteration in range(actual_retries):
            try:
                return target(*args, **kwargs)

            except exceptions as e:
                if iteration < actual_retries - 1:
                    time.sleep(interval_secs)

                else:
                    raise
                # endif
            # endtry

        # e is not available outside except clause in Python 3
        # https://cosmicpercolator.com/2016/01/13/exception-leaks-in-python-2-and-3/
        assert False, "Unexpected execution"

    
    decorator = FunctionDecorator(retry_function)
    return decorator.generic_decorator


def synchronized_on_function(
        __target=None,
        *, lock_field='__lock', dont_synchronize=False):
    """
    Used to decorate function that need thread locking for access

    When called for the first time, this decorator creates a field on
    the function object named by `lock_field`, which holds the lock
    instance for synchronization.

    Argument:
      dont_synchronize -- (bool) If True, synchronization will not be
        performed
    """
    def _call_function(target, *args, **kwargs):

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
        
    #TODO: A little inefficient when dont_synchronize=True
    decorator = FunctionDecorator(
        _call_function
        if not dont_synchronize else _through_staticmethod,
        function_for_staticmethod=_through_classmethod,
        function_for_classmethod=_through_classmethod)
    return decorator.generic_decorator(__target)


def synchronized_on_instance(__target=None, *, lock_field='__lock'):
    """
    Used to decorate instance methods and classes that need thread locking
    for access

    When called for the first time for an instance, this decorator creates
    a field on self named by `lock_field`, which holds the lock instance for
    synchronization.

    @staticmethod and @classmethod not supported. If put on classes,
    @staticmethod and @classmethod will be ignored.
    """
    def call_function(target, *args, **kwargs):

        lock_holder = args[0]

        lock = getattr(lock_holder, lock_field, None)
        if lock is None:
            lock = threading.RLock()
            setattr(lock_holder, lock_field, lock)

        with lock:
            result = target(*args, **kwargs)

        return result


    decorator = FunctionDecorator(
        call_function,
        function_for_staticmethod=_through_classmethod,
        function_for_classmethod=_through_classmethod)
    return decorator.generic_decorator(__target)


def synchronized_on_class(__target=None, *, lock_field='__lock'):
    #TODO: Not sure whether locks should be on each subclass or use one for all subclasses
    ...


def _get_args(target, args, kwargs, exclude_kw=()):

    def _bind_arguments(target, args, kwargs):
        signature = inspect.signature(target)
        bind = signature.bind(*args, **kwargs)
        bind.apply_defaults()
        return bind.arguments


    def _exclude(arguments, exclude_kw):
        for each in exclude_kw:
            del arguments[each]
        # endfor
        

    arguments = _bind_arguments(target, args, kwargs)
    _exclude(arguments, exclude_kw)
    return arguments


def keep_cache(
        __target=None, *, keep_time_secs=None, max_entries=None,
        dont_synchronize=False, exclude_kw=()):
    """
    Decorator to cache returned values of a function for at least the time
    specified since the last call

    Notes:
      Argument values for the target function must be hashable.
    
    Arguments:
      keep_time_secs -- (float; mandatory) Keep value longer than this period
        (seconds)
      max_entries -- (int) Don't keep more than this number of entries
      dont_synchronize -- (bool) True, if thread safety is not necessary
      exclude_kw -- (iterable of str) Iterable of argument names to exclude
        from arguments to identify cache data

    Raises:
      AssertionError -- There are more than `max_entries` values within
        `keep_time_secs`
    """

    cache = OrderedDict()  # holds tuples (<time>, <value>)

    
    @synchronized_on_function(dont_synchronize=dont_synchronize)
    def _cached_function(target, *args, **kwargs):

        now = datetime.datetime.utcnow()
        
        arguments = _get_args(target, args, kwargs, exclude_kw)
        # https://stackoverflow.com/a/39440252/2400328
        key = frozenset(arguments.items())
        if key in cache:
            value = cache[key][1]

            del cache[key]

        else:
            if max_entries and (len(cache) >= max_entries):
                old_key, old_value = cache.popitem(last=False)
                assert (now - old_value[0]).total_seconds() > keep_time_secs

            value = target(*args, **kwargs)

        cache[key] = (now, value)

        return value


    decorator = FunctionDecorator(
        _cached_function,
        function_for_staticmethod=_through_classmethod,
        function_for_classmethod=_through_classmethod)
    return decorator.generic_decorator(__target)


def expire_cache(
        __target=None, *, expire_time_secs=None, max_entries=None,
        dont_synchronize=False):  #TODO: exclude_kw
    """
    Decorator to cache returned values of a function that are held for at most
    a specified amount of time since the first call

    Notes:
      Argument values for the target function must be hashable.
    
    Arguments:
      expire_time_secs -- (float; mandatory) Keep value for less than this
        period (seconds)
      max_entries -- (int) Don't keep more than this number of entries
      dont_synchronize -- (bool) True, if thread safety is not necessary
    """

    cache = OrderedDict()  # holds tuples (<time>, <value>)

    
    @synchronized_on_function(dont_synchronize=dont_synchronize)
    def _cached_function(target, *args, **kwargs):

        now = datetime.datetime.utcnow()
        
        arguments = _get_args(target, args, kwargs)
        # https://stackoverflow.com/a/39440252/2400328
        key = frozenset(arguments.items())
        if key in cache:
            stored_time, stored_value = cache[key]

            if (now - stored_time).total_seconds() < expire_time_secs:
                return stored_value

            del cache[key]

        if max_entries and (len(cache) >= max_entries):
            cache.popitem(last=False)

        value = target(*args, **kwargs)

        cache[key] = (now, value)

        return value


    decorator = FunctionDecorator(
        _cached_function,
        function_for_staticmethod=_through_classmethod,
        function_for_classmethod=_through_classmethod)
    return decorator.generic_decorator(__target)


def _through_function(target, *args, **kwargs):
    return target(*args, **kwargs)


def extend_with_method(__target_class):

    target_class = __target_class

    class _FunctionDecorator(FunctionDecorator):
        def generic_decorator(self, target):  # override
            setattr(target_class, target.__name__, target)
            return super().generic_decorator(target)
        

    decorator = _FunctionDecorator(_through_function)
    return decorator.generic_decorator
