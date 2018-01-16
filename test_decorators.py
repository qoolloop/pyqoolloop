from . import decorators
from .decorators import (
    pass_args,
    retry,
    synchronized,
    deprecated,
)

import pytest
import sys
import threading


### Decorator ###

@pass_args
def name_of_function():
    pass


def test_Decorator__wraps():
    assert 'name_of_function' == name_of_function.__name__
    

### pass_args ###

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

    def __init__(self):
        # args won't be passed to __init__()
        pass


    def func(self, arg0=" ", kwargs=None):
        _pass_args_function(arg0, kwargs=kwargs)
        

def test_pass_args_to_class():

    instance = PassArgsClass()

    instance.func(arg0="A")
    instance.func("A")


def test_old_style_class():

    if sys.version_info[0] < 3:
        with pytest.raises(AssertionError):
            @pass_args
            class OldStyleClass:
                pass
        # endwith


class OldStyleClass:

    @pass_args
    def func(self, arg0=" ", kwargs=None):
        _pass_args_function(arg0, kwargs=kwargs)
    
    
def test_func_in_old_style_class():

    instance = OldStyleClass()

    instance.func(arg0="A")
    instance.func("A")


### deprecated ###

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


### retry ###

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


### synchronized ###

def test_synchronized_method():

    class A(object):

        @synchronized(lock_field='lock')
        def method(self):
            lock = threading.RLock()
            assert isinstance(self.lock, type(lock))  #TODO: no need to use type()
            return "result"


    a = A()
    result = a.method()
    assert result == "result"


def test_synchronized_method__no_parentheses():

    class A(object):

        @synchronized
        def method(self):
            lock = threading.RLock()
            import inspect  #TODO: remove
            print("self: %r" % self)  #TODO: remove
            print("self: %r" % inspect.getmembers(self))  #TODO: remove
            assert isinstance(getattr(self, '__lock'), type(lock))  #TODO: no need to use type()
            return "result"


    a = A()
    result = a.method()
    assert result == "result"


def test_synchronized_class():

    @synchronized(lock_field='lock')
    class A(object):

        def method(self):
            lock = threading.RLock()
            assert isinstance(self.lock, type(lock))  #TODO: no need to use type()
            return "result"


    a = A()
    result = a.method()
    assert result == "result"
