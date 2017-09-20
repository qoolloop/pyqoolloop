from builtins import range
import types
import copy
import funcsigs

"""
Doesn't support decorating classes not inheriting from object (old-style
classes) in Python 2.
"""


class Decorator:

    def __init__(self, called_function):
        self.called_function = called_function

    
    def generic_decorator(self, target):
        
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


def pass_args(target):
    """
    Decorator that passes arguments to the function as a dict as an additional
    argument named `kwargs`

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

    
def obsolete(logger, message=None, raise_exception=False):  #TODO: Rename deprecated.
    """
    Used to decorate obsolete functions and classes

    Arguments:
    logger -- (Logger) where to log message
    message -- (str) additional message to log
    raise_exception -- (bool) True, to raise exception when function (of class)
      is called
    """

    def log_function(target, *args, **kwargs):
        message_str = "obsolete function called: %r (%r)" % \
            (target.__name__, target.__module__)

        if message is not None:
            message_str += "\n" + message
        
        logger.warn(message_str)

        if raise_exception:
            raise DeprecationWarning(message_str)

        result = target(*args, **kwargs)
        return result

    
    decorator = Decorator(log_function)
    return decorator.generic_decorator


deprecated = obsolete  #TODO: Make raise-exception global each for @obsolete and @deprecated


def retry(retries, exceptions, extra_argument=False):
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
                pass
            # endtry

        raise e

    
    decorator = Decorator(retry_function)
    return decorator.generic_decorator
