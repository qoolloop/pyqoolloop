import os
import pytest
from typing import (
    Any,
    Dict,
    List,
)

import pylog

from .testregression import (
    assert_no_change,
    make_filename,
)


def test__make_filename__float_index() -> None:
    int_filename = make_filename(index=1)
    float_filename = make_filename(index=1.1)

    assert int_filename != float_filename


def test__make_filename__index() -> None:
    int_filename = make_filename(index=1)

    assert '1.0' not in int_filename


def test__assert_no_change() -> None:

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
    with pytest.raises(FileNotFoundError):
        assert_no_change(1, save=False)

    with pytest.raises(FileNotFoundError):
        assert_no_change(2, save=False, index=0)

    with pytest.raises(FileNotFoundError):
        assert_no_change(3, save=False, suffix="suffix")

    with pytest.raises(FileNotFoundError):
        assert_no_change(4, save=False, index=0, suffix="suffix")
        

def test__assert_no_change__save() -> None:
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
    
    filename = make_filename(**kwargs)
    try:
        os.remove(filename)

    except FileNotFoundError:
        pass

    try:
        assert_no_change(value, save=True, error_on_save=False, **kwargs)

    finally:
        os.remove(filename)

    return


def test__assert_no_change__logger():

    class _Logger(pylog.Logger):

        called: bool = False

        message: str

        def error(  # type:ignore[override]
                self, message: str, *arg: Any, **kwargs: Any) -> None:
            self.called = True
            
            super().error(message, *arg, **kwargs)
            
            self.message += (message % arg) + "\n"


        def reset_message(self):
            self.message = ""
            

        def check_empty_message(self):
            assert self.message == ""

            
        def check_message_content(self):
            assert _logger.message.find(
                "test__assert_no_change__logger") >= 0, \
                "message not as expected: %s" % self.message
            assert _logger.message.find("test_testregression") >= 0
            assert _logger.message.find(str(value)) >= 0


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
