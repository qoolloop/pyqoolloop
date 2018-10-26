import os
import pickle


def _save_or_load(value, save, module_name, function_name, index):

    def _make_filename(module_name, function_name, index):
        filename = os.path.join(
            '_testregression', module_name + '_' + function_name)
        if index is not None:
            filename += '_%d' % index

        filename += '.p'

        return filename


    filename = _make_filename(module_name, function_name, index)

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
