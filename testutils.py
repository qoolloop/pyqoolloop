import sys
from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    Iterable,
    List,
    Protocol,
    Set,
    Tuple,
    TypeVar,
    Union,
)

import pylog
_logger = pylog.getLogger(__name__)


Operator = Callable[[Any, Any], bool]

_ObjectType = TypeVar('_ObjectType')


def eq(one: object, another: object) -> bool:
    """
    Function equivalent to the equals operator.

    :param one: One value to compare
    :param another: Another value to compare

    :returns: `True` if `one == another`.
    """
    return one == another


class _HasEquals(Protocol):
    def equals(self, value: object) -> bool:
        ...


def equals(one: _HasEquals, another: object) -> bool:  #TODO: rename `equals_method`
    """
    Function equivalent to the `equals()` method.

    :param one: Object with the `equals()` method.
    :param another: Value to compare with `one`.

    :returns: `True` if `one.equals(another)`.
    """
    return one.equals(another)


def equal_set(
        one_set: Collection[object],
        another_set: Collection[object],
        equals: Callable[[object, object], bool] = eq
) -> bool:  #TODO: reimplemet using `set()`
    """
    Check for equality between two iterables ignoring order
    
    Particularly for lists or unhashable sets

    :param one_set: An iterable to compare.
    :param another_set: Another iterable to compare.
    :param equals: The function to compare elements in the sets.

    :returns: `True` if the two iterables are equal.
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
                    _logger.info("Couldn't remove: %r / %d",
                                 each_another, len(another_set_copy))
                    return False
                # endtry
        # endif

    return len(another_set_copy) == 0


def _included_set(
        one_set: Iterable[Any],
        another_set: Iterable[Any],
        equals: Operator = eq
) -> bool:
    another_set = set(another_set)

    for each in one_set:
        if each not in another_set:
            _logger.info("%r not included", each)
            return False

        continue

    return True


def _included_dict(
        one: Dict[Any, Any], another: Dict[Any, Any], equals: Operator = eq
) -> bool:
    for each_key, each_value in one.items():
        if each_key not in another:
            _logger.info("Key %r not included", each_key)
            return False

        if not equals(each_value, another[each_key]):
            _logger.info(
                "Values %r and %r are not equal for key %r",
                each_value, another[each_key], each_key)
            return False

        continue

    return True


def included(
        one: Iterable[Any], another: Iterable[Any], equals: Operator = eq
) -> bool:
    """
    Check that all elements in one is included in the other

    :param one: Iterable or `dict` that could be included in `another`
    :param another: Iterable or `dict` that could include `one`.
    :param equals: Function to be used to compare values.

    :returns: Returns `True`, when elements in `one` are included in
        `another`.

    .. note::
      Same as `one_set <= another_set`, if both arguments are `set`s.
    """
    if isinstance(one, dict):
        assert isinstance(another, dict)
        return _included_dict(one, another, equals=equals)

    return _included_set(one, another, equals=equals)


def current_function_name(pop_stack: int = 0) -> str:
    """
    Get name of function on stack.

    :param pop_stack: How deep in the stack to look. `0` for direct caller.
      `1` for caller of caller.  #TODO: rename `depth`

    :returns: Name of function on stack.
    """
    # https://stackoverflow.com/a/13514318/2400328
    return sys._getframe(pop_stack + 1).f_code.co_name


def combine_lists(
        *args: Union[object, Iterable[object]]) -> Iterable[object]:  #TODO: test
    """
    Create a list of lists by taking one element from each of the arguments.
    Can be used to create test parameters from combinations.

    If one of the arguments is not iterable, it will be treated as though
    it was in a list.

    #TODO: test example
      >>> combine_lists((a, b), (c, d))
      [[a, c], [a, d], [b, c], [b, d]]
      >>> combline_lists((a, b), c)
      [[a, c], [b, c]]
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


def list_list_to_tuple_set(
        list_list: List[List[_ObjectType]]) -> Set[Tuple[_ObjectType, ...]]:
    """
    Convert list of lists to set of tuples.

    :param list_list: List of lists

    :returns: Set of tuples.
    """
    result = set()
    for each_list in list_list:
        result.add(tuple(each_list))

    return result
