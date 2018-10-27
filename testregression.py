import os
import pickle


#TODO: Get module name and function name from stack https://stackoverflow.com/questions/5067604/determine-function-name-from-within-that-function-without-using-traceback
def make_filename(
        module_name, function_name, *, index=None, suffix=None, extension='.p'):
    """
    Arguments:
      index -- (optional: int/float) If specified, this value will be used as
        additional information to discriminate produced filename.
      suffix -- (str) Add this value to the base name of the filename.
      extension -- (str) Use this value as the extension of the filename.

    Notes:
      Do not assume that the returned filename will be of a particular format
      other than the fact that `extension` will be used as the extension
      and the directory will be respected.
    """
    filename = os.path.join(
        '_testregression', module_name + '.' + function_name)

    if index is not None:
        filename += '#%g' % index

    if suffix is not None:
        filename += '=' + suffix

    filename += extension

    return filename


def _save_or_load(value, save, module_name, function_name, index):

    filename = make_filename(module_name, function_name, index=index)

    if save:
        with open(filename, 'wb') as f:
            pickle.dump(value, f)

        return value

    else:
        with open(filename, 'rb') as f:
            previous_value = pickle.load(f)

        return previous_value


def assert_no_change(value, save, module_name, function_name, index=None):
    previous_value = _save_or_load(
        value, save, module_name, function_name, index)

    assert previous_value == value
