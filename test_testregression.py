import pytest

from .testregression import (
    assert_no_change,
    make_filename,
)


def test__make_filename__float_index():
    int_filename = make_filename(index=1)
    float_filename = make_filename(index=1.1)

    assert int_filename != float_filename


def test__make_filename__index():
    int_filename = make_filename(index=1)

    assert '1.0' not in int_filename


def test__assert_no_change():
    save = False

    assert_no_change(1, save, error_on_save=False)

    assert_no_change(2, save, index=0, error_on_save=False)

    assert_no_change(3, save, suffix="suffix", error_on_save=False)

    assert_no_change(4, save, index=0, suffix="suffix")


def test__assert_no_change__no_save():
    with pytest.raises(FileNotFoundError):
        assert_no_change(1, save=False)

    with pytest.raises(FileNotFoundError):
        assert_no_change(2, save=False, index=0)

    with pytest.raises(FileNotFoundError):
        assert_no_change(3, save=False, suffix="suffix")

    with pytest.raises(FileNotFoundError):
        assert_no_change(4, save=False, index=0, suffix="suffix")
        

def test__assert_no_change__save():
    with pytest.raises(AssertionError):
        assert_no_change(1, save=True)

    with pytest.raises(AssertionError):
        assert_no_change(2, save=True, index=0)

    with pytest.raises(AssertionError):
        assert_no_change(3, save=True, suffix="suffix")

    with pytest.raises(AssertionError):
        assert_no_change(4, save=True, index=0, suffix="suffix")
