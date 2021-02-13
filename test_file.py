from . import file

import os
from mypy_extensions import (
    DefaultNamedArg,
)
import pytest
import tempfile
from typing import (
    Any,
    Callable,
)

import pylog
logger = pylog.getLogger(__name__)


LoadFunc = Callable[[str, str, DefaultNamedArg(bool, 'raise_exception')], Any]

DumpFunc = Callable[[str, str, Any, DefaultNamedArg(bool, 'overwrite')], None]


def _test__no_file__no_exception(load_func: LoadFunc) -> None:
    read = load_func('', 'non-existent-file.pp')
    assert read is None


def _test__no_file__exception(load_func: LoadFunc) -> None:
    with pytest.raises(FileNotFoundError):
        read = load_func('', 'non-existent-file.pp',
                         raise_exception=True)
        assert read is None
    # endwith


def test_load_pickle__no_file__no_exception() -> None:
    _test__no_file__no_exception(file.load_pickle)
    

def test_load_text__no_file__no_exception() -> None:
    _test__no_file__no_exception(file.load_text)
    

def test_load_pickle__no_file__exception() -> None:
    _test__no_file__exception(file.load_pickle)
    

def test_load_text__no_file__exception() -> None:
    _test__no_file__exception(file.load_text)
    

load_dump_parameters = ("load_func, dump_func, value", (
    (file.load_pickle, file.dump_pickle, {'key': 11}),
    (file.load_text, file.dump_text, 'text'),
))

@pytest.mark.parametrize(*load_dump_parameters)
def test__no_destination(
        load_func: LoadFunc, dump_func: DumpFunc, value: Any) -> None:

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
    

@pytest.mark.parametrize(*load_dump_parameters)
def test__destination_exists__no_exception(
        load_func: LoadFunc, dump_func: DumpFunc, value: Any) -> None:

    f, temp_filename = tempfile.mkstemp()
    os.close(f)

    dump_func('', temp_filename, value, overwrite=True)

    try:
        read = load_func('', temp_filename)

    finally:
        os.remove(temp_filename)

    assert read == value
    

@pytest.mark.parametrize(*load_dump_parameters)
def test__destination_exists__exception(
        load_func: LoadFunc, dump_func: DumpFunc, value: Any) -> None:

    f, temp_filename = tempfile.mkstemp()
    os.close(f)

    with pytest.raises(FileExistsError):
        dump_func('', temp_filename, value)

    os.remove(temp_filename)
