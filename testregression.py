"""
Functions for testing for regression
"""
import os
import logging
import pickle
from typing import (
    Any,
    Optional,
    TypeVar,
    Union,
)

from . import introspect

import pylog  # pylint: disable=wrong-import-order
_logger = pylog.getLogger(__name__)


_ParameterType = TypeVar('_ParameterType')


def make_filename(
        *,
        index: Union[None, int, float] = None,
        suffix: Optional[str] = None,
        extension: str = '.p',
        depth: int = 1) -> str:
    """
    Make a filename in a subdirectory named `_testregression`
    to save values for regression test

    :param index: If specified, this value will be used as
        additional information to discriminate produced filename.
    :param suffix: Add this value to the base name of the filename.
    :param extension: Use this value as the extension of the filename.
    :param depth: How much up the stack to look. -1 for the caller.

    :returns: The created filename.

    .. note::
      Do not assume that the returned filename will be of a particular format
      other than the fact that `extension` will be used as the extension
      and the directory will be respected.
    """
    module_name, function_name, dir_name = introspect.get_function_info(
        depth=depth + 1)

    split_module = module_name.split('.')
    
    filename = os.path.join(
        dir_name, '_testregression', split_module[-1] + '.' + function_name)

    if index is not None:
        filename += '#%g' % index

    if suffix is not None:
        filename += '=' + suffix

    assert extension[0] == '.'
    filename += extension

    return filename


def _save_or_load(
        value: _ParameterType,
        save: bool,
        index: Union[None, int, float] = None,
        suffix: Optional[str] = None,
        depth: int = 1
) -> Any:

    class _CannotRead:  # pylint: disable=too-few-public-methods
        """ Something that should not exist elsewhere"""
    

    filename = make_filename(index=index, suffix=suffix, depth=depth + 1)

    try:
        with open(filename, 'rb') as read_file:
            previous_value = pickle.load(read_file)

    except IOError:
        if save:
            previous_value = _CannotRead

        else:
            raise

    if save:
        if previous_value != value:
            with open(filename, 'wb') as write_file:
                pickle.dump(value, write_file)

        return value

    return previous_value


def assert_no_change(
        value: object,
        *,  # too many positional arguments
        save: bool,
        index: Union[None, int, float] = None,
        suffix: Optional[str] = None,
        error_on_save: bool = True,
        depth: int = 1,
        _logger: logging.Logger = _logger
) -> None:
    """
    Assertion to check for regression.

    :param value: -- Value to check. Needs to be picklable.
    :param save: If `True`, `value` will be saved for later use.
        If `False`, `value` will be compared with the saved value.
    :param index: If specified, this value will be used as part of the filename
        to store values as additional information to discriminate the values.
    :param suffix: Extra `str` to discriminate the values.
    :param error_on_save: If `True`, raises class:`AssertionError` if
        `save == True`. This can be used to avoid leaving `save` as True.
    :para depth: (For internal use)  #TODO: rename with prefix `_`
    :para _logger: (For test) Logger to use.

    :raises AssertionError: If `value` does not equal saved value
    :raises FileNotFoundError: If `value` has not been saved before

    .. note::
      A folder named `_testregression` needs to exist in the same directory as
      the calling module.
      `value` will not be saved, if it is equal to the value that was saved
      previously. This is to avoid unnecessary commits to git.
      #TODO: Automatically create subdirectory?
    """
    if save:
        module_name, function_name, _ = introspect.get_function_info(
            depth=depth + 1)
        _logger.error(
            "`save` is `True` in %s (%s)", function_name, module_name)
        _logger.error(
            "`value` is %r", value)

    previous_value = _save_or_load(
        value, save, index=index, suffix=suffix, depth=depth + 1)

    assert previous_value == value, \
        "%r\nDOES NOT EQUAL%r\n" % (previous_value, value)

    if error_on_save:
        assert not save

    # endif
