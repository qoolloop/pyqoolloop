import inspect
import os
import pickle

import pylog
logger = pylog.getLogger(__name__)


def _get_function_info(depth=2):
    """
    Argument:
      depth -- (int) How much up the stack to look. -1 for the caller.

    Returns:
      A tuple with the following elements about the stack frame:
        - (str) name of module
        - (str) name of function
        - (str) name of the folder that has the module
    """
    frame = inspect.currentframe()
    assert frame is not None, "Not supported on certain python implementations"

    for index in range(depth):
        frame = frame.f_back

    module_name = frame.f_globals['__name__']

    function_name = frame.f_code.co_name

    dir_name = os.path.dirname(inspect.getfile(frame))

    return module_name, function_name, dir_name

    
def make_filename(*, index=None, suffix=None, extension='.p', depth=1):
    """
    Make a filename in a subdirectory named `_testregression`
    to save values for regression test

    Arguments:
      index -- (optional: int/float) If specified, this value will be used as
        additional information to discriminate produced filename.
      suffix -- (str) Add this value to the base name of the filename.
      extension -- (str) Use this value as the extension of the filename.
      depth -- (int) How much up the stack to look. -1 for the caller.

    Notes:
      Do not assume that the returned filename will be of a particular format
      other than the fact that `extension` will be used as the extension
      and the directory will be respected.
    """
    module_name, function_name, dir_name = _get_function_info(depth=depth + 1)
    filename = os.path.join(
        dir_name, '_testregression', module_name + '.' + function_name)

    if index is not None:
        filename += '#%g' % index

    if suffix is not None:
        filename += '=' + suffix

    assert extension[0] == '.'
    filename += extension

    return filename


def _save_or_load(value, save, index=None, suffix=None, depth=1):

    filename = make_filename(index=index, suffix=suffix, depth=depth + 1)

    if save:
        with open(filename, 'wb') as f:
            pickle.dump(value, f)

        return value

    else:
        with open(filename, 'rb') as f:
            previous_value = pickle.load(f)

        return previous_value


def assert_no_change(
        value,
        save,
        index=None,
        suffix=None,
        error_on_save=True,
        depth=1):
    """
    Regression assertion

    Arguments:
      value -- value to check
      save -- (bool) if True, `value` will be saved for use later.
        If False, `value` will be compared with the saved value.
      index -- (optional: int/float) If specified, this value will be used as
        additional information to discriminate values.
      suffix -- (str) extra `str` to discriminate values.
      error_on_save -- (bool) if True, raises AssertionError, if
        `save == True`. This can be used to avoid leaving `save` as True.

    Raises:
      AssertionError -- if `value` does not equal saved value
      FileNotFoundError -- if `value` has not been saved before

    Notes:
      A folder named `_testregression` needs to exist in the same folder as
      the calling module.
    """
    if save:
        module_name, function_name, _ = _get_function_info(depth=depth)
        logger.error(
            "`save` is True in %s (%s)" % (function_name, module_name))
        logger.error(
            "`value` is %r" % (value,))

    previous_value = _save_or_load(
        value, save, index=index, suffix=suffix, depth=depth + 1)

    assert previous_value == value, \
        "%r\nDOES NOT EQUAL%r\n" % (previous_value, value)

    if error_on_save:
        assert not save

    return
