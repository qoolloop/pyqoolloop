from .decorators import (
    pass_args,
    retry,
    synchronized,
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
            assert isinstance(self.lock, type(lock))


    a = A()
    a.method()


def test_synchronized_class():

    @synchronized(lock_field='lock')
    class A(object):

        def method(self):
            lock = threading.RLock()
            assert isinstance(self.lock, type(lock))


    a = A()
    a.method()
