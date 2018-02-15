import os
import pickle


def get_file_path(filename):
    """
    Argument:
    filename -- Specify __file__
    """
    file_path = os.path.dirname(os.path.abspath(filename))
    return file_path
    

def load_pickle(file_path, filename, raise_exception=False):
    try:
        with open(os.path.join(file_path, filename), 'rb') as f:
            value = pickle.load(f)

        return value

    except:
        if raise_exception:
            raise

        return None
    # endtry
    

def dump_pickle(file_path, filename, value):
    with open(os.path.join(file_path, filename), 'wb') as f:
        pickle.dump(value, f)
    # endwith


def load_text(file_path, filename):
    with open(os.path.join(file_path, filename), 'rb') as f:
        return f.read()
    # endwith


def dump_text(file_path, filename, value):
    with open(os.path.join(file_path, filename), 'wb') as f:
        f.write(value)
    # endwith


def list_directories(path, exclusion=()):
    exclusion = set(exclusion)
    
    result = []
    for each in os.scandir(path):
        if each.is_dir() and (each.name not in exclusion):
            result.append(each.name)
        # endif

    return result
