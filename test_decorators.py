import inspect
from mypy_extensions import (
    DefaultArg,
    # DefaultNamedArg,
)
import pytest
import threading
from typing_extensions import Protocol
import time
from typing import (
    Any,
    Callable,
    cast,
    ClassVar,
    Dict,
    Iterable,
    Optional,
    Type,
    Tuple,
    Union,
)

from . import decorators
from .decorators import (
    deprecated,
    expire_cache,
    extend_with_method,
    extend_with_class_method,
    extend_with_static_method,
    extension,
    keep_cache,
    pass_args,
    retry,
    synchronized_on_function,
    synchronized_on_instance,
)

import pylog
logger = pylog.getLogger(__name__)


# Common ###

_counter = 0


def _counter_function() -> int:
    global _counter
    _counter += 1
    return _counter


DecoratorType = Callable[..., Callable[..., Any]]  #TODO: ?
    

# FunctionDecorator ###

@pass_args
def name_of_function() -> None:
    pass


def test_FunctionDecorator__wraps() -> None:
    assert 'name_of_function' == name_of_function.__name__
    

# pass_args ###

def _pass_args_function(
        arg0: Any = 0,
        arg1: Any = 1,
        arg2: Any = 2,
        kwargs: Optional[Dict[str, Any]] = None) -> None:

    def _check_argument(
            name: str,
            value: Any,
            default_value: Any,
            kwargs: Optional[Dict[str, Any]] = None) -> None:
        assert kwargs is not None
        assert ((name not in kwargs) and (value == default_value)) or \
            (kwargs[name] == value)
    
    _check_argument("arg0", arg0, 0, kwargs)
    _check_argument("arg1", arg1, 1, kwargs)
    _check_argument("arg2", arg2, 2, kwargs)


@pass_args
def pass_args_function(
        arg0: Any = 0,
        arg1: Any = 1,
        arg2: Any = 2,
        kwargs: Optional[Dict[str, Any]] = None) -> None:
    _pass_args_function(arg0, arg1, arg2, kwargs=kwargs)


@pass_args
def pass_args_function_with_mandatory_keyword(
        arg0: Any = 0,
        arg1: Any = 1,
        arg2: Any = 2,
        *,
        kwargs: Dict[str, Any]) -> None:
    _pass_args_function(arg0, arg1, arg2, kwargs=kwargs)


@pytest.mark.parametrize('function', (
    pass_args_function,
    pass_args_function_with_mandatory_keyword,
))
def test_pass_args_to_function(
        function: Callable[
            [
                DefaultArg(Any, 'arg0'),
                DefaultArg(Any, 'arg1'),
                DefaultArg(Any, 'arg2'),
                # DefaultNamedArg(Dict[str, Any], 'kwargs')
            ],
            None]
) -> None:
    
    function()
    function("a")
    function("a", "b")
    function(arg1="b")
    function(arg2="c")
    function(arg0="a", arg1="b")
    function(arg0="a", arg1="b", arg2="c")


@pass_args
class PassArgsClass(object):

    static_func_call_count = 0

    class_func_call_count = 0

    def __init__(
            self, arg0: Any = 0, kwargs: Optional[Dict[str, Any]] = None
    ) -> None:
        _pass_args_function(arg0, kwargs=kwargs)

        self.init_call_count = 1
        self.func_call_count = 0


    # Special methods like __eq__() (slot wrapper) and __dir__()
    # (method) are not supported. (They are not in class.__dict__,
    # but they can be obtained with inspect.getmembers()


    def func(
            self, arg0: Any = 0, kwargs: Optional[Dict[str, Any]] = None
    ) -> None:
        _pass_args_function(arg0, kwargs=kwargs)

        self.func_call_count += 1
        

    @staticmethod
    def static_func(
            arg0: Any = 0, kwargs: Optional[Dict[str, Any]] = None
    ) -> None:
        _pass_args_function(arg0, kwargs=kwargs)

        PassArgsClass.static_func_call_count += 1


    @classmethod
    def class_func(
            cls, arg0: Any = 0, kwargs: Optional[Dict[str, Any]] = None
    ) -> None:
        _pass_args_function(arg0, kwargs=kwargs)

        cls.class_func_call_count += 1
        

@pass_args
class PassArgsClassWithMandatoryKeyword(object):

    static_func_call_count = 0

    class_func_call_count = 0

    def __init__(
            self, arg0: Any = 0, *, kwargs: Dict[str, Any]
    ) -> None:
        _pass_args_function(arg0, kwargs=kwargs)

        self.init_call_count = 1
        self.func_call_count = 0


    # Special methods like __eq__() (slot wrapper) and __dir__()
    # (method) are not supported. (They are not in class.__dict__,
    # but they can be obtained with inspect.getmembers()


    def func(
            self, arg0: Any = 0, *, kwargs: Dict[str, Any]
    ) -> None:
        _pass_args_function(arg0, kwargs=kwargs)

        self.func_call_count += 1
        

    @staticmethod
    def static_func(
            arg0: Any = 0, *, kwargs: Dict[str, Any]
    ) -> None:
        _pass_args_function(arg0, kwargs=kwargs)

        PassArgsClassWithMandatoryKeyword.static_func_call_count += 1


    @classmethod
    def class_func(
            cls, arg0: Any = 0, *, kwargs: Dict[str, Any]
    ) -> None:
        _pass_args_function(arg0, kwargs=kwargs)

        cls.class_func_call_count += 1
        

class DifferentFunctions(Protocol):

    static_func_call_count: ClassVar[int]

    class_func_call_count: ClassVar[int]

    init_call_count: int
    
    func_call_count: int
    
    def __init__(
            self, arg0: Any = 0, # *, kwargs: Dict[str, Any]
    ) -> None:
        ...


    def func(
            self, arg0: Any = 0, # *, kwargs: Dict[str, Any]
    ) -> None:
        ...
        

    @staticmethod
    def static_func(
            arg0: Any = 0, # *, kwargs: Dict[str, Any]
    ) -> None:
        ...


    @classmethod
    def class_func(
            cls, arg0: Any = 0, # *, kwargs: Dict[str, Any]
    ) -> None:
        ...
        

@pytest.mark.parametrize('Klass', (
    PassArgsClass,
    PassArgsClassWithMandatoryKeyword,
))
def test_pass_args_to_class(Klass: Type[DifferentFunctions]) -> None:

    instance = Klass()

    instance = Klass("a")
    assert instance.init_call_count == 1

    instance.func(arg0="A")
    assert instance.func_call_count == 1
    
    instance.func("A")
    assert instance.func_call_count == 2

    instance.func()
    assert instance.func_call_count == 3

    Klass.static_func()
    assert Klass.static_func_call_count == 1

    Klass.static_func(arg0="O")
    assert Klass.static_func_call_count == 2

    Klass.static_func("")
    assert Klass.static_func_call_count == 3

    instance.static_func("oo")
    assert instance.static_func_call_count == 4
    
    Klass.class_func()
    assert Klass.class_func_call_count == 1

    Klass.class_func(arg0="O")
    assert Klass.class_func_call_count == 2

    Klass.class_func("")
    assert Klass.class_func_call_count == 3

    instance.class_func("")
    assert instance.class_func_call_count == 4

    
# deprecated ###

def test_deprecated__log() -> None:

    class _Logger(pylog.Logger):

        function_called: bool

        def warning(  # type:ignore[override]
                self, message: str, *arg: Any, **kwargs: Any) -> None:
            super().warning(message, *arg, **kwargs)
            
            self.warn_called = True

            assert message.find("deprecated_function") >= 0


    _logger = _Logger('name')


    @deprecated(_logger)
    def deprecated_function(
            arg1: int,
            arg2: int,
            kwarg1: Optional[int] = None,
            kwarg2: Optional[int] = None
    ) -> int:
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
def test_deprecated__raise_exception_true(global_setting: bool) -> None:

    class _Logger(pylog.Logger):

        function_called = False

        def warning(  # type:ignore[override]
                self, message: str, *args: Any, **kwargs: Any) -> None:
            self.warn_called = True


    _logger = _Logger('name')


    @deprecated(_logger, raise_exception=True)
    def deprecated_function() -> int:
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
def test_deprecated__raise_exception_false(global_setting: bool) -> None:

    class _Logger(pylog.Logger):

        function_called = False

        def warning(  # type:ignore[override]
                self, message: str, *args: Any, **kwargs: Any) -> None:
            super().warning(message, *args, **kwargs)
            self.warn_called = True


    _logger = _Logger('name')


    @deprecated(_logger, raise_exception=False)
    def deprecated_function() -> int:
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


def test_deprecated__raise_exception_for_deprecated_true() -> None:

    class _Logger(pylog.Logger):

        function_called = False

        def warning(  # type:ignore[override]
                self, message: str, *args: Any, **kwargs: Any) -> None:
            super().warning(message, *args, **kwargs)
            self.warn_called = True


    _logger = _Logger('name')


    @deprecated(_logger)
    def deprecated_function() -> int:
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


def test_deprecated__raise_exception_for_deprecated_false() -> None:

    class _Logger(pylog.Logger):

        function_called = False

        def warning(  # type:ignore[override]
                self, message: str, *args: Any, **kwargs: Any) -> None:
            super().warning(message, *args, **kwargs)
            self.warn_called = True


    _logger = _Logger('name')


    @deprecated(_logger)
    def deprecated_function() -> int:
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


@pytest.mark.parametrize('attempts, exceptions', (
    (1, AnException),
    (2, (AnException, RuntimeError)),
    (3, (TypeError, AnException)),
))
def test_retry__with_exceptions(
        attempts: int,
        exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]]
) -> None:

    result = {'count': 0}

    @retry(attempts, exceptions)
    def func(
            arg1: str,
            arg2: str,
            kwarg1: Optional[str] = None,
            kwarg2: Optional[str] = None) -> None:
        assert arg1 == 'arg1'
        assert arg2 == 'arg2'
        assert kwarg1 == 'kwarg1'
        assert kwarg2 == 'kwarg2'

        result['count'] += 1

        raise AnException("an exception")


    with pytest.raises(AnException):
        func('arg1', 'arg2', 'kwarg1', 'kwarg2')

    assert result['count'] == attempts


@pytest.mark.parametrize('attempts, exceptions', (
    (1, AnException),
    (2, (AnException, RuntimeError)),
    (3, (TypeError, AnException)),
))
def test_retry__with_unhandled_exceptions(
        attempts: int,
        exceptions: Union[Type[Exception], Tuple[Type[Exception]]]) -> None:

    result = {'count': 0}

    @retry(attempts, exceptions)
    def func(
            arg1: str,
            arg2: str,
            kwarg1: Optional[str] = None,
            kwarg2: Optional[str] = None) -> None:
        assert arg1 == 'arg1'
        assert arg2 == 'arg2'
        assert kwarg1 == 'kwarg1'
        assert kwarg2 == 'kwarg2'

        result['count'] += 1

        raise UnhandledException("an exception")


    with pytest.raises(UnhandledException):
        func('arg1', 'arg2', 'kwarg1', 'kwarg2')

    assert result['count'] == 1


@pytest.mark.parametrize('attempts, exceptions', (
    (1, AnException),
    (2, (AnException, RuntimeError)),
    (3, (TypeError, AnException)),
))
def test_retry__with_no_exceptions(
        attempts: int,
        exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]]
) -> None:

    result = {'count': 0}

    @retry(attempts, exceptions)
    def func(
            arg1: str,
            arg2: str,
            kwarg1: Optional[str] = None,
            kwarg2: Optional[str] = None
    ) -> int:
        assert arg1 == 'arg1'
        assert arg2 == 'arg2'
        assert kwarg1 == 'kwarg1'
        assert kwarg2 == 'kwarg2'

        result['count'] += 1

        return 0


    value = func('arg1', 'arg2', 'kwarg1', 'kwarg2')
    assert 0 == value

    assert result['count'] == 1

    
@pytest.mark.parametrize('attempts', (
    1,
    2,
    3,
))
def test_retry__with_extra_argument(attempts: int) -> None:

    result = {'count': 0}

    class AnException(Exception):
        pass

    @retry(1, AnException, extra_argument=True)
    def func(
            arg1: str,
            arg2: str,
            kwarg1: Optional[str] = None,
            kwarg2: Optional[str] = None
    ) -> None:
        assert arg1 == 'arg1'
        assert arg2 == 'arg2'
        assert kwarg1 == 'kwarg1'
        assert kwarg2 == 'kwarg2'

        result['count'] += 1

        raise AnException("an exception")


    with pytest.raises(AnException):
        func(
            'arg1', 'arg2', kwarg2='kwarg2', kwarg1='kwarg1', attempts=attempts)

    assert result['count'] == attempts


@pytest.mark.parametrize('attempts_value', (
    1,
    2,
    3,
))
def test_retry__without_extra_argument(attempts_value: int) -> None:

    result = {'count': 0}

    class AnException(Exception):
        pass

    @retry(1, AnException, extra_argument=False)
    def func(
            arg1: str,
            arg2: str,
            kwarg1: Optional[str] = None,
            kwarg2: Optional[str] = None,
            attempts: Optional[int] = None) -> None:
        assert arg1 == 'arg1'
        assert arg2 == 'arg2'
        assert kwarg1 == 'kwarg1'
        assert kwarg2 == 'kwarg2'
        assert attempts == attempts_value

        result['count'] += 1

        raise AnException("an exception")


    with pytest.raises(AnException):
        func('arg1', 'arg2', kwarg2='kwarg2', kwarg1='kwarg1',
             attempts=attempts_value)

    assert result['count'] == 1


@pytest.mark.parametrize('attempts, exceptions', (
    (1, AnException),
    (2, (AnException, RuntimeError)),
    (3, (TypeError, AnException)),
))
def test_retry__method(
        attempts: int,
        exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]]
) -> None:

    result = {'count': 0}

    class A:

        @retry(attempts, exceptions)
        def func(
                self,
                arg1: str,
                arg2: str,
                kwarg1: Optional[str] = None,
                kwarg2: Optional[str] = None) -> None:
            assert arg1 == 'arg1'
            assert arg2 == 'arg2'
            assert kwarg1 == 'kwarg1'
            assert kwarg2 == 'kwarg2'

            result['count'] += 1

            raise AnException("an exception")


    a = A()
    with pytest.raises(AnException):
        a.func('arg1', 'arg2', 'kwarg1', 'kwarg2')

    assert result['count'] == attempts
    

@pytest.mark.parametrize('attempts, exceptions', (
    (1, AnException),
    (2, (AnException, RuntimeError)),
    (3, (TypeError, AnException)),
))
def test_retry__staticmethod(
        attempts: int,
        exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]]
) -> None:

    result = {'count': 0}

    class A:

        @staticmethod
        @retry(attempts, exceptions)
        def func(
                arg1: str,
                arg2: str,
                kwarg1: Optional[str] = None,
                kwarg2: Optional[str] = None) -> None:
            assert arg1 == 'arg1'
            assert arg2 == 'arg2'
            assert kwarg1 == 'kwarg1'
            assert kwarg2 == 'kwarg2'

            result['count'] += 1

            raise AnException("an exception")


    with pytest.raises(AnException):
        A.func('arg1', 'arg2', 'kwarg1', 'kwarg2')

    assert result['count'] == attempts

    a = A()
    with pytest.raises(AnException):
        a.func('arg1', 'arg2', 'kwarg1', 'kwarg2')

    assert result['count'] == attempts * 2
    

@pytest.mark.parametrize('attempts, exceptions', (
    (1, AnException),
    (2, (AnException, RuntimeError)),
    (3, (TypeError, AnException)),
))
def test_retry__classmethod(
        attempts: int,
        exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]]
) -> None:
    result = {'count': 0}

    class A:

        @classmethod
        @retry(attempts, exceptions)
        def func(
                cls,
                arg1: str,
                arg2: str,
                kwarg1: Optional[str] = None,
                kwarg2: Optional[str] = None) -> None:
            assert arg1 == 'arg1'
            assert arg2 == 'arg2'
            assert kwarg1 == 'kwarg1'
            assert kwarg2 == 'kwarg2'

            result['count'] += 1

            raise AnException("an exception")


    with pytest.raises(AnException):
        A.func('arg1', 'arg2', 'kwarg1', 'kwarg2')

    assert result['count'] == attempts

    a = A()
    with pytest.raises(AnException):
        a.func('arg1', 'arg2', 'kwarg1', 'kwarg2')

    assert result['count'] == attempts * 2
    

# common functions ###

def _create_variables() -> Dict[str, Union[int, bool]]:
    variables = {'count': 0, 'inc_dec': 0, 'failure': False, 'called': False}
    return variables


def _reset_variables(variables: Dict[str, Union[int, bool]]) -> None:
    original_values = _create_variables()
    variables.update(original_values)


def _inc_dec(variables: Dict[str, Union[int, bool]]) -> str:
    variables['called'] = True

    variables['count'] += 1

    variables['inc_dec'] += 1
    if variables['inc_dec'] != 1:
        variables['failure'] = True

    time.sleep(0.001)

    variables['inc_dec'] -= 1
    if variables['inc_dec'] != 0:
        variables['failure'] = True

    return "result"


def _test_synchronized(
        variables: Dict[str, Union[int, bool]],
        function: Union[Callable[..., str], Iterable[Callable[..., str]]],
        args: Tuple[Any, ...] = (),
        kwargs: Dict[str, Any] = dict(),
        expected_count: Optional[int] = None
) -> None:

    NUM_ITERATIONS = 5
            
    NUM_THREADS = 5

    class _Thread(threading.Thread):

        def __init__(
                self, function: Callable[..., str], *arg: Any, **kwargs: Any
        ) -> None:
            super().__init__(*arg, **kwargs)
            self.function = function

        def run(self) -> None:
            for iteration in range(NUM_ITERATIONS):
                result = self.function(*args, **kwargs)
                assert result == "result"
            # endfor


    if not isinstance(function, Iterable):
        function = (function,)

    threads = []
    for each_function in function:
        threads.extend(
            [_Thread(each_function) for count in range(NUM_THREADS)]
        )

    for each_thread in threads:
        each_thread.start()

    for each_thread in threads:
        each_thread.join()

    assert variables['called']

    assert not variables['failure']

    if expected_count is None:
        expected_count = len(threads) * NUM_ITERATIONS
        
    assert variables['count'] == expected_count


# synchronized_on_function ###

def test_synchronized_on_function() -> None:

    variables = _create_variables()

    @synchronized_on_function(lock_field='lock')
    def function() -> str:
        # Cannot access lock on function, because the name `function` doesn't
        # point to this target function anymore after decoration
        return _inc_dec(variables)

    _test_synchronized(variables, function)


@pytest.mark.unreliable
def test_synchronized_on_function__dont_synchronize() -> None:

    variables = _create_variables()

    @synchronized_on_function(lock_field='lock', dont_synchronize=True)
    def function() -> str:
        # Cannot access lock on function, because the name `function` doesn't
        # point to this target function anymore after decoration
        return _inc_dec(variables)

    with pytest.raises(AssertionError):  # Should raise at least sometimes.
        _test_synchronized(variables, function)
    # endwith


# synchronized_on_instance ###

def test_synchronized_on_instance__method() -> None:

    class A(object):

        @synchronized_on_instance(lock_field='lock')
        def method(self, variables: Dict[str, Union[int, bool]]) -> str:
            lock = threading.RLock()  # RLock() is a function
            assert isinstance(
                self.lock, type(lock))  # type:ignore[attr-defined]
            return _inc_dec(variables)


    variables = _create_variables()

    a = A()
    _test_synchronized(variables, a.method, (variables,))


def test_synchronized_on_instance__method__no_parentheses() -> None:

    class A(object):

        @synchronized_on_instance
        def method(self, variables: Dict[str, Union[int, bool]]) -> str:
            lock = threading.RLock()  # RLock() is a function
            logger.info("self: %r", self)
            logger.info("self: %r", inspect.getmembers(self))
            assert isinstance(getattr(self, '__lock'), type(lock))
            return _inc_dec(variables)


    variables = _create_variables()

    a = A()
    _test_synchronized(variables, a.method, (variables,))


def test_synchronized_on_instance__staticmethod() -> None:

    @synchronized_on_instance(lock_field='lock')
    class A(object):

        # __init__(self) doesn't really need locking

        @staticmethod
        def method() -> str:
            assert getattr(A, "lock", None) is None

            return "result"


    result = A.method()
    assert result == "result"

    a = A()
    result = a.method()
    assert result == "result"


def test_synchronized_on_instance__classmethod() -> None:

    @synchronized_on_instance(lock_field='lock')
    class A(object):

        @classmethod
        def method(cls) -> str:
            assert cls is A

            assert getattr(cls, "lock", None) is None

            return "result"


    result = A.method()
    assert result == "result"

    a = A()
    result = a.method()
    assert result == "result"


def test_synchronized_on_instance__class() -> None:

    @synchronized_on_instance(lock_field='lock')
    class A(object):

        def method(self, variables: Dict[str, Union[int, bool]]) -> str:
            lock = threading.RLock()  # RLock() is a function
            assert isinstance(
                self.lock, type(lock))  # type:ignore[attr-defined]
            return _inc_dec(variables)


    variables = _create_variables()

    a = A()
    _test_synchronized(variables, a.method, (variables,))


def test_synchronized_on_instance__class__no_parentheses() -> None:

    @synchronized_on_instance
    class A(object):

        def method(self, variables: Dict[str, Union[int, bool]]) -> str:
            lock = threading.RLock()  # RLock() is a function
            assert isinstance(getattr(self, '__lock'), type(lock))
            return _inc_dec(variables)


    variables = _create_variables()

    a = A()
    _test_synchronized(variables, a.method, (variables,))


# common cache ###

CACHE_DECORATORS = (
    (keep_cache, dict(keep_time_secs=0.1)),
    (expire_cache, dict(expire_time_secs=10)),
)
    

@pytest.mark.parametrize('decorator, kwargs',
                         CACHE_DECORATORS)
def test_cache__no_args(
        decorator: DecoratorType,
        kwargs: Any
) -> None:
    
    @decorator(**kwargs)
    def _function() -> int:
        return _counter_function()


    @decorator(**kwargs)
    class _Class:
        def a_method(self) -> int:
            return _counter_function()


        @staticmethod
        def a_staticmethod() -> int:
            return _counter_function()


        @classmethod
        def a_classmethod(cls) -> int:
            return _counter_function()


    instance = _Class()

    for each in (
            _function,
            instance.a_method,
            instance.a_staticmethod,
            instance.a_classmethod,
            _Class.a_staticmethod,
            _Class.a_classmethod,
    ):
        first = each()

        second = each()

        assert first == second


@pytest.mark.parametrize('decorator, kwargs',
                         CACHE_DECORATORS)
def test_cache__args(
        decorator: DecoratorType,
        kwargs: Any
) -> None:

    @decorator(**kwargs)
    def _function(arg1: int, arg2: int) -> int:
        return arg1 + arg2 + _counter_function()


    @decorator(**kwargs)
    class _Class:
        def a_method(self, arg1: int, arg2: int) -> int:
            return arg1 + arg2 + _counter_function()


        @staticmethod
        def a_staticmethod(arg1: int, arg2: int) -> int:
            return arg1 + arg2 + _counter_function()


        @classmethod
        def a_classmethod(cls, arg1: int, arg2: int) -> int:
            return arg1 + arg2 + _counter_function()


    instance = _Class()

    for each in (
            _function,
            instance.a_method,
            instance.a_staticmethod,
            instance.a_classmethod,
            _Class.a_staticmethod,
            _Class.a_classmethod,
    ):
        first = each(1, 1)

        different = each(1, 2)
        assert different != first

        second = each(1, 1)

        assert first == second


@pytest.mark.parametrize('decorator, kwargs',
                         CACHE_DECORATORS)
def test_cache__kwargs(
        decorator: DecoratorType,
        kwargs: Any
) -> None:

    @decorator(**kwargs)
    def _function(arg0: int, arg1: int = 0, arg2: int = 3) -> int:
        return arg1 + arg2 + _counter_function()


    @decorator(**kwargs)
    class _Class:
        def a_method(self, arg0: int, arg1: int = 0, arg2: int = 3) -> int:
            return arg1 + arg2 + _counter_function()


        @staticmethod
        def a_staticmethod(arg0: int, arg1: int = 0, arg2: int = 3) -> int:
            return arg1 + arg2 + _counter_function()


        @classmethod
        def a_classmethod(
                cls, arg0: int, arg1: int = 0, arg2: int = 3) -> int:
            return arg1 + arg2 + _counter_function()


    instance = _Class()

    for each in (
            _function,
            instance.a_method,
            instance.a_staticmethod,
            instance.a_classmethod,
            _Class.a_staticmethod,
            _Class.a_classmethod,
    ):
        first = each(1, arg2=1)

        different = each(1, arg2=2)
        assert different != first

        second = each(1, arg2=1)

        assert first == second


@pytest.mark.parametrize('decorator, kwargs',
                         CACHE_DECORATORS)
def test_cache__default_kwargs(
        decorator: DecoratorType,
        kwargs: Any
) -> None:

    @decorator(**kwargs)
    def _function(arg0: int, arg1: int = 0, arg2: int = 3) -> int:
        return arg1 + arg2 + _counter_function()


    @decorator(**kwargs)
    class _Class():
        def a_method(self, arg0: int, arg1: int = 0, arg2: int = 3) -> int:
            return arg1 + arg2 + _counter_function()


        @staticmethod
        def a_staticmethod(arg0: int, arg1: int = 0, arg2: int = 3) -> int:
            return arg1 + arg2 + _counter_function()


        @classmethod
        def a_classmethod(
                cls, arg0: int, arg1: int = 0, arg2: int = 3) -> int:
            return arg1 + arg2 + _counter_function()


    instance = _Class()

    for each in (
            _function,
            instance.a_method,
            instance.a_staticmethod,
            instance.a_classmethod,
            _Class.a_staticmethod,
            _Class.a_classmethod,
    ):
        first = each(1)

        different = each(1, arg2=4)
        assert different != first

        second = each(1, arg1=0)

        assert first == second


@pytest.mark.parametrize('decorator, kwargs',
                         CACHE_DECORATORS)
def test_cache__synchronize(
        decorator: DecoratorType,
        kwargs: Any
) -> None:

    max_entries = 3

    variables = _create_variables()

    @decorator(max_entries=max_entries, **kwargs)
    def _function() -> str:
        return _inc_dec(variables)


    @decorator(max_entries=max_entries, **kwargs)
    class _Class:
        def a_method(self) -> str:
            return _inc_dec(variables)


        @staticmethod
        def a_staticmethod() -> str:
            return _inc_dec(variables)


        @classmethod
        def a_classmethod(cls) -> str:
            return _inc_dec(variables)


    instance = _Class()

    for each in (
            _function,
            instance.a_method,
            (_Class.a_staticmethod, instance.a_staticmethod),
            (_Class.a_classmethod, instance.a_classmethod),
    ):
        
        _reset_variables(variables)

        _test_synchronized(variables, each, expected_count=1)


# keep_cache ###

def test_keep_cache__max_entries() -> None:

    max_entries = 3

    @keep_cache(keep_time_secs=10, max_entries=max_entries)
    def _function(arg: int) -> int:
        return arg


    NUM_CALLABLES = 6
    for index in range(NUM_CALLABLES):

        @keep_cache(keep_time_secs=10, max_entries=max_entries)  #TODO: No mypy warning even though `@keep_cache` isn't declared for classes.
        class _Class():
            def a_method(self, arg: int) -> int:
                return arg

            @staticmethod
            def a_staticmethod(arg: int) -> int:
                return arg

            @classmethod
            def a_classmethod(cls, arg: int) -> int:
                return arg


        instance = _Class()

        CALLABLES = (
            _function,
            instance.a_method,
            instance.a_staticmethod,
            instance.a_classmethod,
            _Class.a_staticmethod,
            _Class.a_classmethod,
        )
        assert len(CALLABLES) == NUM_CALLABLES

        each = CALLABLES[index]
        
        for index in range(max_entries + 1):
            if index == max_entries:
                with pytest.raises(AssertionError):
                    _ = each(index)
                # endwith

            else:
                value = each(index)
                assert value == index
            # endif
        # endfor
    # endfor


def test_keep_cache__max_entries__expire() -> None:

    max_entries = 3

    keep_time_secs = 0.01

    @keep_cache(keep_time_secs=keep_time_secs, max_entries=max_entries)
    def _function(arg: int) -> int:
        return arg


    @keep_cache(keep_time_secs=keep_time_secs, max_entries=max_entries)
    class _Class():
        def a_method(self, arg: int) -> int:
            return arg

        @staticmethod
        def a_staticmethod(arg: int) -> int:
            return arg

        @classmethod
        def a_classmethod(cls, arg: int) -> int:
            return arg


    instance = _Class()

    for each in (
            _function,
            instance.a_method,
            instance.a_staticmethod,
            instance.a_classmethod,
            _Class.a_staticmethod,
            _Class.a_classmethod,
    ):
        for index in range(max_entries):
            if index == max_entries - 1:
                time.sleep(keep_time_secs)

            value = each(index)
            assert value == index
        # endfor
    # endfor


def test_keep_cache__max_entries__refresh() -> None:

    max_entries = 3

    keep_time_secs = 0.01

    @keep_cache(keep_time_secs=keep_time_secs, max_entries=max_entries)
    def _function(arg: int) -> int:
        return arg

    
    NUM_CALLABLES = 6
    for index in range(NUM_CALLABLES):

        @keep_cache(keep_time_secs=keep_time_secs, max_entries=max_entries)
        class _Class():
            def a_method(self, arg: int) -> int:
                return arg

            @staticmethod
            def a_staticmethod(arg: int) -> int:
                return arg

            @classmethod
            def a_classmethod(cls, arg: int) -> int:
                return arg


        instance = _Class()

        CALLABLES = (
            _function,
            instance.a_method,
            instance.a_staticmethod,
            instance.a_classmethod,
            _Class.a_staticmethod,
            _Class.a_classmethod,
        )
        assert len(CALLABLES) == NUM_CALLABLES

        each = CALLABLES[index]
        
        for index in range(max_entries):
            value = each(index)
            assert value == index

        for index in range(5):
            time.sleep(keep_time_secs / 2)
            value = each(0)
            assert value == 0
        # endfor
    # endfor


def test_keep_cache__exclude_kw() -> None:
    
    @keep_cache(keep_time_secs=0, exclude_kw=['extra'])
    def _function(arg: int, extra: int) -> int:
        return arg + extra


    @keep_cache(keep_time_secs=0, exclude_kw=['extra'])
    class _Class():
        def a_method(self, arg: int, extra: int) -> int:
            return arg + extra

        @staticmethod
        def a_staticmethod(arg: int, extra: int) -> int:
            return arg + extra

        @classmethod
        def a_classmethod(cls, arg: int, extra: int) -> int:
            return arg + extra


    instance = _Class()

    for each in (
            _function,
            instance.a_method,
            instance.a_staticmethod,
            instance.a_classmethod,
            _Class.a_staticmethod,
            _Class.a_classmethod,
    ):
        first = each(1, 1)

        different = each(2, 1)
        assert different != first

        second = each(1, 2)
        assert first == second
    # endfor


# expire_cache ###

def test_expire_cache__no_args__expire() -> None:

    @expire_cache(expire_time_secs=0)
    def _function() -> int:
        return _counter_function()


    @expire_cache(expire_time_secs=0)
    class _Class:
        def a_method(self) -> int:
            return _counter_function()


        @staticmethod
        def a_staticmethod() -> int:
            return _counter_function()


        @classmethod
        def a_classmethod(cls) -> int:
            return _counter_function()


    instance = _Class()

    for each in (
            _function,
            instance.a_method,
            instance.a_staticmethod,
            instance.a_classmethod,
            _Class.a_staticmethod,
            _Class.a_classmethod,
    ):
        first = each()

        second = each()

        assert first < second


def test_expire_cache__max_entries() -> None:

    max_entries = 3

    @expire_cache(expire_time_secs=10, max_entries=max_entries)
    def _function(arg: int) -> int:
        return arg


    @expire_cache(expire_time_secs=10, max_entries=max_entries)
    class _Class:
        def a_method(self, arg: int) -> int:
            return arg


        @staticmethod
        def a_staticmethod(arg: int) -> int:
            return arg


        @classmethod
        def a_classmethod(cls, arg: int) -> int:
            return arg


    instance = _Class()

    for each in (
            _function,
            instance.a_method,
            instance.a_staticmethod,
            instance.a_classmethod,
            _Class.a_staticmethod,
            _Class.a_classmethod,
    ):
        for index in range(max_entries + 1):
            value = each(index)
            assert value == index
        # endfor


@pytest.mark.parametrize('decorator, kwargs',
                         CACHE_DECORATORS)
def test_expire_cache__max_entries__same_args(
        decorator: DecoratorType,
        kwargs: Any
) -> None:

    max_entries = 3

    @decorator(max_entries=max_entries, **kwargs)
    def _function(arg: int) -> int:
        return arg


    @decorator(max_entries=max_entries, **kwargs)
    class _Class:
        def a_method(self, arg: int) -> int:
            return arg


        @staticmethod
        def a_staticmethod(arg: int) -> int:
            return arg


        @classmethod
        def a_classmethod(cls, arg: int) -> int:
            return arg


    instance = _Class()

    for each in (
            _function,
            instance.a_method,
            instance.a_staticmethod,
            instance.a_classmethod,
            _Class.a_staticmethod,
            _Class.a_classmethod,
    ):
        for index in range(max_entries + 1):
            value = each(0)
            assert value == 0
        # endfor


def test_expire_cache__max_entries__refresh() -> None:

    max_entries = 3

    @expire_cache(expire_time_secs=10, max_entries=max_entries)
    def _function(arg: int) -> int:
        return arg + _counter_function()


    @expire_cache(expire_time_secs=10, max_entries=max_entries)
    class _Class:
        def a_method(self, arg: int) -> int:
            return arg + _counter_function()


        @staticmethod
        def a_staticmethod(arg: int) -> int:
            return arg + _counter_function()


        @classmethod
        def a_classmethod(cls, arg: int) -> int:
            return arg + _counter_function()


    instance = _Class()

    for each in (
            _function,
            instance.a_method,
            instance.a_staticmethod,
            instance.a_classmethod,
            _Class.a_staticmethod,
            _Class.a_classmethod,
    ):
        first = each(0)

        for index in range(max_entries):
            each(index + 1)

        second = each(0)

        assert first < second


# extend_with_method ##

class NewMethodClass(Protocol):
    new_value: int

    def method(self, value: int) -> None:
        ...
        
    def new_method(self, value: int) -> None:
        ...


def _test_new_method(A: Type[NewMethodClass], a: NewMethodClass) -> None:
    value = 1
    a.new_method(value)
    assert value == a.new_value

    with pytest.raises(TypeError):
        A.method(value)  # type:ignore[attr-defined, arg-type, call-arg]

    with pytest.raises(TypeError):
        A.new_method(value)  # type:ignore[attr-defined, arg-type, call-arg]


def test__extend_with_method() -> None:

    class A:
        new_value: int
        
        def method(self, value: int) -> None:
            pass
    

    @extend_with_method(A)
    def new_method(self: A, value: int) -> None:
        self.new_value = value


    a = A()

    _test_new_method(cast(Type[NewMethodClass], A), cast(NewMethodClass, a))


# @extend_with_class_method ##

class NewClassMethodClass(Protocol):
    new_value: ClassVar[int]
    
    @classmethod
    def new_class_method(cls, value: int) -> None:
        ...
        

def _test_new_class_method(
        A: Type[NewClassMethodClass], a: NewClassMethodClass) -> None:
    value = 1
    a.new_class_method(value)
    assert value == a.new_value
    assert value == A.new_value

    new_value = 2
    A.new_class_method(new_value)
    assert new_value == A.new_value
    

def test__extend_with_class_method() -> None:

    class A:
        new_value: ClassVar[int]
    

    @extend_with_class_method(A)
    def new_class_method(cls: Type[A], value: int) -> None:
        cls.new_value = value


    # A = cast(Type[NewStaticMethodClass], A)  # Doesn't work for mypy 0.800
    CastedA = cast(Type[NewClassMethodClass], A)
    casted_a = CastedA()

    _test_new_class_method(CastedA, casted_a)


# @extend_with_static_method ##

class NewStaticMethodClass(Protocol):
    @staticmethod
    def new_static_method(value: int) -> int:
        ...
    

def _test_new_static_method(
        A: Type[NewStaticMethodClass], a: NewStaticMethodClass) -> None:
    value = 1
    assert value == a.new_static_method(value)

    new_value = 2
    assert new_value == A.new_static_method(new_value)
    

def test__extend_with_static_method() -> None:

    class A:
        pass


    @extend_with_static_method(A)
    def new_static_method(value: int) -> int:
        return value


    # A = cast(Type[NewStaticMethodClass], A)  # Doesn't work for mypy 0.800
    CastedA = cast(Type[NewStaticMethodClass], A)
    casted_a = CastedA()

    _test_new_static_method(CastedA, casted_a)


# @extension ##

def test__extension() -> None:

    class A:
        def method(self, value: int) -> None:
            pass


    @extension(A)
    class Extension:
        def new_method(self, value: int) -> None:
            self.new_value = value

        @classmethod
        def new_class_method(cls, value: int) -> None:
            cls.new_value = value

        @staticmethod
        def new_static_method(value: int) -> int:
            return value

        
    # A = cast(Type[NewStaticMethodClass], A)  # Doesn't work for mypy 0.800
    # CastedA = cast(  # Doesn't work for mypy 0.800
    #     Union[Type[NewClassMethodClass], Type[NewStaticMethodClass]], A)
    a = A()

    _test_new_method(
        cast(Type[NewMethodClass], A), cast(NewMethodClass, a))
    _test_new_class_method(
        cast(Type[NewClassMethodClass], A), cast(NewClassMethodClass, a))
    _test_new_static_method(
        cast(Type[NewStaticMethodClass], A), cast(NewStaticMethodClass, a))
