"""Functions for testing for regression."""

from collections.abc import Callable
import logging
from pathlib import Path
import pickle
from typing import (
    Any,
    TypeVar,
)

from . import inspection

_logger = logging.getLogger(__name__)


_ParameterT = TypeVar('_ParameterT')


def make_filename(
    *,
    index: None | float = None,
    suffix: str | None = None,
    extension: str = '.p',
    depth: int = 1,
) -> str:
    """
    Make a filename in a subdirectory to save values for regression test.

    The subdirectory will be named `_testregression`.

    :param index: If specified, this value will be used as
        additional information to discriminate produced filename.
    :param suffix: Add this value to the base name of the filename.
    :param extension: Use this value as the extension of the filename.
    :param depth: How much up the stack to look. 1 for the caller.

    :return: The created filename.

    .. note::
      Do not assume that the returned filename will be of a particular format other
      than the fact that `extension` will be used as the extension and the directory
      will be respected.
    """
    module_name, function_name, dir_name = inspection.get_function_info(depth=depth + 1)

    split_module = module_name.split('.')

    filename = str(
        Path(dir_name) / '_testregression' / (split_module[-1] + '.' + function_name)
    )

    if index is not None:
        filename += f'#{index}'

    if suffix is not None:
        filename += '=' + suffix

    assert extension[0] == '.'
    filename += extension

    return filename


def make_filepath(
    *,
    index: None | float = None,
    suffix: str | None = None,
    extension: str = '.p',
    depth: int = 1,
) -> Path:
    """
    Make a filepath in a subdirectory to save values for regression test.

    The subdirectory will be named `_testregression`.

    :param index: If specified, this value will be used as
        additional information to discriminate produced filename.
    :param suffix: Add this value to the base name of the filename.
    :param extension: Use this value as the extension of the filename.
    :param depth: How much up the stack to look. 1 for the caller.

    :return: The created filepath.

    .. note::
      Do not assume that the filename of the returned filepath will be of a particular
      format other than the fact that `extension` will be used as the extension and the
      directory will be respected.
    """
    return Path(
        make_filename(index=index, suffix=suffix, extension=extension, depth=depth + 1)
    )


def _save_or_load(
    value: _ParameterT,
    *,
    save: bool,
    index: None | float = None,
    suffix: str | None = None,
    depth: int = 1,
) -> Any:  # noqa: ANN401
    class _CannotRead:
        """Something that should not exist elsewhere."""

    filepath = make_filepath(index=index, suffix=suffix, depth=depth + 1)

    try:
        with Path.open(filepath, 'rb') as read_file:
            previous_value = pickle.load(read_file)  # noqa: S301

    except OSError:
        if save:
            previous_value = _CannotRead

        else:
            raise

    if save:
        if previous_value != value:
            with Path.open(filepath, 'wb') as write_file:
                pickle.dump(value, write_file)

        return value

    return previous_value


def _equals(one: object, another: object) -> bool:
    return one == another


def assert_no_change(  # noqa: PLR0913  # FUTURE: Until keyword arguments are handled separately
    value: object,
    *,
    save: bool,
    index: None | float = None,
    suffix: str | None = None,
    error_on_save: bool = True,
    equals: Callable[[object, object], bool] = _equals,
    _depth: int = 1,
    _logger: logging.Logger = _logger,
) -> None:
    """
    Check for regression with assertion.

    :param value: -- Value to check. Needs to be picklable.
    :param save: If `True`, `value` will be saved for later use.
        If `False`, `value` will be compared with the saved value.
    :param index: If specified, this value will be used as part of the filename
        to store values as additional information to discriminate the values.
    :param suffix: Extra `str` to discriminate the values.
    :param error_on_save: If `True`, raises class:`AssertionError` if
        `save == True`. This can be used to avoid leaving `save` as True.
    :param equals: Function to check that values are equal.
    :param _depth: (For internal use)
    :param _logger: (For test) Logger to use.

    :raise AssertionError: If `value` does not equal saved value
    :raise FileNotFoundError: If `value` has not been saved before

    .. note::
      A folder named `_testregression` needs to exist in the same directory as
      the calling module.
      `value` will not be saved, if it is equal to the value that was saved
      previously. This is to avoid unnecessary commits to git.
    """
    # FUTURE: Automatically create subdirectory?
    if save:
        module_name, function_name, _ = inspection.get_function_info(depth=_depth + 1)
        _logger.error("`save` is `True` in %s (%s)", function_name, module_name)
        _logger.error("`value` is %r", value)

    previous_value = _save_or_load(
        value, save=save, index=index, suffix=suffix, depth=_depth + 1
    )

    assert equals(previous_value, value), (
        f"{previous_value!r}\nDOES NOT EQUAL{value!r}\n"
    )

    if error_on_save:
        assert not save

    # endif
