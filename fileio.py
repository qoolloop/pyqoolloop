"""
Module for file manipulation.

.. note::
  Note that reading pickle files from an unknown source can be a security risk.
"""
import os
import pickle
from typing import (
    Any,
    IO,
    Iterable,
    List,
    Optional,
    overload,
    Union,
)


@overload
def get_directory(
        path: str
) -> str:
    ...


@overload
def get_directory(
        path: bytes
) -> bytes:
    ...


@overload
def get_directory(
        path: os.PathLike[str]
) -> os.PathLike[str]:
    ...


@overload
def get_directory(
        path: os.PathLike[bytes]
) -> os.PathLike[bytes]:
    ...


def get_directory(
        path: Union[str, bytes, os.PathLike[str], os.PathLike[bytes]]
) -> Union[str, bytes, os.PathLike[str], os.PathLike[bytes]]:  #TODO: accept PathLike
    """
    Get directory of file.

    :param filename: Path to file. Specify `__file__`, for example.
    :return: Path to directory of the file.
    """
    if isinstance(path, os.PathLike):
        return path.parent.resolve()

    else:
        directory_path = os.path.dirname(os.path.abspath(path))
        return directory_path


def _write_mode(
        overwrite: bool = False
) -> str:
    mode = 'w' if overwrite else 'x'
    return mode


def _join_path(file_path: Union[str, Iterable[str]]) -> str:
    if isinstance(file_path, str):
        return file_path

    return os.path.join(*file_path)


def open_write_text(
        file_path: Union[str, Iterable[str]],
        *,
        overwrite: bool = False
) -> IO[str]:
    """
    Open text file for writing.

    Same as standard `open()`, but with a different way to specify arguments.

    :param file_path: Path to file. If iterable of `str`, the elements will be
      joined.
    :param overwrite: `True` to allow overwriting existing file.

    :return: File object that is opened.

    :raises FileExistsError: Raised when file already exists and
      `overwrite` is `False`
    """
    mode = _write_mode(overwrite=overwrite)

    full_path = _join_path(file_path)
    
    return open(full_path, mode)  # pylint: disable=consider-using-with


def open_write_binary(
        file_path: Union[str, Iterable[str]],
        *,
        overwrite: bool = False
) -> IO[bytes]:
    """
    Open binary file for writing.

    Same as standard `open()`, but with a different way to specify arguments.

    :param file_path: Path to file. If iterable of `str`, the elements will be
      joined.
    :param overwrite: `True` to allow overwriting existing file.

    :return: File object that is opened.

    :raises FileExistsError: Raised when file already exists and
      `overwrite` is `False`
    """
    mode = _write_mode(overwrite=overwrite)

    full_path = _join_path(file_path)
    
    return open(full_path, mode + 'b')  # pylint: disable=consider-using-with


def open_read_text(
        file_path: Union[str, Iterable[str]],
) -> IO[str]:
    """
    Open text file for reading.

    Same as standard `open()`, but with a different way to specify arguments.

    :param file_path: Path to file. If iterable of `str`, the elements will be
      joined.

    :return: File object that is opened.
    """
    full_path = _join_path(file_path)
    
    return open(full_path, 'r')  # pylint: disable=consider-using-with


def open_read_binary(
        file_path: Union[str, Iterable[str]],
) -> IO[bytes]:
    """
    Open binary file for reading.

    Same as standard `open()`, but with a different way to specify arguments.

    :param file_path: Path to file. If iterable of `str`, the elements will be
      joined.

    :return: File object that is opened.
    """
    full_path = _join_path(file_path)
    
    return open(full_path, 'rb')  # pylint: disable=consider-using-with


def load_pickle(
        file_path: Union[str, Iterable[str]],
        *,
        raise_exception: bool = False
) -> Any:
    """
    Load from pickle file.

    :param file_path: Path to directory. If `Iterable`, the elements will be
      joined.
    :param filename: Name of file in `file_path` directory.
    :param raise_exception: `True` to raise exception on error, such as
      file not found. If `False`, this function will return `None` on error.

    :return: loaded value

    :raise FileNotFoundError: File is not found
    :raise other: Other file related errors.
    """
    try:
        with open_read_binary(file_path) as read_file:
            value = pickle.load(read_file)

        return value

    except:  # noqa: E722
        if raise_exception:
            # Python 3 raises FileNotFoundError
            # https://stackoverflow.com/a/15032444/2400328
            raise

        return None
    # endtry


def dump_pickle(
        file_path: Union[str, Iterable[str]],
        value: object,
        *,
        overwrite: bool = False
) -> None:
    """
    Save to pickle file.

    :param file_path: Path to directory. If `Iterable` the elements will be
      joined
    :param filename: Name of file in `file_path` directory.
    :param overwrite: `True` to write over existing file.

    :raises FileExistsError: Raised when file already exists and
      `overwrite` is `False`
    """
    with open_write_binary(file_path, overwrite=overwrite) \
         as write_file:
        pickle.dump(value, write_file)
    # endwith


def load_text(
    file_path: Union[str, Iterable[str]], *, raise_exception: bool = False
) -> Optional[str]:
    """
    Read text from file.

    :param file_path: Path to directory. If `Iterable`, the elements will be
      joined.
    :param filename: Name of file in `file_path` directory.
    :param raise_exception: `True` to raise exception on error, such as
      file not found. If `False`, this function will return `None` on error.

    :raise FileNotFoundError: File is not found
    :raise other: Other file related errors.

    :return: Text read from file. `None` if file doesn't exist and
      `file_`raise_exception` is `False`.
    """
    try:
        with open_read_text(file_path) as read_file:
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
        file_path: Union[str, Iterable[str]],
        value: str,
        *,
        overwrite: bool = False
) -> None:
    """
    Save text to file.

    :param file_path: Path to directory. If `Iterable` the elements will be
      joined
    :param filename: Name of file in `file_path`.
    :param value: Text to save.
    :param overwrite: `True` to write over existing file.

    :raises FileExistsError: Raised when file already exists and
      `overwrite` is `False`
    """
    with open_write_text(file_path, overwrite=overwrite) as write_file:
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
