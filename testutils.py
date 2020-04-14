import sys

import pylog
logger = pylog.getLogger(__name__)


def eq(one, another):
    return one == another


def equals(one, another):
    return one.equals(another)


def equal_set(one_set, another_set, equals=eq):  #TODO: reimplemet using `set()`
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


def included(one_set, another_set, equals=eq):
    """
    Check that all elements in one set is included in the other set

    Arguments:
      one_set -- (iterable)
      another_set -- (iterable)
      equals -- (callable) function to see equality

    Returns:
      (bool) returns True, when elements in `one_set` are included in
        `another_set`.

    Notes:
      Same as `one_set <= another_set`, if both arguments are `set`s.
    """
    another_set = set(another_set)

    for each in one_set:
        if each not in another_set:
            logger.info("%r not included", each)
            return False

        continue

    return True


def current_function_name(pop_stack=0):
    # https://stackoverflow.com/a/13514318/2400328
    return sys._getframe(pop_stack + 1).f_code.co_name


def combine_lists(*args):
    """
    Create a list of lists by taking one element from each of the arguments.
    Can be used to create test parameters from combinations.
    """
    assert len(args) >= 1

    if len(args) == 1:
        return args[0]
    
    one_list = args[0]
    another_list = combine_lists(*args[1:])
                                  
    result = []
    for another in another_list:
        if not isinstance(another, (list, tuple)):
            another = [another]
            
        for one in one_list:
            if not isinstance(one, (list, tuple)):
                one = [one]
                
            elif isinstance(one, tuple):
                one = list(one)

            one.extend(another)

            result.append(one)
        # endfor
    # endfor

    return result


def list_list_to_tuple_set(list_list):
    result = set()
    for each_list in list_list:
        result.add(tuple(each_list))

    return result
