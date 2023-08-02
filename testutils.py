"""Module with useful functions for unit testing."""
import inspect
from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    Hashable,
    Iterable,
    Set,
    Union,
)

from typing_extensions import Protocol

import logging  # pylint: disable=wrong-import-order

_logger = logging.getLogger(__name__)


Operator = Callable[[Any, Any], bool]


def eq_operator(one: object, another: object) -> bool:
    """
    Compare whether one value equals another.

    Function equivalent to the equals (`__eq__`) operator.

    :param one: One value to compare
    :param another: Another value to compare

    :returns: `True` if `one == another`.
    """
    return one == another


class _HasEquals(Protocol):  # pylint: disable=too-few-public-methods
    def equals(self, value: object) -> bool:
        """
        Comparison for equality.

        :param another: Value to compare with `self`.

        :returns: `True` if `self` equals `value`.
        """


def equals_method(one: _HasEquals, another: object) -> bool:
    """
    Compare whether one value equals another.

    Function equivalent to the `equals()` method.

    :param one: Object with the `equals()` method.
    :param another: Value to compare with `one`.

    :returns: `True` if `one.equals(another)`.
    """
    return one.equals(another)


def equal_set(
    one_set: Collection[object],
    another_set: Collection[object],
    equals: Callable[
        [object, object], bool
    ] = eq_operator,  # pylint: disable=redefined-outer-name
) -> bool:  # FUTURE: reimplement using `set()`
    """
    Check for equality between two iterables ignoring order.

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
                    _logger.info(
                        "Couldn't remove: %r / %d", each_another, len(another_set_copy)
                    )
                    return False
                # endtry
        # endif

    return len(another_set_copy) == 0


def _included_set(
    one_set: Iterable[Any],
    another_set: Iterable[Any],
    equals: Operator = eq_operator,  # pylint: disable=redefined-outer-name
) -> bool:
    def _iterable_in(each: Any, another_set: Iterable[Any]) -> bool:
        for other in another_set:
            if equals(each, other):
                return True

        return False

    def _set_in(each: Any, another_set: set[Any]) -> bool:
        return each in another_set

    if equals == eq_operator:  # pylint: disable=comparison-with-callable
        is_in = _set_in

    else:
        is_in = _iterable_in

    another_set = set(another_set)

    for each in one_set:
        if not is_in(each, another_set):
            _logger.info("%r not included", each)
            return False

        continue

    return True


def _included_dict(
    one: Dict[Any, Any],
    another: Dict[Any, Any],
    equals: Operator = eq_operator,  # pylint: disable=redefined-outer-name
) -> bool:
    for each_key, each_value in one.items():
        if each_key not in another:
            _logger.info("Key %r not included", each_key)
            return False

        if not equals(each_value, another[each_key]):
            _logger.info(
                "Values %r and %r are not equal for key %r",
                each_value,
                another[each_key],
                each_key,
            )
            return False

        continue

    return True


def included(
    one: Iterable[Any],
    another: Iterable[Any],
    equals: Operator = eq_operator,  # pylint: disable=redefined-outer-name
) -> bool:
    """
    Check that all elements in one is included in the other.

    :param one: Iterable or `dict` that could be included in `another`
    :param another: Iterable or `dict` that could include `one`.
    :param equals: Function to be used to compare values (not keys).

    :returns: Returns `True`, when elements in `one` are included in
        `another`.

    .. note::
      Same as `one_set <= another_set`, if both arguments are `set` s.
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

    :raises AssertionError: `pop_stack` is too large.
    """
    # https://stackoverflow.com/a/13514318/2400328
    frame = inspect.currentframe()
    assert frame is not None
    for _ in range(pop_stack + 1):
        frame = frame.f_back
        assert frame is not None

    return frame.f_code.co_name


def combine_lists(
    *args: Union[object, Iterable[object]], raise_if_empty: bool = True
) -> list[object]:
    r"""
    Create a list of entries created by taking one element from each of the arguments.

    Can be used to create test parameters from combinations.

    If one of the arguments is not an iterable, it will be treated as though
    it was in a list.

    If both elements in the arguments are lists, the result will be a
    concatenation.

    If one of the elements is a list and the other is not, the non-list element
    will be prefixed or appended to the list.

    If both elements are not lists, a list will be created with both elments.

    If there is only one argument, that argument will be returned as is.

      >>> to_set( combine_lists(['a', 'b'], ['c', 'd']) ) == \
      ...  to_set( [['a', 'c'], ['a', 'd'], ['b', 'c'], ['b', 'd']] )
      True
      >>> to_set( combine_lists(['a', 'b'], 'c') ) == \
      ...  to_set( [['a', 'c'], ['b', 'c']] )
      True

    :param \*args: Lists to combine
    :param raise_if_empty: If `True`, raise an exception if the result is
      empty.

    :return: combined result.

    :raises AssertionError: The result is empty and
      `raise_if_empty` was `True` or omitted.
    """
    assert len(args) >= 1

    if isinstance(args[0], list):
        args0 = args[0]

    else:
        args0 = [args[0]]

    if len(args) == 1:
        result = list(args0)

    else:
        one_list = args0
        another_list = combine_lists(*args[1:], raise_if_empty=raise_if_empty)

        result = []
        for another in another_list:
            if not isinstance(another, list):
                another = [another]

            for one in one_list:
                if not isinstance(one, list):
                    one = [one]

                else:
                    one = list(one)  # need to make copy not to modify original

                one.extend(another)

                result.append(one)
            # endfor
        # endfor

    if raise_if_empty:
        for _ in result:  # `result` is `Iterable`
            return result
        # endfor

        raise AssertionError("Empty result")

    return result


def to_set(iterable: Iterable[Hashable]) -> Set[Hashable]:
    """
    Convert iterable to set.

    If elements of the iterable are also iterable (may not be hashable),
    they will be converted to tuples.

    :param iterable: Iterable.

    :returns: Resulting set.

    .. note:: This is convenient for use with `@pytest.mark.parametrize`.
    """
    result = set()
    for each in iterable:
        if isinstance(each, Hashable):
            result.add(each)

        else:
            result.add(tuple(each))

    return result
