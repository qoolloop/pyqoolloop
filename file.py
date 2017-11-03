import os
import pickle


def get_file_path(filename):
    """
    Argument:
    filename -- Specify __file__
    """
    file_path = os.path.dirname(os.path.abspath(filename))
    return file_path
    

def load_pickle(file_path, filename):
    with open(os.path.join(file_path, filename), 'rb') as f:
        value = pickle.load(f)

    return value


def dump_pickle(file_path, filename, value):
    with open(os.path.join(file_path, filename), 'wb') as f:
        pickle.dump(value, f)
    # endwith
