"""Defines functions for processing Python internals."""
from collections import namedtuple
from importlib import import_module
from importlib.util import find_spec
import inspect
import logging
import os
from pathlib import Path
import re
from types import ModuleType
from typing import Optional


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


def autoimport_modules(
    package: str,
    *,
    ignore_pattern: str = '(test_.*)|(__.*)',
    logger: Optional[logging.Logger] = None,
) -> dict[str, ModuleType]:
    """
    Import modules in a package.

    :param package: Name of package to import modules from.
    :param ignore_pattern: Regular expression for names of modules to ignore.

    :returns: A `dict` of imported modules, with their names as keys.
    """
    spec = find_spec(package)
    assert spec is not None, f"'{package}' not found."
    assert (
        spec.submodule_search_locations is not None
    ), f"'{package}' was not a package."
    assert len(spec.submodule_search_locations) == 1
    path = Path(spec.submodule_search_locations[0])

    ignore = re.compile(ignore_pattern)

    imported = dict[str, ModuleType]()

    assert path.exists(), f"Path '{path.absolute()}' does not exist"
    for each_path in path.glob('*.py'):
        if ignore.match(each_path.name):
            continue

        module = import_module('.' + each_path.stem, package)
        if logger is not None:
            logger.info("Imported %s", module.__name__)

        imported[each_path.stem] = module

    return imported
