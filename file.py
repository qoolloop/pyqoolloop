"""
Note that reading pickle files from an unknown source can be a security risk.
"""
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
            # Python 3 raises FileNotFoundError
            # https://stackoverflow.com/a/15032444/2400328
            raise

        return None
    # endtry


def _check_overwrite(full_filename, overwrite):
    #TODO: Do something about race conditions with os.path.exists()=>Use 'x' for file mode. See encrypt

    if not overwrite and os.path.exists(full_filename):
        raise FileExistsError()
    # endif
    

def dump_pickle(file_path, filename, value, overwrite=False):
    full_filename = os.path.join(file_path, filename)

    _check_overwrite(full_filename, overwrite)

    with open(full_filename, 'wb') as f:
        pickle.dump(value, f)
    # endwith


def load_text(file_path, filename, raise_exception=False):
    try:
        with open(os.path.join(file_path, filename), 'r') as f:
            return f.read()
        # endwith

    except:
        if raise_exception:
            # Python 3 raises FileNotFoundError
            # https://stackoverflow.com/a/15032444/2400328
            raise

        return None
    # endtry


def dump_text(file_path, filename, value, overwrite=False):
    full_filename = os.path.join(file_path, filename)

    _check_overwrite(full_filename, overwrite)

    with open(full_filename, 'w') as f:
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
