"""
.. note::
  Note that reading pickle files from an unknown source can be a security risk.
"""
import os
import pickle
from typing import (
    Any,
    Iterable,
    List,
    Optional,
)


#TODO: rename `get_directory()`
def get_file_path(filename: str) -> str:  #TODO: rename `path`
    """
    Get directory of file.

    :param filename: Path to file. Specify `__file__`, for example.
    :return: Path to directory of the file.
    """
    file_path = os.path.dirname(os.path.abspath(filename))
    return file_path
    

def load_pickle(
        file_path: str, filename: str, raise_exception: bool = False
) -> Any:
    #TODO: Accept `None` for `filename` to specify file with `file_path`?
    """
    Load from pickle file.

    :param file_path: Path to directory.
    :param filename: Name of file in `file_path` directory.
    :param raise_exception: `True` to raise exception on error, such as
      file not found. If `False`, this function will return `None` on error.

    :return: loaded value

    :raise FileNotFoundError: File is not found
    :raise other: Other file related errors.
    """
    try:
        with open(os.path.join(file_path, filename), 'rb') as read_file:
            value = pickle.load(read_file)

        return value

    except:  # noqa: E722
        if raise_exception:
            # Python 3 raises FileNotFoundError
            # https://stackoverflow.com/a/15032444/2400328
            raise

        return None
    # endtry


def _check_overwrite(full_filename: str, overwrite: bool) -> None:
    #TODO: Do something about race conditions with os.path.exists()=>Use 'x' for file mode. See encrypt

    if not overwrite and os.path.exists(full_filename):
        raise FileExistsError()
    # endif
    

def dump_pickle(
        file_path: str, filename: str, value: object, overwrite: bool = False
) -> None:
    """
    Save to pickle file.

    :param file_path: Path to directory.
    :param filename: Name of file in `file_path` directory.
    :param overwrite: `True` to write over existing file.

    :raises FileExistsError: Raised when file already exists and
      `overwrite` is `False`
    """
    full_filename = os.path.join(file_path, filename)

    _check_overwrite(full_filename, overwrite)

    with open(full_filename, 'wb') as write_file:
        pickle.dump(value, write_file)
    # endwith


def load_text(
    file_path: str, filename: str, raise_exception: bool = False
) -> Optional[str]:
    #TODO: Accept `None` for `filename` to specify file with `file_path`?    
    """
    Read text from file.

    :param file_path: Path to directory.
    :param filename: Name of file in `file_path` directory.
    :param raise_exception: `True` to raise exception on error, such as
      file not found. If `False`, this function will return `None` on error.

    :raise FileNotFoundError: File is not found
    :raise other: Other file related errors.

    :return: Text read from file. `None` if file doesn't exist and
      `file_`raise_exception` is `False`.
    """
    try:
        with open(os.path.join(file_path, filename), 'r') as read_file:
            return read_file.read()
        # endwith

    except:  # noqa:E722
        if raise_exception:
            # Python 3 raises FileNotFoundError
            # https://stackoverflow.com/a/15032444/2400328
            raise

        return None
    # endtry


def dump_text(
        file_path: str, filename: str, value: str, overwrite: bool = False
) -> None:
    """
    Save text to file.

    :param file_path: Path to directory.
    :param filename: Name of file in `file_path`.
    :param value: Text to save.
    :param overwrite: `True` to write over existing file.

    :raises FileExistsError: Raised when file already exists and
      `overwrite` is `False`
    """
    full_filename = os.path.join(file_path, filename)

    _check_overwrite(full_filename, overwrite)

    with open(full_filename, 'w') as write_file:
        write_file.write(value)
    # endwith


def list_directories(
        path: str, exclusion: Iterable[str] = ()) -> List[str]:
    """
    List directories in directory.

    :param path: Path to directory.
    :param exclusion: Directories to ignore.  #TODO: rename `exclude`
    """
    exclusion = set(exclusion)
    
    result = []
    for each in os.scandir(path):
        if each.is_dir() and (each.name not in exclusion):
            result.append(each.name)
        # endif

    return result
