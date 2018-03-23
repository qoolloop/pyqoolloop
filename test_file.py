from . import file

import os
import pytest
import tempfile

import pylog
logger = pylog.getLogger(__name__)


def _test__no_file__no_exception(load_func):
    read = load_func('', 'non-existent-file.pp')
    assert read is None


def _test__no_file__exception(load_func):
    with pytest.raises(FileNotFoundError):
        read = load_func('', 'non-existent-file.pp',
                         raise_exception=True)
        assert read is None
    # endwith


def test_load_pickle__no_file__no_exception():
    _test__no_file__no_exception(file.load_pickle)
    

def test_load_text__no_file__no_exception():
    _test__no_file__no_exception(file.load_text)
    

def test_load_pickle__no_file__exception():
    _test__no_file__exception(file.load_pickle)
    

def test_load_text__no_file__exception():
    _test__no_file__exception(file.load_text)
    

@pytest.mark.parametrize("load_func, dump_func, value", (
    (file.load_pickle, file.dump_pickle, {'key': 11}),
    (file.load_text, file.dump_text, 'text'),
))
def test__no_destination(load_func, dump_func, value):

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
    

@pytest.mark.parametrize("load_func, dump_func, value", (
    (file.load_pickle, file.dump_pickle, {'key': 11}),
    (file.load_text, file.dump_text, 'text'),
))
def test__destination_exists__no_exception(load_func, dump_func, value):

    f, temp_filename = tempfile.mkstemp()
    os.close(f)

    dump_func('', temp_filename, value, overwrite=True)

    try:
        read = load_func('', temp_filename)

    finally:
        os.remove(temp_filename)

    assert read == value
    

@pytest.mark.parametrize("load_func, dump_func, value", (
    (file.load_pickle, file.dump_pickle, {'key': 11}),
    (file.load_text, file.dump_text, 'text'),
))
def test__destination_exists__exception(load_func, dump_func, value):

    f, temp_filename = tempfile.mkstemp()
    os.close(f)

    with pytest.raises(FileExistsError):
        dump_func('', temp_filename, value)

    os.remove(temp_filename)
