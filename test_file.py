from . import file

import os
import pytest
import tempfile


def test_load_pickle__no_file__no_exception():
    read = file.load_pickle('', 'non-existent-file.pp')
    assert read is None


def test_load_pickle__no_file__exception():
    with pytest.raises(FileNotFoundError):
        read = file.load_pickle('', 'non-existent-file.pp',
                                raise_exception=True)
        assert read is None
    # endwith


def test_dump_pickle__no_destination():

    temp_dir_name = tempfile.mkdtemp()
    try:
        filename = 'filename.p'

        value = {'key': 11}
        file.dump_pickle(temp_dir_name, filename, value)

        try:
            read = file.load_pickle(temp_dir_name, filename)

        finally:
            os.remove(os.path.join(temp_dir_name, filename))

        assert read == value

    finally:
        os.rmdir(temp_dir_name)
    # endtry
