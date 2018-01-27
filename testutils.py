from .database import transaction

import sys

import pylog
logger = pylog.getLogger(__name__)


def eq(one, another):
    return one == another


def equals(one, another):
    return one.equals(another)


def equal_set(one_set, another_set, equals=eq):
    """
    Check for equality between two iterables ignoring order
    
    Particularly for lists or unhashable sets
    """
    # Needs to be list to remove() from unhashable set
    another_set_copy = list(another_set)

    if len(one_set) != len(another_set):
        return False

    for each_one in one_set:
        for each_another in another_set_copy:
            if equals(each_one, each_another):
                try:
                    another_set_copy.remove(each_another)
                    break

                except (KeyError, ValueError):
                    logger.info("Couldn't remove: %r / %d",
                                each_another, len(another_set_copy))
                    return False
                # endtry
        # endif

    return len(another_set_copy) == 0


def current_function_name(pop_stack=0):
    # https://stackoverflow.com/a/13514318/2400328
    return sys._getframe(pop_stack + 1).f_code.co_name
