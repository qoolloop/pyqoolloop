"""Tests for `testutils` module."""
from typing import (
    Any,
    Iterable,
    List,
    Sequence,
    Union,
)

import pytest

from .testutils import (
    combine_lists,
    current_function_name,
    included,
    to_set,
)


@pytest.mark.parametrize("one, another, result", (
    ([], [], True),
    ([], [1], True),
    ([1], [], False),
    ([1], [1], True),
    (["1"], ["1"], True),
    (["1"], ["1", 1], True),
    (["1", 1], ["1"], False),

    (dict(), dict(), True),
    (dict(), dict(a=1), True),
    (dict(a=1), dict(), False),
    (dict(a=1), dict(a=1), True),
    (dict(a=1), dict(a="1"), False),
    (dict(a="1"), dict(a="1"), True),
    (dict(a=1), dict(a="1"), False),
    (dict(a="1"), dict(a="1", bcd=1), True),
    (dict(a=1), dict(a="1", bcd=1), False),
    (dict(a="1", bcd=1), dict(a="1"), False),

    ({}, {}, True),
    ({}, {1: 1}, True),
    ({}, {"1": 1}, True),
    ({1: 1}, {}, False),
    ({1: 1}, {1: 1}, True),
    ({"1": 1}, {1: 1}, False),
    ({1: 1}, {"1": 1}, False),
    ({1: 1}, {1: "1"}, False),
    ({1: "1"}, {1: "1"}, True),
    ({"1": "1"}, {1: "1"}, False),
    ({1: "1"}, {"1": "1"}, False),
    ({1: 1}, {1: "1"}, False),
    ({1: "1"}, {1: "1", "bcd": 1}, True),
    ({"1": "1"}, {1: "1", "bcd": 1}, False),
    ({1: "1"}, {"1": "1", "bcd": 1}, False),
    ({1: 1}, {1: "1", "bcd": 1}, False),
    ({1: "1", "bcd": 1}, {1: "1"}, False),
))
def test__included(
        one: Iterable[Any], another: Iterable[Any], result: bool
) -> None:
    """Test for `included()`."""
    assert result == included(one, another)


@pytest.mark.parametrize("one, another, result", (
    ([], [], True),
    ([], [1], True),
    ([1], [], False),
    ([1], [1], True),
    (["1"], ["1"], True),
    (["1"], ["1", 1], True),
    (["1", 1], ["1"], True),  # not `False`

    (dict(), dict(), True),
    (dict(), dict(a=1), True),
    (dict(a=1), dict(), False),
    (dict(a=1), dict(a=1), True),
    (dict(a=1), dict(a="1"), True),  # not `False`
    (dict(a="1"), dict(a="1"), True),
    (dict(a=1), dict(a="1"), True),  # not `False`
    (dict(a="1"), dict(a="1", bcd=1), True),
    (dict(a=1), dict(a="1", bcd=1), True),  # not `False`
    (dict(a="1", bcd=1), dict(a="1"), False),

    ({}, {}, True),
    ({}, {1: 1}, True),
    ({}, {"1": 1}, True),
    ({1: 1}, {}, False),
    ({1: 1}, {1: 1}, True),
    ({"1": 1}, {1: 1}, False),
    ({1: 1}, {"1": 1}, False),
    ({1: 1}, {1: "1"}, True),  # not `False`
    ({1: "1"}, {1: "1"}, True),
    ({"1": "1"}, {1: "1"}, False),
    ({1: "1"}, {"1": "1"}, False),
    ({1: 1}, {1: "1"}, True),  # not `False`
    ({1: "1"}, {1: "1", "bcd": 1}, True),
    ({"1": "1"}, {1: "1", "bcd": 1}, False),
    ({1: "1"}, {"1": "1", "bcd": 1}, False),
    ({1: 1}, {1: "1", "bcd": 1}, True),  # not `False`
    ({1: "1", "bcd": 1}, {1: "1"}, False),
))
def test__included__equals(
        one: Iterable[Any], another: Iterable[Any], result: bool
) -> None:
    """Test for `included()` with `equals` argument specified."""

    def _str_equals(one: Any, another: Any) -> bool:
        return str(one) == str(another)
    

    assert result == included(one, another, equals=_str_equals)


@pytest.mark.parametrize("expected_result, args", [
    ([], ([],)),  # 1 empty argument
    ([1], ([1],)),  # 1 single entity argument
    ([1], (1,)),  # 1 single entity argument
    ([1, 2], ([1, 2],)),  # 1 two entity argument
    ([], ([], [])),
    ([], ([1], [])),
    ([], (1, [])),
    ([[1]], ([1], [()])),
    ([], ([], [2])),
    ([], ([], 2)),
    ([[2]], ([()], [2])),
    ([[2]], ([()], 2)),
    ([[3, 4]], ([[3]], [4])),
    ([[3, 4]], ([[3]], 4)),
    ([[3, 4]], (3, [4])),
    ([[3, 4]], (3, 4)),
    ([[5, 7], [5, 8]], ([5], [7, 8])),
    ([[5, 7], [5, 8]], (5, [7, 8])),
    ([[5, 8], [6, 8]], ([5, 6], [8])),
    ([[5, 8], [6, 8]], ([5, 6], 8)),
    ([[5, 7], [5, 8], [6, 7], [6, 8]], ([5, 6], [7, 8])),
    ([[5, 6, 10], [5, 6, 7, 8], [9, 10], [9, 7, 8]],
     ([(5, 6), 9], [10, (7, 8)])),
])
def test__combine_lists(
        expected_result: Sequence[Iterable[object]],
        args: Iterable[Union[object, Iterable[object]]]
) -> None:
    """Test for `combine_lists()`."""
    expected_set = to_set(expected_result)

    if len(expected_result) == 0:
        with pytest.raises(AssertionError):
            result_list = combine_lists(*args)

        with pytest.raises(AssertionError):
            result_list = combine_lists(*args, raise_if_empty=True)

    else:
        for raise_if_empty in [True, False]:
            result_list = combine_lists(*args, raise_if_empty=raise_if_empty)
            
            result_set = to_set(result_list)

            assert expected_set == result_set

    # enddef


@pytest.mark.parametrize('operand', (
    combine_lists('c', 'd'),
    [],
    [1],
))
def test__combine_lists__add(operand: List[object]) -> None:
    """Test that `+` operator works for result of `combine_lists()`."""
    # Just make sure addition works
    assert (combine_lists('a', 'b') + operand) is not None
    assert (operand + combine_lists('a', 'b')) is not None


def test__current_function_name() -> None:
    """Test for `current_function_name()`."""

    def _inner_function() -> None:
        assert current_function_name() == '_inner_function'
        assert current_function_name(1) == 'test__current_function_name'


    _inner_function()
