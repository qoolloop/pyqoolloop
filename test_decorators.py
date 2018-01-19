from . import decorators
from .decorators import (
    pass_args,
    retry,
    synchronized_on_function,
    synchronized_on_instance,
    deprecated,
)

import inspect
import pytest
import threading
import time


# FunctionDecorator ###

@pass_args
def name_of_function():
    pass


def test_FunctionDecorator__wraps():
    assert 'name_of_function' == name_of_function.__name__
    

# pass_args ###

def _pass_args_function(arg0=0, arg1=1, arg2=2, kwargs=None):

    def _check_argument(name, value, default_value, kwargs):
        assert ((name not in kwargs) and (value == default_value)) or \
            (kwargs[name] == value)
    
    _check_argument("arg0", arg0, 0, kwargs)
    _check_argument("arg1", arg1, 1, kwargs)
    _check_argument("arg2", arg2, 2, kwargs)


@pass_args
def pass_args_function(arg0=0, arg1=1, arg2=2, kwargs=None):
    _pass_args_function(arg0, arg1, arg2, kwargs)


def test_pass_args_to_function():
    
    pass_args_function()
    pass_args_function("a")
    pass_args_function("a", "b")
    pass_args_function(arg1="b")
    pass_args_function(arg2="c")
    pass_args_function(arg0="a", arg1="b")
    pass_args_function(arg0="a", arg1="b", arg2="c")


@pass_args
class PassArgsClass(object):

    static_func_call_count = 0

    class_func_call_count = 0

    def __init__(self, arg0=0, kwargs=None):
        _pass_args_function(arg0, kwargs=kwargs)

        self.init_call_count = 1
        self.func_call_count = 0


    # Special methods like __eq__() (slot wrapper) and __dir__()
    # (method) are not supported. (They are not in class.__dict__,
    # but they can be obtained with inspect.getmembers()


    def func(self, arg0=0, kwargs=None):
        _pass_args_function(arg0, kwargs=kwargs)

        self.func_call_count += 1
        

    @staticmethod
    def static_func(arg0=0, kwargs=None):
        _pass_args_function(arg0, kwargs=kwargs)

        PassArgsClass.static_func_call_count += 1


    @classmethod
    def class_func(cls, arg0=0, kwargs=None):
        _pass_args_function(arg0, kwargs=kwargs)

        cls.class_func_call_count += 1
        

def test_pass_args_to_class():

    instance = PassArgsClass()

    instance = PassArgsClass("a")
    assert instance.init_call_count == 1

    instance.func(arg0="A")
    assert instance.func_call_count == 1
    
    instance.func("A")
    assert instance.func_call_count == 2

    instance.func()
    assert instance.func_call_count == 3

    PassArgsClass.static_func()
    assert PassArgsClass.static_func_call_count == 1

    PassArgsClass.static_func(arg0="O")
    assert PassArgsClass.static_func_call_count == 2

    PassArgsClass.static_func("")
    assert PassArgsClass.static_func_call_count == 3

    instance.static_func("oo")
    assert instance.static_func_call_count == 4
    
    PassArgsClass.class_func()
    assert PassArgsClass.class_func_call_count == 1

    PassArgsClass.class_func(arg0="O")
    assert PassArgsClass.class_func_call_count == 2

    PassArgsClass.class_func("")
    assert PassArgsClass.class_func_call_count == 3

    instance.class_func("")
    assert instance.class_func_call_count == 4

    
# deprecated ###

def test_deprecated__log():

    class _Logger(object):

        def warn(self, message):
            self.warn_called = True

            assert message.find("deprecated_function") >= 0


    _logger = _Logger()


    @deprecated(_logger)
    def deprecated_function(arg1, arg2, kwarg1=None, kwarg2=None):
        assert arg1 == 1
        assert arg2 == 2
        assert kwarg1 == 3
        assert kwarg2 == 4
        
        _logger.function_called = True

        return 5


    result = deprecated_function(1, 2, kwarg1=3, kwarg2=4)
    assert result == 5

    assert _logger.warn_called
    assert _logger.function_called


@pytest.mark.parametrize('global_setting', (
    True,
    False,
))
def test_deprecated__raise_exception_true(global_setting):

    class _Logger(object):

        function_called = False

        def warn(self, message):
            self.warn_called = True


    _logger = _Logger()


    @deprecated(_logger, raise_exception=True)
    def deprecated_function():
        _logger.function_called = True

        return 5


    decorators.raise_exception_for_deprecated = global_setting

    try:
        with pytest.raises(DeprecationWarning):
            result = deprecated_function()
            assert result is None

        assert _logger.warn_called
        assert not _logger.function_called

    finally:
        decorators.raise_exception_for_deprecated = False
    # endtry


@pytest.mark.parametrize('global_setting', (
    True,
    False,
))
def test_deprecated__raise_exception_false(global_setting):

    class _Logger(object):

        function_called = False

        def warn(self, message):
            self.warn_called = True


    _logger = _Logger()


    @deprecated(_logger, raise_exception=False)
    def deprecated_function():
        _logger.function_called = True

        return 5


    decorators.raise_exception_for_deprecated = global_setting

    try:
        result = deprecated_function()
        assert result == 5

        assert _logger.warn_called
        assert _logger.function_called

    finally:
        decorators.raise_exception_for_deprecated = False
    # endtry


def test_deprecated__raise_exception_for_deprecated_true():

    class _Logger(object):

        function_called = False

        def warn(self, message):
            self.warn_called = True


    _logger = _Logger()


    @deprecated(_logger)
    def deprecated_function():
        _logger.function_called = True

        return 5


    decorators.raise_exception_for_deprecated = True

    try:
        with pytest.raises(DeprecationWarning):
            result = deprecated_function()
            assert result is None

        assert _logger.warn_called
        assert not _logger.function_called

    finally:
        decorators.raise_exception_for_deprecated = False
    # endtry


def test_deprecated__raise_exception_for_deprecated_false():

    class _Logger(object):

        function_called = False

        def warn(self, message):
            self.warn_called = True


    _logger = _Logger()


    @deprecated(_logger)
    def deprecated_function():
        _logger.function_called = True

        return 5


    decorators.raise_exception_for_deprecated = False

    try:
        result = deprecated_function()
        assert result == 5

        assert _logger.warn_called
        assert _logger.function_called

    finally:
        decorators.raise_exception_for_deprecated = False
    # endtry


# retry ###

class AnException(Exception):
    pass


class UnhandledException(Exception):
    pass


@pytest.mark.parametrize('retries, exceptions', (
    (1, AnException),
    (2, (AnException, RuntimeError)),
    (3, (TypeError, AnException)),
))
def test_retry__with_exceptions(retries, exceptions):

    result = {'count': 0}

    @retry(retries, exceptions)
    def func(arg1, arg2, kwarg1=None, kwarg2=None):
        assert arg1 == 'arg1'
        assert arg2 == 'arg2'
        assert kwarg1 == 'kwarg1'
        assert kwarg2 == 'kwarg2'

        result['count'] += 1

        raise AnException("an exception")


    with pytest.raises(AnException):
        func('arg1', 'arg2', 'kwarg1', 'kwarg2')

    assert result['count'] == retries


@pytest.mark.parametrize('retries, exceptions', (
    (1, AnException),
    (2, (AnException, RuntimeError)),
    (3, (TypeError, AnException)),
))
def test_retry__with_unhandled_exceptions(retries, exceptions):

    result = {'count': 0}

    @retry(retries, exceptions)
    def func(arg1, arg2, kwarg1=None, kwarg2=None):
        assert arg1 == 'arg1'
        assert arg2 == 'arg2'
        assert kwarg1 == 'kwarg1'
        assert kwarg2 == 'kwarg2'

        result['count'] += 1

        raise UnhandledException("an exception")


    with pytest.raises(UnhandledException):
        func('arg1', 'arg2', 'kwarg1', 'kwarg2')

    assert result['count'] == 1


@pytest.mark.parametrize('retries, exceptions', (
    (1, AnException),
    (2, (AnException, RuntimeError)),
    (3, (TypeError, AnException)),
))
def test_retry__with_no_exceptions(retries, exceptions):

    result = {'count': 0}

    @retry(retries, exceptions)
    def func(arg1, arg2, kwarg1=None, kwarg2=None):
        assert arg1 == 'arg1'
        assert arg2 == 'arg2'
        assert kwarg1 == 'kwarg1'
        assert kwarg2 == 'kwarg2'

        result['count'] += 1

        return 0


    value = func('arg1', 'arg2', 'kwarg1', 'kwarg2')
    assert 0 == value

    assert result['count'] == 1

    
@pytest.mark.parametrize('retries', (
    1,
    2,
    3,
))
def test_retry__with_extra_argument(retries):

    result = {'count': 0}

    class AnException(Exception):
        pass

    @retry(1, AnException, extra_argument=True)
    def func(arg1, arg2, kwarg1=None, kwarg2=None):
        assert arg1 == 'arg1'
        assert arg2 == 'arg2'
        assert kwarg1 == 'kwarg1'
        assert kwarg2 == 'kwarg2'

        result['count'] += 1

        raise AnException("an exception")


    with pytest.raises(AnException):
        func('arg1', 'arg2', kwarg2='kwarg2', kwarg1='kwarg1', retries=retries)

    assert result['count'] == retries


@pytest.mark.parametrize('retries_value', (
    1,
    2,
    3,
))
def test_retry__without_extra_argument(retries_value):

    result = {'count': 0}

    class AnException(Exception):
        pass

    @retry(1, AnException, extra_argument=False)
    def func(arg1, arg2, kwarg1=None, kwarg2=None, retries=None):
        assert arg1 == 'arg1'
        assert arg2 == 'arg2'
        assert kwarg1 == 'kwarg1'
        assert kwarg2 == 'kwarg2'
        assert retries == retries_value

        result['count'] += 1

        raise AnException("an exception")


    with pytest.raises(AnException):
        func('arg1', 'arg2', kwarg2='kwarg2', kwarg1='kwarg1',
             retries=retries_value)

    assert result['count'] == 1


@pytest.mark.parametrize('retries, exceptions', (
    (1, AnException),
    (2, (AnException, RuntimeError)),
    (3, (TypeError, AnException)),
))
def test_retry__method(retries, exceptions):

    result = {'count': 0}

    class A:

        @retry(retries, exceptions)
        def func(self, arg1, arg2, kwarg1=None, kwarg2=None):
            assert arg1 == 'arg1'
            assert arg2 == 'arg2'
            assert kwarg1 == 'kwarg1'
            assert kwarg2 == 'kwarg2'

            result['count'] += 1

            raise AnException("an exception")


    a = A()
    with pytest.raises(AnException):
        a.func('arg1', 'arg2', 'kwarg1', 'kwarg2')

    assert result['count'] == retries
    

@pytest.mark.parametrize('retries, exceptions', (
    (1, AnException),
    (2, (AnException, RuntimeError)),
    (3, (TypeError, AnException)),
))
def test_retry__staticmethod(retries, exceptions):

    result = {'count': 0}

    class A:

        @staticmethod
        @retry(retries, exceptions)
        def func(arg1, arg2, kwarg1=None, kwarg2=None):
            assert arg1 == 'arg1'
            assert arg2 == 'arg2'
            assert kwarg1 == 'kwarg1'
            assert kwarg2 == 'kwarg2'

            result['count'] += 1

            raise AnException("an exception")


    with pytest.raises(AnException):
        A.func('arg1', 'arg2', 'kwarg1', 'kwarg2')

    assert result['count'] == retries

    a = A()
    with pytest.raises(AnException):
        a.func('arg1', 'arg2', 'kwarg1', 'kwarg2')

    assert result['count'] == retries * 2
    

@pytest.mark.parametrize('retries, exceptions', (
    (1, AnException),
    (2, (AnException, RuntimeError)),
    (3, (TypeError, AnException)),
))
def test_retry__classmethod(retries, exceptions):

    result = {'count': 0}

    class A:

        @classmethod
        @retry(retries, exceptions)
        def func(cls, arg1, arg2, kwarg1=None, kwarg2=None):
            assert arg1 == 'arg1'
            assert arg2 == 'arg2'
            assert kwarg1 == 'kwarg1'
            assert kwarg2 == 'kwarg2'

            result['count'] += 1

            raise AnException("an exception")


    with pytest.raises(AnException):
        A.func('arg1', 'arg2', 'kwarg1', 'kwarg2')

    assert result['count'] == retries

    a = A()
    with pytest.raises(AnException):
        a.func('arg1', 'arg2', 'kwarg1', 'kwarg2')

    assert result['count'] == retries * 2
    

# common functions ###

def _inc_dec(variables):
    variables['called'] = True

    variables['count'] += 1
    if variables['count'] != 1:
        variables['failure'] = True

    time.sleep(0.001)

    variables['count'] -= 1
    if variables['count'] != 0:
        variables['failure'] = True

    return "result"


def _test_synchronized(function):

    variables = {'count': 0, 'failure': False, 'called': False}

    class _Thread(threading.Thread):

        def run(self):
            NUM_ITERATIONS = 5
            
            for iteration in range(NUM_ITERATIONS):
                result = function(variables)
                assert result == "result"
            # endfor


    NUM_THREADS = 5

    threads = [_Thread() for count in range(NUM_THREADS)]
    for each in threads:
        each.start()

    for each in threads:
        each.join()

    assert variables['called']

    assert not variables['failure']

 
# synchronized_on_function ###

def test_synchronized_on_function():

    @synchronized_on_function(lock_field='lock')
    def function(variables):
        # Cannot access lock on function, because the name `function` doesn't
        # point to this target function anymore after decoration
        return _inc_dec(variables)

    _test_synchronized(function)


# synchronized_on_instance ###

def test_synchronized_on_instance__method():

    class A(object):

        @synchronized_on_instance(lock_field='lock')
        def method(self, variables):
            lock = threading.RLock() # RLock() is a function
            assert isinstance(self.lock, type(lock))
            return _inc_dec(variables)


    a = A()
    _test_synchronized(a.method)


def test_synchronized_on_instance__method__no_parentheses():

    class A(object):

        @synchronized_on_instance
        def method(self, variables):
            lock = threading.RLock() # RLock() is a function
            print("self: %r" % self)  #TODO: remove
            print("self: %r" % inspect.getmembers(self))  #TODO: remove
            assert isinstance(getattr(self, '__lock'), type(lock))
            return _inc_dec(variables)


    a = A()
    _test_synchronized(a.method)


def test_synchronized_on_instance__staticmethod():

    @synchronized_on_instance(lock_field='lock')
    class A(object):

        # __init__(self) doesn't really need locking

        @staticmethod
        def method():
            assert getattr(A, "lock", None) is None

            return "result"


    result = A.method()
    assert result == "result"

    a = A()
    result = a.method()
    assert result == "result"


def test_synchronized_on_instance__classmethod():

    @synchronized_on_instance(lock_field='lock')
    class A(object):

        @classmethod
        def method(cls):
            assert cls is A

            assert getattr(cls, "lock", None) is None

            return "result"


    print("A: %r" % A)  #TODO: remove

    result = A.method()
    assert result == "result"

    a = A()
    result = a.method()
    assert result == "result"


def test_synchronized_on_instance__class():

    @synchronized_on_instance(lock_field='lock')
    class A(object):

        def method(self, variables):
            lock = threading.RLock() # RLock() is a function
            assert isinstance(self.lock, type(lock))
            return _inc_dec(variables)


    a = A()
    _test_synchronized(a.method)


def test_synchronized_on_instance__class__no_parentheses():

    @synchronized_on_instance
    class A(object):

        def method(self, variables):
            lock = threading.RLock() # RLock() is a function
            assert isinstance(getattr(self, '__lock'), type(lock))
            return _inc_dec(variables)


    a = A()
    _test_synchronized(a.method)
