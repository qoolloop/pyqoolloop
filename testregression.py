import inspect
import os
import pickle


def _get_function_info(depth=2):
    """
    Argument:
      depth -- (int) How much up the stack to look. -1 for the caller.

    Returns:
      A tuple with the following elements:
        - (str) name of module
        - (str) name of function
    """
    frame = inspect.currentframe()
    assert frame is not None, "Not supported on certain python implementations"

    for index in range(depth):
        frame = frame.f_back

    module_name = frame.f_globals['__name__']

    function_name = frame.f_code.co_name

    return module_name, function_name

    
#TODO: Get module name and function name from stack https://stackoverflow.com/questions/5067604/determine-function-name-from-within-that-function-without-using-traceback
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
    module_name, function_name = _get_function_info(depth=depth + 1)
    filename = os.path.join(
        '_testregression', module_name + '.' + function_name)

    if index is not None:
        filename += '#%g' % index

    if suffix is not None:
        assert suffix[0] == '.'
        filename += '=' + suffix

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
        value, save, index=None, suffix=None, depth=1):
    previous_value = _save_or_load(
        value, save, index=index, suffix=suffix, depth=depth + 1)

    assert previous_value == value
