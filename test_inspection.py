"""Tests for `introspect.py`."""
from typing import Tuple

from .inspection import (
    FunctionInfo,
    get_function_info,
    autoimport_modules,
)


def test__get_function_info() -> None:
    """Test for `get_function_info()`."""
    module_name, function_name, dir_name = get_function_info()

    assert module_name == 'pyqoolloop.test_inspection'
    assert function_name == 'test__get_function_info'
    assert dir_name.endswith('/pyqoolloop')


def test__get_function_info__namedtuple() -> None:
    """Test for `get_function_info()`."""
    function_info = get_function_info()

    assert function_info.module == 'pyqoolloop.test_inspection'
    assert function_info.function == 'test__get_function_info__namedtuple'
    assert function_info.dir.endswith('/pyqoolloop')


def test__get_function_info__depth() -> None:
    """Test for `get_function_info()` with depth argument."""

    def _deep_function() -> Tuple[str, str, str]:
        module_name, function_name, dir_name = get_function_info(2)
        return module_name, function_name, dir_name

    module_name, function_name, dir_name = _deep_function()

    assert module_name == 'pyqoolloop.test_inspection'
    assert function_name == 'test__get_function_info__depth'
    assert dir_name.endswith('/pyqoolloop')


def test__get_function_info__depth__namedtuple() -> None:
    """Test for `get_function_info()` with depth argument."""

    def _deep_function() -> FunctionInfo:
        return get_function_info(2)

    function_info = _deep_function()

    assert function_info.module == 'pyqoolloop.test_inspection'
    assert function_info.function == 'test__get_function_info__depth__namedtuple'
    assert function_info.dir.endswith('/pyqoolloop')


def test__autoimport_modules() -> None:
    """Test for `autoimport_modules()`."""
    imported = autoimport_modules(__package__ + '.test_autoimport_modules')
    assert imported['a_module'].A_CONSTANT == 1
    assert imported['may_ignore'].MAYBE_IGNORED is False


def test__autoimport_modules__ignore_prefixes() -> None:
    """Test for `autoimport_modules()` with `ignore_prefixes` specified."""
    imported = autoimport_modules(
        __package__ + '.test_autoimport_modules',
        ignore_prefixes=('test_', '__', 'may_ignore'),
    )
    assert imported['a_module'].A_CONSTANT == 1
    assert 'may_ignore' not in imported
