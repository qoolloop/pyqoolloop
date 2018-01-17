from builtins import range
import copy
import funcsigs
from functools import (
    wraps,
)
import inspect
import threading
import time
import types


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


    def generic_decorator_for_class(self, target):
        return self.generic_decorator(target)

    
    def generic_decorator(self, target):

        @wraps(target)
        def called_function(*args, **kwargs):
            return parent.called_function(target, *args, **kwargs)


        class NewMetaClass(type):

            def __getattribute__(self, attr_name):  # self = cls
                print("@attr_name: %r" % attr_name)  #TODO: remove
                
                try:  #TODO: Might want to rethink order with next __getattribute__() call
                    class_attr = super(NewMetaClass, self).__getattribute__(
                        attr_name)
                    print("@@class_attr: %r" % class_attr)
                    return class_attr

                except AttributeError:
                    pass

                print("@target: %r" % target)  #TODO: remove
                class_attr = type(target).__getattribute__(target, attr_name)
                print("@class_attr: %r" % class_attr)  #TODO: remove
                return class_attr


        class NewClass(object, metaclass=NewMetaClass):  #TODO: subclass target

            def __init__(self, *args, **kwargs):
                self.instance = target(*args, **kwargs)  #TODO: need to hide `instance` so that it doesn't collide with other names


            def __getattribute__(self, attr_name):

                def _is_class_attr(attr):  #TODO: remove?
                    cls = self.instance.__class__
                    #TODO: Should be? class_attr = type(cls).__getattribute__(cls, attr_name)
                    class_attr = cls.__getattribute__(cls, attr_name)
                    print("class_attr: %r" % class_attr)  #TODO: remove
                    return attr == class_attr
                

                print("attr_name: %r" % attr_name)  #TODO: remove

                #TODO: Is this going to work for user-overrided functions? searching super before self.instance

                try:
                    attr = super(NewClass, self).__getattribute__(attr_name)
                    return attr

                except AttributeError:
                    pass

                attr = self.instance.__getattribute__(attr_name)

                if callable(attr):
                    print("callable attr: %r" % attr)  #TODO: remove
                    members = inspect.getmembers(attr)
                    print("getmembers: %r" % [each[0] for each in members])  #TODO: remove
                    print("call: %r" % attr.__call__)  #TODO: remove
                    assert not isinstance(attr, type)
                    if _is_class_attr(attr):
                        return parent.generic_decorator_for_class(attr)
                    
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
            print("callable: %r" % target)  #TODO: remove
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
    Used to decorate instance methods and classes that need thread locking
    for access

    When called for the first time for an instance, this decorator creates
    a field on self named by `lock_field`, which holds the lock instance for
    synchronization.

    @staticmethod and @classmethod not supported. If put on classes,
    @staticmethod and @classmethod will be ignored.
    """
    def call_function(target, *args, **kwargs):

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


    decorator = Decorator(call_function)  #TODO: Don't need to use Decorator
    return decorator.generic_decorator(__target)


def synchronized_on_class(__target=None, *, lock_field='__lock'):
    TODO
