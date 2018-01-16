from builtins import range
import copy
import funcsigs
from functools import (
    wraps,
    partial,
)
import inspect
import threading
import time
import types


#TODO: optional decorator arguments c.f. https://stackoverflow.com/a/14412901

"""
Doesn't support decorating classes not inheriting from object (old-style
classes) in Python 2.

Cannot decorate fixtures or test functions directly in py.test.
Arguments(=fixtures) don't get passed in. Please define another function to
be called from the function of interest.
"""


class Decorator:

    def __init__(self, called_function):
        self.called_function = called_function

    
    def generic_decorator(self, target):

        @wraps(target)
        def called_function(*args, **kwargs):
            return parent.called_function(target, *args, **kwargs)


        class NewClass(object):

            def __init__(self, *args, **kwargs):
                self.instance = target(*args, **kwargs)


            def __getattribute__(self, attr_name):
                try:
                    attr = super(NewClass, self).__getattribute__(attr_name)
                    return attr

                except AttributeError:
                    pass

                attr = self.instance.__getattribute__(attr_name)

                if callable(attr):
                    assert not isinstance(attr, type)
                    return parent.generic_decorator(attr)

                return attr


        if target is None:
            # https://stackoverflow.com/q/653368/2400328
            # @synchronized(...) with parentheses
            return self.generic_decorator

        parent = self

        try:
            assert not isinstance(target, types.ClassType), \
                "Decorator doesn't support old-style classes in Python 2"

        except AttributeError:
            pass  # types.ClassType doesn't exist in Python 3

        if isinstance(target, type):
            return NewClass

        elif callable(target):
            return called_function

        elif isinstance(target, staticmethod):
            assert False, "Put decorator after @staticmethod"

        elif isinstance(target, classmethod):
            assert False, "Put decorator after @classmethod"

        else:
            assert False, \
                "Unsupported target of type: %r\n" % type(target) + \
                "(You could have forgotten argument to decorator.)"
        # endif


#TODO: remove
def parentheses_omittable(f):
    # https://stackoverflow.com/a/14412901/2400328
    '''
    a decorator decorator, allowing the decorator to be used as:
    @decorator(with, arguments, and=kwargs)
    or
    @decorator

    Attention:
      The first argument cannot be a callable or a type.
    '''
    @wraps(f)
    def new_dec(*args, **kwargs):
        if len(args) == 1 and len(kwargs) == 0 and \
           (callable(args[0]) or isinstance(args[0], type)):
            # actual decorated function
            return f(args[0])
        else:
            # decorator arguments
            return lambda realf: f(realf, *args, **kwargs)
        # endif

    return new_dec


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


    decorator = Decorator(log_function)
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


    decorator = Decorator(log_function)
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

    decorator = Decorator(passer_function)
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

    
    decorator = Decorator(log_function)
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
        raise e  # noqa: F821

    
    decorator = Decorator(retry_function)
    return decorator.generic_decorator


def synchronized(__target=None, *, lock_field='__lock'):
    """
    Used to decorate instance methods that need thread locking
    for access

    When called for the first time for an instance, this decorator creates
    a field on self named by `lock_field`, which holds the lock instance for
    synchronization.
    """
    def call_function(target, *args, **kwargs):  #TODO: prefix _

        def _get_self():  #TODO: test with @staticmethod, @classmethod
            print("%r %r" % (inspect.ismethod(target), inspect.isfunction(target))) #TODO: remove
            if inspect.ismethod(target):
                return target.__self__

            print("target: %r" % target)  #TODO: remove
            
            return args[0]
        

        print("arguments: %d, %d" % (len(args), len(kwargs)))  #TODO: remove
        self = _get_self()
        print("self type: %r" % type(self))  #TODO: remove
        if self is None:
            self = target

        lock = getattr(self, lock_field, None)
        if lock is None:
            lock = threading.RLock()
            setattr(self, lock_field, lock)

        with lock:
            result = target(*args, **kwargs)

        return result


    #TODO: somehow functools.partial didn't work
    def _partial_function(*args, **kwargs):
        return call_function(__target, *args, **kwargs)


    decorator = Decorator(call_function)
    
    if __target is None:
        # https://stackoverflow.com/q/653368/2400328
        # @synchronized(...) with parentheses
        return decorator.generic_decorator

    if isinstance(__target, type):
        return decorator.generic_decorator(__target)

    if callable(__target):
        return _partial_function

    assert False, "%r" % type(__target)  #TODO:
