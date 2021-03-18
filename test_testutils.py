import pytest
from typing import (
    Any,
    Iterable,
    Sequence,
    Union,
)

from pyexception.exception import RecoveredException
from pyexception.testutils import raises

from .testutils import (
    combine_lists,
    current_function_name,
    EmptyResult,
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
        one: Iterable[Any], another: Iterable[Any], result: bool) -> None:
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
        one: Iterable[Any], another: Iterable[Any], result: bool) -> None:

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
def test_combine_lists(
        expected_result: Sequence[Iterable[object]],
        args: Iterable[Union[object, Iterable[object]]]
) -> None:
    expected_set = to_set(expected_result)

    if (len(expected_result) == 0):
        with raises(RecoveredException, EmptyResult):
            result_list = combine_lists(*args)

        with raises(RecoveredException, EmptyResult):
            result_list = combine_lists(*args, raise_if_empty=True)

    else:
        for raise_if_empty in [True, False]:
            result_list = combine_lists(*args, raise_if_empty=raise_if_empty)
            
            result_set = to_set(result_list)

            assert expected_set == result_set

    return


def test__current_function_name():

    def _inner_function():
        assert '_inner_function' == current_function_name()
        assert 'test__current_function_name' == current_function_name(1)


    _inner_function()
