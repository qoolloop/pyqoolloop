"""
Tests for `introspect.py`
"""
from typing import Tuple

from .introspect import (
    FunctionInfo,
    get_function_info,
)


def test__get_function_info() -> None:
    """
    Test for `get_function_info()`
    """
    module_name, function_name, dir_name = get_function_info()

    assert module_name == 'pyqoolloop.test_introspect'
    assert function_name ==  'test__get_function_info'
    assert dir_name.endswith('/pyqoolloop')


def test__get_function_info__namedtuple() -> None:
    """
    Test for `get_function_info()`
    """
    function_info = get_function_info()

    assert function_info.module == 'pyqoolloop.test_introspect'
    assert function_info.function ==  'test__get_function_info__namedtuple'
    assert function_info.dir.endswith('/pyqoolloop')


def test__get_function_info__depth() -> None:
    """
    Test for `get_function_info()` with depth argument
    """
    def _deep_function() -> Tuple[str, str, str]:
        module_name, function_name, dir_name = get_function_info(2)
        return module_name, function_name, dir_name


    module_name, function_name, dir_name = _deep_function()

    assert module_name == 'pyqoolloop.test_introspect'
    assert function_name ==  'test__get_function_info__depth'
    assert dir_name.endswith('/pyqoolloop')


def test__get_function_info__depth__namedtuple() -> None:
    """
    Test for `get_function_info()` with depth argument
    """
    def _deep_function() -> FunctionInfo:
        return get_function_info(2)


    function_info = _deep_function()

    assert function_info.module == 'pyqoolloop.test_introspect'
    assert function_info.function ==  \
        'test__get_function_info__depth__namedtuple'
    assert function_info.dir.endswith('/pyqoolloop')
