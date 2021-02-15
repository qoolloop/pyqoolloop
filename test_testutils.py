import pytest
from typing import (
    Any,
    Iterable,
    Union,
)

from .testutils import (
    combine_lists,
    included,
    list_list_to_tuple_set,
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
))
def test__included(
        one: Iterable[Any], another: Iterable[Any], result: bool) -> None:
    assert result == included(one, another)


@pytest.mark.parametrize("expected_result, one_list, another_list", [
    ([], [], []),
    ([], [1], []),
    ([[1]], [1], [()]),
    ([], [], [2]),
    ([[2]], [()], [2]),
    ([[3, 4]], [[3]], [4]),
    ([[5, 7], [5, 8], [6, 7], [6, 8]], [5, 6], [7, 8]),
    ([[5, 6, 10], [5, 6, 7, 8], [9, 10], [9, 7, 8]],
     [(5, 6), 9], [10, (7, 8)]),
])
def test_combine_lists(
        expected_result: Iterable[Iterable[object]],
        one_list: Union[object, Iterable[object]],
        another_list: Union[object, Iterable[object]]
) -> None:
    expected_set = list_list_to_tuple_set(expected_result)

    result_list = combine_lists(one_list, another_list)
    result_set = list_list_to_tuple_set(result_list)

    assert expected_set == result_set
