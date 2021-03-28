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


def test__assert_no_change() -> None:
    """
    Test that `assert_no_change()` raises `AssertionError`, when
    the `value` argument has changed.
    """

    class _NonExistent:  # pylint: disable=too-few-public-methods
        """ Something that should not exist elsewhere"""


    save = False

    assert_no_change(1, save=save, error_on_save=False)
    with pytest.raises(AssertionError):
        assert_no_change(False, save=False, error_on_save=False)

    assert_no_change(2, save=save, index=0, error_on_save=False)
    with pytest.raises(AssertionError):
        assert_no_change(None, save=False, index=0, error_on_save=False)

    assert_no_change(3, save=save, suffix="suffix", error_on_save=False)
    with pytest.raises(AssertionError):
        assert_no_change(
            True, save=False, suffix="suffix", error_on_save=False)

    assert_no_change(4, save=save, index=0, suffix="suffix")
    with pytest.raises(AssertionError):
        assert_no_change(_NonExistent, save=False, index=0, suffix="suffix")


def test__assert_no_change__no_save() -> None:
    """
    Test that `assert_no_change()` raises `FileNotFoundError` when the `save`
    argument is `False` and no previous value has been saved.
    """
    with pytest.raises(FileNotFoundError):
        assert_no_change(1, save=False)

    with pytest.raises(FileNotFoundError):
        assert_no_change(2, save=False, index=0)

    with pytest.raises(FileNotFoundError):
        assert_no_change(3, save=False, suffix="suffix")

    with pytest.raises(FileNotFoundError):
        assert_no_change(4, save=False, index=0, suffix="suffix")
        

def test__assert_no_change__save() -> None:
    """
    Test that `assert_no_change()` raises `AssertionError` when the `save`
    argument is `True`.
    """
    with pytest.raises(AssertionError):
        assert_no_change(1, save=True)

    with pytest.raises(AssertionError):
        assert_no_change(2, save=True, index=0)

    with pytest.raises(AssertionError):
        assert_no_change(3, save=True, suffix="suffix")

    with pytest.raises(AssertionError):
        assert_no_change(4, save=True, index=0, suffix="suffix")


@pytest.mark.parametrize('value, kwargs', (  #TODO: Use same parameters for other tests
    (1, {}),
    (2, dict(index=0)),
    (3, dict(suffix="suffix")),
    (4, dict(index=0, suffix="suffix")),
))
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


def test__assert_no_change__logger():
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


        def reset_message(self):
            self.message = ""
            

        def check_empty_message(self):
            assert self.message == ""

            
        def check_message_content(self):
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
