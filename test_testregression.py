"""
Tests for the `testregression` module.
"""
import os
from typing import (
    Any,
    Dict,
)

import pytest

import pylog

from .testregression import (
    assert_no_change,
    make_filename,
)


def test__make_filename__float_index() -> None:
    """
    Test that the `index` argument is treated differently is different types
    are passed to `make_filename()`.
    """
    int_filename = make_filename(index=1)
    float_filename = make_filename(index=1.1)

    assert int_filename != float_filename


def test__make_filename__index() -> None:
    """
    Test that the `index` argument is treated as a `int`, when an `int` is
    passed to `make_filename()`.
    """
    int_filename = make_filename(index=1)

    assert '1' in int_filename
    assert '1.0' not in int_filename


parametrize__assert_no_change = pytest.mark.parametrize('value, kwargs', (
    (1, {}),
    (2, dict(index=0)),
    (3, dict(suffix="suffix")),
    (4, dict(index=0, suffix="suffix")),
))


@parametrize__assert_no_change
def test__assert_no_change(
        value: int, kwargs: Dict[str, Any]) -> None:
    """
    Test that `assert_no_change()` raises `AssertionError`, when
    the `value` argument has changed.
    """

    class _NonExistent:  # pylint: disable=too-few-public-methods
        """ Something that should not exist elsewhere"""


    save = False

    different_values = {
        1: False,
        2: None,
        3: True,
        4: _NonExistent
    }

    assert_no_change(value, save=save, error_on_save=False, **kwargs)
    with pytest.raises(AssertionError):
        assert_no_change(
            different_values[value], save=False, error_on_save=False, **kwargs)


@parametrize__assert_no_change
def test__assert_no_change__no_save(
        value: int, kwargs: Dict[str, Any]) -> None:
    """
    Test that `assert_no_change()` raises `FileNotFoundError` when the `save`
    argument is `False` and no previous value has been saved.
    """
    with pytest.raises(FileNotFoundError):
        assert_no_change(value, save=False, **kwargs)


@parametrize__assert_no_change
def test__assert_no_change__save(
        value: int, kwargs: Dict[str, Any]) -> None:
    """
    Test that `assert_no_change()` raises `AssertionError` when the `save`
    argument is `True`.
    """
    with pytest.raises(AssertionError):
        assert_no_change(value, save=True, **kwargs)


@parametrize__assert_no_change
def test__assert_no_change__save__no_previous(
        value: int, kwargs: Dict[str, Any]) -> None:
    """
    Test that no exception occurs with no value being saved, when  the `save`
    argument if `True`for `assert_no_change()`.
    """
    
    filename = make_filename(**kwargs)
    try:
        os.remove(filename)

    except FileNotFoundError:
        pass

    try:
        assert_no_change(value, save=True, error_on_save=False, **kwargs)

    finally:
        os.remove(filename)

    # enddef


def test__assert_no_change__logger() -> None:
    """
    Test that logging is as expected for `assert_no_change()`.
    """
    # pylint: disable=missing-function-docstring

    class _Logger(pylog.Logger):

        called: bool = False

        message: str

        def error(
                self, msg: str, *arg: Any, **kwargs: Any) -> None:
            self.called = True
            
            super().error(msg, *arg, **kwargs)
            
            self.message += (msg % arg) + "\n"


        def reset_message(self) -> None:
            self.message = ""
            

        def check_empty_message(self) -> None:
            assert self.message == ""

            
        def check_message_content(self) -> None:
            assert "test__assert_no_change__logger" in _logger.message, \
                "message not as expected: %s" % self.message
            assert "test_testregression" in _logger.message
            assert str(value) in _logger.message


        # endclass


    _logger = _Logger('name')

    value = 1

    filename = make_filename()

    try:
        _logger.reset_message()

        with pytest.raises(AssertionError):
            assert_no_change(
                value, save=True, error_on_save=True, _logger=_logger)

        assert _logger.called
        _logger.check_message_content()
            
        _logger.reset_message()

        assert_no_change(
            value, save=True, error_on_save=False, _logger=_logger)
        
        _logger.check_message_content()

        _logger.reset_message()

        assert_no_change(
            value, save=False, error_on_save=False, _logger=_logger)

        _logger.check_empty_message()
        
        _logger.reset_message()

        assert_no_change(
            value, save=False, error_on_save=True, _logger=_logger)

        _logger.check_empty_message()

        _logger.reset_message()

        assert value is not None

        with pytest.raises(AssertionError):
            assert_no_change(
                None, save=False, error_on_save=True, _logger=_logger)

        _logger.check_empty_message()

        _logger.reset_message()

        with pytest.raises(AssertionError):
            assert_no_change(
                None, save=False, error_on_save=False, _logger=_logger)

        _logger.check_empty_message()

    finally:
        os.remove(filename)

    # enddef
