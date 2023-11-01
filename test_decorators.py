# pylint: disable=too-many-lines
"""Tests for `decorators` module."""
import inspect
import threading
import time
from typing import (
    Any,
    Callable,
    cast,
    Dict,
    Iterable,
    Optional,
    Type,
    Tuple,
    Union,
)
from typing_extensions import Protocol

import pytest

from . import decorators
from .decorators import (
    deprecated,
    cache,
    extend_with_method,
    extend_with_class_method,
    extend_with_static_method,
    extension,
    pass_args,
    retry,
    synchronized_on_function,
    synchronized_on_instance,
)

import logging  # pylint: disable=wrong-import-order

logger = logging.getLogger(__name__)


# Common ###


class _Counter:
    counter = 0

    def inc(self) -> int:
        """Increment counter."""
        self.counter += 1
        return self.counter


_counter = _Counter()


DecoratorType = Callable[..., Callable[..., Any]]


# FunctionDecorator ###


def test__FunctionDecorator__wraps() -> None:  # pylint: disable=invalid-name
    """Test that `__name__` of decorated function is the name of the target."""

    @pass_args
    def _name_of_function() -> None:
        """Decorate with `@pass_args`."""

    assert _name_of_function.__name__ == '_name_of_function'


# pass_args ###


class PassArgsFunction(Protocol):
    """A callable that takes 3 arguments."""

    def __call__(self, arg0: Any = 0, arg1: Any = 1, arg2: Any = 2) -> None:
        """Take 3 arguments."""


def _pass_args_function(
    arg0: Any = 0, arg1: Any = 1, arg2: Any = 2, kwargs: Optional[Dict[str, Any]] = None
) -> None:
    def _check_argument(
        name: str,
        value: Any,
        default_value: Any,
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> None:
        assert kwargs is not None
        assert ((name not in kwargs) and (value == default_value)) or (
            kwargs[name] == value
        )

    _check_argument("arg0", arg0, 0, kwargs)
    _check_argument("arg1", arg1, 1, kwargs)
    _check_argument("arg2", arg2, 2, kwargs)


@pass_args
def pass_args_function(
    arg0: Any = 0, arg1: Any = 1, arg2: Any = 2, kwargs: Optional[Dict[str, Any]] = None
) -> None:
    """Decorate with `@pass_args`."""
    _pass_args_function(arg0, arg1, arg2, kwargs=kwargs)


@pass_args
def pass_args_function_with_mandatory_keyword(
    # pylint: disable=invalid-name
    arg0: Any = 0,
    arg1: Any = 1,
    arg2: Any = 2,
    *,
    kwargs: Dict[str, Any],
) -> None:
    """Decorate with `@pass_args` with mandatory keywords."""
    _pass_args_function(arg0, arg1, arg2, kwargs=kwargs)


@pytest.mark.parametrize(
    'function',
    (
        pass_args_function,
        pass_args_function_with_mandatory_keyword,
    ),
)
def test__pass_args_to_function(function: PassArgsFunction) -> None:
    """Test passing argument to functions decorated by `@pass_args`."""
    function()
    function("a")
    function("a", "b")
    function(arg1="b")
    function(arg2="c")
    function(arg0="a", arg1="b")
    function(arg0="a", arg1="b", arg2="c")


class DifferentFunctions(Protocol):
    """Protocol with instance, static, and class methods."""

    static_func_call_count: int

    class_func_call_count: int

    init_call_count: int

    func_call_count: int

    def __init__(
        self,
        arg0: Any = 0,
    ) -> None:
        super().__init__()

    def func(
        self,
        arg0: Any = 0,
    ) -> None:
        """Increment `self.func_call_count`."""

    @staticmethod
    def static_func(
        arg0: Any = 0,
    ) -> None:
        """Increment `cls.static_func_call_count`."""

    @classmethod
    def class_func(
        cls,
        arg0: Any = 0,
    ) -> None:
        """Increment `cls.class_func_call_count`."""


@pass_args
class PassArgsClass:
    # Not subclassing Protocol, because want to test regular class
    """
    Test class for instance, static, and class methods.

    Follows DifferentFunctions protocol.
    """

    # pylint: disable=missing-function-docstring  # b/c follows protocol

    static_func_call_count = 0

    class_func_call_count = 0

    def __init__(self, arg0: Any = 0, kwargs: Optional[Dict[str, Any]] = None) -> None:
        _pass_args_function(arg0, kwargs=kwargs)

        self.init_call_count = 1
        self.func_call_count = 0

    # Special methods like __eq__() (slot wrapper) and __dir__()
    # (method) are not supported. (They are not in class.__dict__,
    # but they can be obtained with inspect.getmembers()

    def func(self, arg0: Any = 0, kwargs: Optional[Dict[str, Any]] = None) -> None:
        """Define instance method."""
        _pass_args_function(arg0, kwargs=kwargs)

        self.func_call_count += 1

    @staticmethod
    def static_func(arg0: Any = 0, kwargs: Optional[Dict[str, Any]] = None) -> None:
        """Define static method."""
        _pass_args_function(arg0, kwargs=kwargs)

        PassArgsClass.static_func_call_count += 1

    @classmethod
    def class_func(cls, arg0: Any = 0, kwargs: Optional[Dict[str, Any]] = None) -> None:
        """Define class method."""
        _pass_args_function(arg0, kwargs=kwargs)

        cls.class_func_call_count += 1


@pass_args
class PassArgsClassWithMandatoryKeyword:
    """
    Test class for methods with mandatory keyword argument.

    Follows DifferentFunctions protocol.

    :param arg0: Optional argument.
    :param kwargs: Mandatory keyword argument.
    """

    # pylint: disable=missing-function-docstring  # b/c follows protocol

    static_func_call_count = 0

    class_func_call_count = 0

    def __init__(self, arg0: Any = 0, *, kwargs: Dict[str, Any]) -> None:
        _pass_args_function(arg0, kwargs=kwargs)

        self.init_call_count = 1
        self.func_call_count = 0

    # Special methods like __eq__() (slot wrapper) and __dir__()
    # (method) are not supported. (They are not in class.__dict__,
    # but they can be obtained with inspect.getmembers()

    def func(self, arg0: Any = 0, *, kwargs: Dict[str, Any]) -> None:
        """Define instance function."""
        _pass_args_function(arg0, kwargs=kwargs)

        self.func_call_count += 1

    @staticmethod
    def static_func(arg0: Any = 0, *, kwargs: Dict[str, Any]) -> None:
        """Define static method."""
        _pass_args_function(arg0, kwargs=kwargs)

        PassArgsClassWithMandatoryKeyword.static_func_call_count += 1

    @classmethod
    def class_func(cls, arg0: Any = 0, *, kwargs: Dict[str, Any]) -> None:
        """Define class method."""
        _pass_args_function(arg0, kwargs=kwargs)

        cls.class_func_call_count += 1


@pytest.mark.parametrize(
    'pass_args_class',
    (
        PassArgsClass,
        PassArgsClassWithMandatoryKeyword,
    ),
)
def test__pass_args_to_class(pass_args_class: Type[DifferentFunctions]) -> None:
    """Test passing arguments to methods in class decorated by `@pass_args`."""
    instance = pass_args_class()

    instance = pass_args_class("a")
    assert instance.init_call_count == 1

    instance.func(arg0="A")
    assert instance.func_call_count == 1

    instance.func("A")
    assert instance.func_call_count == 2

    instance.func()
    assert instance.func_call_count == 3

    pass_args_class.static_func()
    assert pass_args_class.static_func_call_count == 1

    pass_args_class.static_func(arg0="O")
    assert pass_args_class.static_func_call_count == 2

    pass_args_class.static_func("")
    assert pass_args_class.static_func_call_count == 3

    instance.static_func("oo")
    assert instance.static_func_call_count == 4

    pass_args_class.class_func()
    assert pass_args_class.class_func_call_count == 1

    pass_args_class.class_func(arg0="O")
    assert pass_args_class.class_func_call_count == 2

    pass_args_class.class_func("")
    assert pass_args_class.class_func_call_count == 3

    instance.class_func("")
    assert instance.class_func_call_count == 4


# deprecated ###


def test__deprecated__log() -> None:
    """Test `@deprecated` so that it logs the function name."""

    class _Logger(logging.Logger):
        function_called = False
        warn_called = False

        def warning(  # type: ignore[override]
            self, msg: str, *arg: Any, **kwargs: Any
        ) -> None:
            super().warning(msg, *arg, **kwargs)

            self.warn_called = True

            assert "deprecated_function" in msg % arg

    _logger = _Logger('name')

    @deprecated(_logger)
    def _deprecated_function(
        arg1: int, arg2: int, kwarg1: Optional[int] = None, kwarg2: Optional[int] = None
    ) -> int:
        assert arg1 == 1
        assert arg2 == 2
        assert kwarg1 == 3
        assert kwarg2 == 4

        _logger.function_called = True

        return 5

    result = _deprecated_function(1, 2, kwarg1=3, kwarg2=4)
    assert result == 5

    assert _logger.warn_called
    assert _logger.function_called


@pytest.mark.parametrize(
    'global_setting',
    (
        True,
        False,
    ),
)
def test__deprecated__raise_exception_true(global_setting: bool) -> None:
    """Test `@deprecated` with argument `raise_exception` as `True`."""
    # FUTURE: lock for `raise_exception_for_deprecated`, when running parallel

    class _Logger(logging.Logger):
        function_called = False
        warn_called = False

        def warning(  # type: ignore[override]
            self, msg: str, *args: Any, **kwargs: Any
        ) -> None:
            super().warning(msg, *args, **kwargs)
            self.warn_called = True

    _logger = _Logger('name')

    @deprecated(_logger, raise_exception=True)
    def _deprecated_function() -> int:
        _logger.function_called = True

        return 5

    decorators.raise_exception_for_deprecated = global_setting

    try:
        with pytest.raises(DeprecationWarning):
            try:
                result = _deprecated_function()
                assert result is None

            except DeprecationWarning as exception:
                assert "deprecated_function" in str(exception)
                raise

        assert _logger.warn_called
        assert not _logger.function_called

    finally:
        decorators.raise_exception_for_deprecated = False
    # endtry


@pytest.mark.parametrize(
    'global_setting',
    (
        True,
        False,
    ),
)
def test__deprecated__raise_exception_false(global_setting: bool) -> None:
    """Test `@deprecated` with argument `raise_exception` as `False`."""

    class _Logger(logging.Logger):
        function_called = False
        warn_called = False

        def warning(  # type: ignore[override]
            self, msg: str, *args: Any, **kwargs: Any
        ) -> None:
            super().warning(msg, *args, **kwargs)
            self.warn_called = True

    _logger = _Logger('name')

    @deprecated(_logger, raise_exception=False)
    def _deprecated_function() -> int:
        _logger.function_called = True

        return 5

    decorators.raise_exception_for_deprecated = global_setting

    try:
        result = _deprecated_function()
        assert result == 5

        assert _logger.warn_called
        assert _logger.function_called

    finally:
        decorators.raise_exception_for_deprecated = False
    # endtry


def test__deprecated__raise_exception_for_deprecated_true() -> None:
    # noqa: D200
    """
    Test `@deprecated` with argument `raise_exception_for_deprecated=True`.
    """

    class _Logger(logging.Logger):
        function_called = False
        warn_called = False

        def warning(  # type: ignore[override]
            self, msg: str, *args: Any, **kwargs: Any
        ) -> None:
            super().warning(msg, *args, **kwargs)
            self.warn_called = True

    _logger = _Logger('name')

    @deprecated(_logger)
    def _deprecated_function() -> int:
        _logger.function_called = True

        return 5

    decorators.raise_exception_for_deprecated = True

    try:
        with pytest.raises(DeprecationWarning):
            result = _deprecated_function()
            assert result is None

        assert _logger.warn_called
        assert not _logger.function_called

    finally:
        decorators.raise_exception_for_deprecated = False
    # endtry


def test__deprecated__raise_exception_for_deprecated_false() -> None:
    """Test `@deprecated` with `raise_exception_for_deprecated` as `False`."""

    class _Logger(logging.Logger):
        function_called = False
        warn_called = False

        def warning(  # type: ignore[override]
            self, msg: str, *args: Any, **kwargs: Any
        ) -> None:
            super().warning(msg, *args, **kwargs)
            self.warn_called = True

    _logger = _Logger('name')

    @deprecated(_logger)
    def _deprecated_function() -> int:
        _logger.function_called = True

        return 5

    decorators.raise_exception_for_deprecated = False

    try:
        result = _deprecated_function()
        assert result == 5

        assert _logger.warn_called
        assert _logger.function_called

    finally:
        decorators.raise_exception_for_deprecated = False
    # endtry


def test__deprecated__name() -> None:
    """Test that the name of the function decorated with `@retry` is correct."""

    _logger = logging.Logger('name')

    @deprecated(_logger)
    def target() -> None:
        pass

    assert target.__name__ == 'target'


# retry ###


class AnException(Exception):
    """An exception to be raised."""


class UnhandledException(Exception):
    """An exception that isn't handled."""


@pytest.mark.parametrize(
    'attempts, exceptions',
    (
        (1, AnException),
        (2, (AnException, RuntimeError)),
        (3, (TypeError, AnException)),
    ),
)
def test__retry__with_exceptions(
    attempts: int, exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]]
) -> None:
    """Test `@retry` on function that raises expected exception."""
    result = {'count': 0}

    @retry(attempts, exceptions)
    def _func(
        arg1: str, arg2: str, kwarg1: Optional[str] = None, kwarg2: Optional[str] = None
    ) -> None:
        assert arg1 == 'arg1'
        assert arg2 == 'arg2'
        assert kwarg1 == 'kwarg1'
        assert kwarg2 == 'kwarg2'

        result['count'] += 1

        raise AnException("an exception")

    with pytest.raises(AnException):
        _func('arg1', 'arg2', 'kwarg1', 'kwarg2')

    assert result['count'] == attempts


@pytest.mark.parametrize(
    'attempts, exceptions',
    (
        (1, AnException),
        (2, (AnException, RuntimeError)),
        (3, (TypeError, AnException)),
    ),
)
def test__retry__with_unhandled_exceptions(
    attempts: int, exceptions: Union[Type[Exception], Tuple[Type[Exception]]]
) -> None:
    """Test `@retry` on function that raises an unlisted exception."""
    result = {'count': 0}

    @retry(attempts, exceptions)
    def _func(
        arg1: str, arg2: str, kwarg1: Optional[str] = None, kwarg2: Optional[str] = None
    ) -> None:
        assert arg1 == 'arg1'
        assert arg2 == 'arg2'
        assert kwarg1 == 'kwarg1'
        assert kwarg2 == 'kwarg2'

        result['count'] += 1

        raise UnhandledException("an exception")

    with pytest.raises(UnhandledException):
        _func('arg1', 'arg2', 'kwarg1', 'kwarg2')

    assert result['count'] == 1


@pytest.mark.parametrize(
    'attempts, exceptions',
    (
        (1, AnException),
        (2, (AnException, RuntimeError)),
        (3, (TypeError, AnException)),
    ),
)
def test__retry__with_no_exceptions(
    attempts: int, exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]]
) -> None:
    """Test `@retry` with function that doesn't raise exceptions."""
    result = {'count': 0}

    @retry(attempts, exceptions)
    def _func(
        arg1: str, arg2: str, kwarg1: Optional[str] = None, kwarg2: Optional[str] = None
    ) -> int:
        assert arg1 == 'arg1'
        assert arg2 == 'arg2'
        assert kwarg1 == 'kwarg1'
        assert kwarg2 == 'kwarg2'

        result['count'] += 1

        return 0

    value = _func('arg1', 'arg2', 'kwarg1', 'kwarg2')
    assert value == 0

    assert result['count'] == 1


@pytest.mark.parametrize(
    'attempts',
    (
        1,
        2,
        3,
    ),
)
def test__retry__with_extra_argument(attempts: int) -> None:
    """Test `@retry` with `attemps` argument."""
    result = {'count': 0}

    class _AnException(Exception):
        ...

    @retry(1, _AnException, extra_argument=True)
    def _func(
        arg1: str, arg2: str, kwarg1: Optional[str] = None, kwarg2: Optional[str] = None
    ) -> None:
        assert arg1 == 'arg1'
        assert arg2 == 'arg2'
        assert kwarg1 == 'kwarg1'
        assert kwarg2 == 'kwarg2'

        result['count'] += 1

        raise _AnException("an exception")

    with pytest.raises(_AnException):
        _func(  # pylint: disable=unexpected-keyword-arg # attempts
            'arg1', 'arg2', kwarg2='kwarg2', kwarg1='kwarg1', attempts=attempts
        )

    assert result['count'] == attempts


@pytest.mark.parametrize(
    'attempts_value',
    (
        1,
        2,
        3,
    ),
)
def test__retry__without_extra_argument(attempts_value: int) -> None:
    """Test `@retry` on instance method without `attempts` argument."""
    result = {'count': 0}

    class _AnException(Exception):
        ...

    @retry(1, _AnException, extra_argument=False)
    def _func(
        arg1: str,
        arg2: str,
        kwarg1: Optional[str] = None,
        kwarg2: Optional[str] = None,
        attempts: Optional[int] = None,
    ) -> None:
        assert arg1 == 'arg1'
        assert arg2 == 'arg2'
        assert kwarg1 == 'kwarg1'
        assert kwarg2 == 'kwarg2'
        assert attempts == attempts_value

        result['count'] += 1

        raise _AnException("an exception")

    with pytest.raises(_AnException):
        _func('arg1', 'arg2', kwarg2='kwarg2', kwarg1='kwarg1', attempts=attempts_value)

    assert result['count'] == 1


@pytest.mark.parametrize(
    'attempts, exceptions',
    (
        (1, AnException),
        (2, (AnException, RuntimeError)),
        (3, (TypeError, AnException)),
    ),
)
def test__retry(
    attempts: int, exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]]
) -> None:
    """Test `@retry`."""
    # pylint: disable=missing-function-docstring

    result = {'count': 0}

    class _Class:
        @staticmethod
        def common(
            arg1: str,
            arg2: str,
            kwarg1: Optional[str] = None,
            kwarg2: Optional[str] = None,
        ) -> None:
            assert arg1 == 'arg1'
            assert arg2 == 'arg2'
            assert kwarg1 == 'kwarg1'
            assert kwarg2 == 'kwarg2'

            result['count'] += 1

            raise AnException("an exception")

        @retry(attempts, exceptions)
        def instance_method(  # pylint:disable=no-self-use
            self,
            arg1: str,
            arg2: str,
            kwarg1: Optional[str] = None,
            kwarg2: Optional[str] = None,
        ) -> None:
            _Class.common(arg1, arg2, kwarg1, kwarg2)

        @staticmethod
        @retry(attempts, exceptions)
        def static_method(
            arg1: str,
            arg2: str,
            kwarg1: Optional[str] = None,
            kwarg2: Optional[str] = None,
        ) -> None:
            _Class.common(arg1, arg2, kwarg1, kwarg2)

        @classmethod
        @retry(attempts, exceptions)
        def class_method(
            cls,
            arg1: str,
            arg2: str,
            kwarg1: Optional[str] = None,
            kwarg2: Optional[str] = None,
        ) -> None:
            assert arg1 == 'arg1'
            assert arg2 == 'arg2'
            assert kwarg1 == 'kwarg1'
            assert kwarg2 == 'kwarg2'

            result['count'] += 1

            raise AnException("an exception")

    instance = _Class()
    for each in (
        _Class.static_method,
        _Class.class_method,
        instance.instance_method,
    ):
        result['count'] = 0

        with pytest.raises(AnException):
            each('arg1', 'arg2', 'kwarg1', 'kwarg2')

        assert result['count'] == attempts


def test__retry__name() -> None:
    """Test that the name of the function decorated with `@retry` is correct."""

    @retry(1, Exception)
    def target() -> None:
        pass

    assert target.__name__ == 'target'


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
    kwargs: Optional[Dict[str, Any]] = None,
    expected_count: Optional[int] = None,
) -> None:
    if kwargs is None:
        kwargs = {}

    num_iterations = 5

    num_threads = 5

    class _Thread(threading.Thread):
        def __init__(
            self, function: Callable[..., str], *arg: Any, **kwargs: Any
        ) -> None:
            super().__init__(*arg, **kwargs)
            self.function = function

        def run(self) -> None:
            assert kwargs is not None

            for _ in range(num_iterations):
                result = self.function(*args, **kwargs)
                assert result == "result"
            # endfor

    if not isinstance(function, Iterable):
        function = (function,)

    threads = []
    for each_function in function:
        threads.extend([_Thread(each_function) for count in range(num_threads)])

    for each_thread in threads:
        each_thread.start()

    for each_thread in threads:
        each_thread.join()

    assert variables['called']

    assert not variables['failure']

    if expected_count is None:
        expected_count = len(threads) * num_iterations

    assert variables['count'] == expected_count


# synchronized_on_function ###


def test__synchronized_on_function__no_parentheses() -> None:
    """Test `@synchronized_on_instance` on function."""
    variables = _create_variables()

    @synchronized_on_function
    def _function() -> str:
        # Cannot access lock on function, because the name `function` doesn't
        # point to this target function anymore after decoration
        return _inc_dec(variables)

    _test_synchronized(variables, _function)


def test__synchronized_on_function() -> None:
    """Test `@synchronized_on_instance` on function."""
    variables = _create_variables()

    @synchronized_on_function()
    def _function() -> str:
        # Cannot access lock on function, because the name `function` doesn't
        # point to this target function anymore after decoration
        return _inc_dec(variables)

    _test_synchronized(variables, _function)


def test__synchronized_on_function__lock_field() -> None:
    """Test `@synchronized_on_instance` on function."""
    variables = _create_variables()

    @synchronized_on_function(lock_field='lock')
    def _function() -> str:
        # Cannot access lock on function, because the name `function` doesn't
        # point to this target function anymore after decoration
        return _inc_dec(variables)

    _test_synchronized(variables, _function)


@pytest.mark.unreliable
def test__synchronized_on_function__dont_synchronize() -> None:
    """
    Test `@synchronized_on_instance` on instance method.

    The instance method will have no synchronization.
    """
    variables = _create_variables()

    @synchronized_on_function(lock_field='lock', dont_synchronize=True)
    def _function() -> str:
        # Cannot access lock on function, because the name `function` doesn't
        # point to this target function anymore after decoration
        return _inc_dec(variables)

    with pytest.raises(AssertionError):  # Should raise at least sometimes.
        _test_synchronized(variables, _function)
    # endwith


# synchronized_on_instance ###


def test__synchronized_on_instance__method() -> None:
    """Test `@synchronized_on_instance` on instance method."""
    # pylint: disable=missing-function-docstring

    class _Class:
        @synchronized_on_instance(lock_field='lock')
        def method(self, variables: Dict[str, Union[int, bool]]) -> str:
            lock = threading.RLock()  # RLock() is a function
            assert isinstance(self.lock, type(lock))  # type:ignore[attr-defined]
            return _inc_dec(variables)

    variables = _create_variables()

    instance = _Class()
    _test_synchronized(variables, instance.method, (variables,))


def test__synchronized_on_instance__method__no_parentheses() -> None:
    # noqa: D200
    """
    Test `@synchronized_on_instance` on instance method with no parentheses.
    """
    # pylint: disable=missing-function-docstring

    class _Class:
        @synchronized_on_instance
        def method(self, variables: Dict[str, Union[int, bool]]) -> str:
            lock = threading.RLock()  # RLock() is a function
            logger.info("self: %r", self)
            logger.info("self: %r", inspect.getmembers(self))
            assert isinstance(getattr(self, '__lock'), type(lock))
            return _inc_dec(variables)

    variables = _create_variables()

    instance = _Class()
    _test_synchronized(variables, instance.method, (variables,))


def test__synchronized_on_instance__staticmethod() -> None:
    """Test `@synchronized_on_instance` on class with static method."""
    # pylint: disable=missing-function-docstring

    @synchronized_on_instance(lock_field='lock')
    class _Class:
        # __init__(self) doesn't really need locking

        @staticmethod
        def method() -> str:
            assert getattr(_Class, "lock", None) is None

            return "result"

    result = _Class.method()
    assert result == "result"

    instance = _Class()
    result = instance.method()
    assert result == "result"


def test__synchronized_on_instance__classmethod() -> None:
    """Test `@synchronized_on_instance` on class with class method."""
    # pylint: disable=missing-function-docstring

    @synchronized_on_instance(lock_field='lock')
    class _Class:
        @classmethod
        def method(cls) -> str:
            assert cls is _Class

            assert getattr(cls, "lock", None) is None

            return "result"

    result = _Class.method()
    assert result == "result"

    instance = _Class()
    result = instance.method()
    assert result == "result"


def test__synchronized_on_instance__class() -> None:
    """Test `@synchronized_on_instance` on class."""
    # pylint: disable=missing-function-docstring

    @synchronized_on_instance(lock_field='lock')
    class _Class:
        def method(self, variables: Dict[str, Union[int, bool]]) -> str:
            lock = threading.RLock()  # RLock() is a function
            assert isinstance(self.lock, type(lock))  # type:ignore[attr-defined]
            return _inc_dec(variables)

    variables = _create_variables()

    instance = _Class()
    _test_synchronized(variables, instance.method, (variables,))


def test__synchronized_on_instance__class__no_parentheses() -> None:
    """Test `@synchronized_on_instance` with no parentheses."""
    # pylint: disable=missing-function-docstring

    @synchronized_on_instance
    class _Class:
        def method(self, variables: Dict[str, Union[int, bool]]) -> str:
            lock = threading.RLock()  # RLock() is a function
            assert isinstance(getattr(self, '__lock'), type(lock))
            return _inc_dec(variables)

    variables = _create_variables()

    instance = _Class()
    _test_synchronized(variables, instance.method, (variables,))


# common cache ###

_parametrize__cache_test = pytest.mark.parametrize(
    'decorator, kwargs', ((cache, {'expire_time_secs': 10}),)
)


@_parametrize__cache_test
def test__cache__no_args(decorator: DecoratorType, kwargs: Any) -> None:
    """Test cache decorators with no arguments."""
    # pylint: disable=missing-function-docstring

    @decorator(**kwargs)
    def _function() -> int:
        return _counter.inc()

    @decorator(**kwargs)
    class _Class:
        def a_method(self) -> int:  # pylint: disable=no-self-use
            return _counter.inc()

        @staticmethod
        def a_staticmethod() -> int:
            return _counter.inc()

        @classmethod
        def a_classmethod(cls) -> int:
            return _counter.inc()

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


@_parametrize__cache_test
def test__cache__args(decorator: DecoratorType, kwargs: Any) -> None:
    """Test cache decorators with same argument values."""
    # pylint: disable=missing-function-docstring

    @decorator(**kwargs)
    def _function(arg1: int, arg2: int) -> int:
        return arg1 + arg2 + _counter.inc()

    @decorator(**kwargs)
    class _Class:
        def a_method(self, arg1: int, arg2: int) -> int:  # pylint: disable=no-self-use
            return arg1 + arg2 + _counter.inc()

        @staticmethod
        def a_staticmethod(arg1: int, arg2: int) -> int:
            return arg1 + arg2 + _counter.inc()

        @classmethod
        def a_classmethod(cls, arg1: int, arg2: int) -> int:
            return arg1 + arg2 + _counter.inc()

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


@_parametrize__cache_test
def test__cache__kwargs(decorator: DecoratorType, kwargs: Any) -> None:
    """Test cache decorators with same optional arguments."""
    # pylint: disable=missing-function-docstring

    @decorator(**kwargs)
    def _function(
        arg0: int, arg1: int = 0, arg2: int = 3  # pylint: disable=unused-argument
    ) -> int:
        return arg1 + arg2 + _counter.inc()

    @decorator(**kwargs)
    class _Class:
        def a_method(  # pylint: disable=no-self-use
            self,
            arg0: int,  # pylint: disable=unused-argument
            arg1: int = 0,
            arg2: int = 3,
        ) -> int:
            return arg1 + arg2 + _counter.inc()

        @staticmethod
        def a_staticmethod(
            arg0: int, arg1: int = 0, arg2: int = 3  # pylint: disable=unused-argument
        ) -> int:
            return arg1 + arg2 + _counter.inc()

        @classmethod
        def a_classmethod(
            cls,
            arg0: int,  # pylint: disable=unused-argument
            arg1: int = 0,
            arg2: int = 3,
        ) -> int:
            return arg1 + arg2 + _counter.inc()

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


@_parametrize__cache_test
def test__cache__default_kwargs(decorator: DecoratorType, kwargs: Any) -> None:
    """Test cache decorators with same default argument values."""
    # pylint: disable=missing-function-docstring

    @decorator(**kwargs)
    def _function(
        arg0: int, arg1: int = 0, arg2: int = 3  # pylint: disable=unused-argument
    ) -> int:
        return arg1 + arg2 + _counter.inc()

    @decorator(**kwargs)
    class _Class:
        def a_method(  # pylint: disable=no-self-use
            self,
            arg0: int,  # pylint: disable=unused-argument
            arg1: int = 0,
            arg2: int = 3,
        ) -> int:
            return arg1 + arg2 + _counter.inc()

        @staticmethod
        def a_staticmethod(
            arg0: int, arg1: int = 0, arg2: int = 3  # pylint: disable=unused-argument
        ) -> int:
            return arg1 + arg2 + _counter.inc()

        @classmethod
        def a_classmethod(
            cls,
            arg0: int,  # pylint: disable=unused-argument
            arg1: int = 0,
            arg2: int = 3,
        ) -> int:
            return arg1 + arg2 + _counter.inc()

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


@_parametrize__cache_test
def test__cache__synchronize(decorator: DecoratorType, kwargs: Any) -> None:
    """Test that the cache decorators are synchronized correctly."""
    # pylint: disable=missing-function-docstring

    max_entries = 3

    variables = _create_variables()

    @decorator(max_entries=max_entries, **kwargs)
    def _function() -> str:
        return _inc_dec(variables)

    @decorator(max_entries=max_entries, **kwargs)
    class _Class:
        def a_method(self) -> str:  # pylint: disable=no-self-use
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


# cache ###


def test__cache__no_args__expire() -> None:
    """Test `@cache` with no arguments expires the cache."""
    # pylint: disable=missing-function-docstring

    @cache(expire_time_secs=0)
    def _function() -> int:
        return _counter.inc()

    @cache(expire_time_secs=0)
    class _Class:
        def a_method(self) -> int:  # pylint: disable=no-self-use
            return _counter.inc()

        @staticmethod
        def a_staticmethod() -> int:
            return _counter.inc()

        @classmethod
        def a_classmethod(cls) -> int:
            return _counter.inc()

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


def test__cache__max_entries() -> None:
    """
    Test cache decorators with argument `max_entries`.

    Calls method with different arguments.
    """
    # pylint: disable=missing-function-docstring

    max_entries = 3

    @cache(expire_time_secs=10, max_entries=max_entries)
    def _function(arg: int) -> int:
        return arg

    @cache(expire_time_secs=10, max_entries=max_entries)
    class _Class:
        def a_method(self, arg: int) -> int:  # pylint: disable=no-self-use
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


@_parametrize__cache_test
def test__cache__max_entries__same_args(decorator: DecoratorType, kwargs: Any) -> None:
    """
    Test cache decorators with argument `max_entries`.

    Calls method with same arguments.
    """
    # pylint: disable=missing-function-docstring

    max_entries = 3

    @decorator(max_entries=max_entries, **kwargs)
    def _function(arg: int) -> int:
        return arg

    @decorator(max_entries=max_entries, **kwargs)
    class _Class:
        def a_method(self, arg: int) -> int:  # pylint: disable=no-self-use
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
        for _ in range(max_entries + 1):
            value = each(0)
            assert value == 0
        # endfor


def test__cache__max_entries__refresh() -> None:
    """Test `@cache` with argument `max_entries`."""
    # pylint: disable=missing-function-docstring

    max_entries = 3

    @cache(expire_time_secs=10, max_entries=max_entries)
    def _function(arg: int) -> int:
        return arg + _counter.inc()

    @cache(expire_time_secs=10, max_entries=max_entries)
    class _Class:
        def a_method(self, arg: int) -> int:  # pylint: disable=no-self-use
            return arg + _counter.inc()

        @staticmethod
        def a_staticmethod(arg: int) -> int:
            return arg + _counter.inc()

        @classmethod
        def a_classmethod(cls, arg: int) -> int:
            return arg + _counter.inc()

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
    """Protocol with 2 instance methods."""

    new_value: int

    def method(self, value: int) -> None:
        """Define an instance method."""

    def new_method(self, value: int) -> None:
        """Set its argument value to instance variable `new_value`."""


def _test_new_method(class_a: Type[NewMethodClass], instance_a: NewMethodClass) -> None:
    value = 1
    instance_a.new_method(value)
    assert value == instance_a.new_value

    with pytest.raises(TypeError):
        class_a.method(value)  # type:ignore[arg-type, call-arg]

    with pytest.raises(TypeError):
        class_a.new_method(value)  # type:ignore[arg-type, call-arg]


def test__extend_with_method() -> None:
    """Test `@extend_with_method`."""
    # pylint: disable=missing-function-docstring

    class _ClassA:
        new_value: int

        def method(self, value: int) -> None:
            pass

    @extend_with_method(_ClassA)
    def new_method(
        self: _ClassA, value: int
    ) -> None:  # pylint: disable=unused-variable
        self.new_value = value

    instance_a = _ClassA()

    _test_new_method(
        cast(Type[NewMethodClass], _ClassA), cast(NewMethodClass, instance_a)
    )


# @extend_with_class_method ##


class NewClassMethodClass(Protocol):
    """Protocol with a class method."""

    new_value: int

    @classmethod
    def new_class_method(cls, value: int) -> None:
        """Set its argument value to a static member variable `new_value`."""


def _test_new_class_method(
    class_a: Type[NewClassMethodClass], instance_a: NewClassMethodClass
) -> None:
    value = 1
    instance_a.new_class_method(value)
    assert value == instance_a.new_value
    assert value == class_a.new_value

    new_value = 2
    class_a.new_class_method(new_value)
    assert new_value == class_a.new_value


def test__extend_with_class_method() -> None:
    """Test `@extend_with_class_method`."""

    class _ClassA:  # pylint: disable=too-few-public-methods
        new_value: int

    @extend_with_class_method(_ClassA)
    def new_class_method(
        cls: Type[_ClassA], value: int
    ) -> None:  # pylint: disable=unused-variable
        cls.new_value = value

    # Doesn't work for mypy 0.800
    # _ClassA = cast(Type[NewStaticMethodClass], _ClassA)

    CastedA = cast(Type[NewClassMethodClass], _ClassA)  # noqa: N806 # naming
    casted_a = CastedA()

    _test_new_class_method(CastedA, casted_a)


# @extend_with_static_method ##


class NewStaticMethodClass(Protocol):
    """Protocol with static method `new_static_method()`."""

    @staticmethod
    def new_static_method(value: int) -> int:
        """Return its argument."""


def _test_new_static_method(
    class_a: Type[NewStaticMethodClass], instance_a: NewStaticMethodClass
) -> None:
    value = 1
    assert value == instance_a.new_static_method(value)

    new_value = 2
    assert new_value == class_a.new_static_method(new_value)


def test__extend_with_static_method() -> None:
    """Test `@extend_with_static_method`."""

    class _ClassA:  # pylint: disable=too-few-public-methods
        ...

    @extend_with_static_method(_ClassA)
    def new_static_method(value: int) -> int:  # pylint: disable=unused-variable
        return value

    # Doesn't work for mypy 0.800
    # _ClassA = cast(Type[NewStaticMethodClass], _ClassA)
    CastedA = cast(Type[NewStaticMethodClass], _ClassA)  # noqa: N806 # naming
    casted_a = CastedA()

    _test_new_static_method(CastedA, casted_a)


# @extension ##


def test__extension() -> None:
    """Test `@extension`."""
    # pylint: disable=missing-function-docstring

    class _ClassA:
        def method(self, value: int) -> None:
            pass

    @extension(_ClassA)
    class _Extension:
        def new_method(self, value: int) -> None:
            self.new_value = value

        @classmethod
        def new_class_method(cls, value: int) -> None:
            cls.new_value = value

        @staticmethod
        def new_static_method(value: int) -> int:
            return value

    # Doesn't work for mypy 0.800
    # _ClassA = cast(Type[NewStaticMethodClass], _ClassA)

    # Doesn't work for mypy 0.800
    # CastedA = cast(
    #     Union[Type[NewClassMethodClass], Type[NewStaticMethodClass]], _ClassA
    # )

    instance_a = _ClassA()

    _test_new_method(
        cast(Type[NewMethodClass], _ClassA), cast(NewMethodClass, instance_a)
    )
    _test_new_class_method(
        cast(Type[NewClassMethodClass], _ClassA), cast(NewClassMethodClass, instance_a)
    )
    _test_new_static_method(
        cast(Type[NewStaticMethodClass], _ClassA),
        cast(NewStaticMethodClass, instance_a),
    )
