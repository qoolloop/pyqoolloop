import copy
import inspect


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

        if isinstance(target, type):
            return NewClass

        elif callable(target):
            return called_function

        elif isinstance(target, staticmethod):
            assert False, "Put decorator after @staticmethod"

        else:
            assert False, "Unsupported target of type: %r" % type(target)
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
        
        arg_names = inspect.signature(target).parameters
        composed_kwargs.update(zip(arg_names, args))
        
        result = target(*args, kwargs=composed_kwargs, **kwargs)
        return result

    decorator = Decorator(passer_function)
    return decorator.generic_decorator(target)

    
def obsolete(logger):
    """
    Used to decorate obsolete functions and classes
    """

    def log_function(target, *args, **kwargs):
        logger.warn("obsolete function called: %r (%r)" %
                    (target.__name__, target.__module__))

        result = target(*args, **kwargs)
        return result

    
    decorator = Decorator(log_function)
    return decorator.generic_decorator
