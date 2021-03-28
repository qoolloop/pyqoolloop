"""
Test for `file` module.
"""
import os
import tempfile
from typing import (
    Any,
    Callable,
)

from mypy_extensions import (
    DefaultNamedArg,
)
import pytest

from . import file

import pylog  # pylint: disable=wrong-import-order
logger = pylog.getLogger(__name__)


LoadFunc = Callable[[str, str, DefaultNamedArg(bool, 'raise_exception')], Any]

DumpFunc = Callable[[str, str, Any, DefaultNamedArg(bool, 'overwrite')], None]


parametrize__load_dump = pytest.mark.parametrize(
    "load_func, dump_func, value",
    (
        (file.load_pickle, file.dump_pickle, {'key': 11}),
        (file.load_text, file.dump_text, 'text'),
    )
)


def _test__no_file__no_exception(load_func: LoadFunc) -> None:
    """
    Subtest to check that no exception is raised
    """
    read = load_func('', 'non-existent-file.pp')
    assert read is None


def _test__no_file__exception(load_func: LoadFunc) -> None:
    """
    Subtest to check that `FileNotFoundError` is raised when the
    `raise_exception` argument is `True`
    """
    with pytest.raises(FileNotFoundError):
        read = load_func('', 'non-existent-file.pp',
                         raise_exception=True)
        assert read is None
    # endwith


@parametrize__load_dump
def test__load__no_file__no_exception(
        load_func: LoadFunc, dump_func: DumpFunc, value: Any) -> None:
    """
    Test load functions that no exception is raised with default argument
    """
    # pylint: disable=unused-argument # dump_func, value
    _test__no_file__no_exception(load_func)
    

@parametrize__load_dump
def test_load_pickle__no_file__exception(
        load_func: LoadFunc, dump_func: DumpFunc, value: Any) -> None:
    """
    Test load functions that exception is raised when the `raise_exception`
    argument is `True`
    """
    # pylint: disable=unused-argument # dump_func, value
    _test__no_file__exception(load_func)
    

@parametrize__load_dump
def test__regular(
        load_func: LoadFunc, dump_func: DumpFunc, value: Any) -> None:
    """
    Test regular dump and load sequence.
    """
    temp_dir_name = tempfile.mkdtemp()
    try:
        filename = 'filename'

        dump_func(temp_dir_name, filename, value)

        try:
            read = load_func(temp_dir_name, filename)

        finally:
            os.remove(os.path.join(temp_dir_name, filename))

        assert read == value

    finally:
        os.rmdir(temp_dir_name)

    # endtry
    

@parametrize__load_dump
def test__destination_exists__no_exception(
        load_func: LoadFunc, dump_func: DumpFunc, value: Any) -> None:
    """
    Test that exception is not raised if the `overwrite` argument is `True`.
    """
    temp_file, temp_filename = tempfile.mkstemp()
    os.close(temp_file)

    try:
        dump_func('', temp_filename, value, overwrite=True)

        read = load_func('', temp_filename)

    finally:
        os.remove(temp_filename)

    assert read == value
    

@parametrize__load_dump
def test__destination_exists__exception(
        load_func: LoadFunc, dump_func: DumpFunc, value: Any) -> None:
    """
    Test that `FileExistsError` is raised when destination file already
    exists.
    """
    # pylint: disable=unused-argument # load_func

    temp_file, temp_filename = tempfile.mkstemp()
    os.close(temp_file)

    try:
        with pytest.raises(FileExistsError):
            dump_func('', temp_filename, value)

    finally:
        os.remove(temp_filename)

    # endtry
