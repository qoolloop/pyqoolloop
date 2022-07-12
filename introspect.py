"""Defines functions for introspection."""
from collections import namedtuple
import inspect
import os


FunctionInfo = namedtuple('FunctionInfo', ('module', 'function', 'dir'))


def get_function_info(depth: int = 1) -> FunctionInfo:
    """
    Get information about a function on the call stack.

    :param depth: -- How much up the stack to look. 1 for the caller.

    :return:
      A tuple with the following elements about the stack frame:
        - (str) name of module
        - (str) name of function
        - (str) name of the folder that has the module
    """
    frame = inspect.currentframe()
    assert frame is not None, "Not supported on certain python implementations"

    for _ in range(depth):
        frame = frame.f_back
        assert frame is not None

    module_name = frame.f_globals['__name__']

    function_name = frame.f_code.co_name

    dir_name = os.path.dirname(inspect.getfile(frame))

    return FunctionInfo(module_name, function_name, dir_name)
