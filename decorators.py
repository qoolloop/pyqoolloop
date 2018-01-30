from builtins import range
import copy
import funcsigs
from functools import (
    wraps,
)
import inspect
import threading
import time


"""
Doesn't support decorating classes not inheriting from object (old-style
classes) in Python 2.

Cannot decorate fixtures or test functions directly in py.test.
Arguments(=fixtures) don't get passed in. Please define another function to
be called from the function of interest.
"""


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
        
        function_for_staticmethod and function_for_classmethod are only
        used for class decorators
        """

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


def log_calls(logger):
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
        
        logger.warn(message_str)

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


def synchronized_on_function(__target=None, *, lock_field='__lock'):
    """
    Used to decorate function that need thread locking for access

    When called for the first time, this decorator creates a field on
    the function object named by `lock_field`, which holds the lock
    instance for synchronization.
    """
    def call_function(target, *args, **kwargs):

        lock_holder = target

        lock = getattr(lock_holder, lock_field, None)
        if lock is None:
            lock = threading.RLock()
            setattr(lock_holder, lock_field, lock)

        with lock:
            result = target(*args, **kwargs)

        return result


    def through_function(target, cls, *args, **kwargs):
        return target(*args, **kwargs)


    #TODO: Don't really need to use FunctionDecorator
    decorator = FunctionDecorator(call_function,
                                  function_for_staticmethod=through_function,
                                  function_for_classmethod=through_function)
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


    def through_function(target, cls, *args, **kwargs):
        return target(*args, **kwargs)


    decorator = FunctionDecorator(call_function,
                                  function_for_staticmethod=through_function,
                                  function_for_classmethod=through_function)
    return decorator.generic_decorator(__target)


def synchronized_on_class(__target=None, *, lock_field='__lock'):
    #TODO: Not sure whether locks should be on each subclass or use one for all subclasses
    ...
