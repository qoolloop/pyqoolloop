import os
import pytest
from typing import (
    Any,
    Dict,
)

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
    save = False

    assert_no_change(1, save=save, error_on_save=False)

    assert_no_change(2, save=save, index=0, error_on_save=False)

    assert_no_change(3, save=save, suffix="suffix", error_on_save=False)

    assert_no_change(4, save=save, index=0, suffix="suffix")


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
def test__assert_no_change__save__no_previous(value: int, kwargs: Dict[str, Any]) -> None:
    
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
