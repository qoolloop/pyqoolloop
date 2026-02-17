"""Tests for `testutils` module."""

from collections.abc import Iterable
from typing import (
    Any,
)

import pytest

from .testutils import (
    combine_lists,
    combine_tuples,
    current_function_name,
    equal_set,
    included,
)


@pytest.mark.parametrize(
    "one, another, result",
    [
        ([], [], True),
        ([], [1], True),
        ([1], [], False),
        ([1], [1], True),
        (["1"], ["1"], True),
        (["1"], ["1", 1], True),
        (["1", 1], ["1"], False),
        ({}, {}, True),
        ({}, {"a": 1}, True),
        ({"a": 1}, {}, False),
        ({"a": 1}, {"a": 1}, True),
        ({"a": 1}, {"a": "1"}, False),
        ({"a": "1"}, {"a": "1"}, True),
        ({"a": "1"}, {"a": "1", "bcd": 1}, True),
        ({"a": 1}, {"a": "1", "bcd": 1}, False),
        ({"a": "1", "bcd": 1}, {"a": "1"}, False),
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
        ({1: "1"}, {1: "1", "bcd": 1}, True),
        ({"1": "1"}, {1: "1", "bcd": 1}, False),
        ({1: "1"}, {"1": "1", "bcd": 1}, False),
        ({1: 1}, {1: "1", "bcd": 1}, False),
        ({1: "1", "bcd": 1}, {1: "1"}, False),
    ],
)
def test__included(one: Iterable[Any], another: Iterable[Any], *, result: bool) -> None:
    """Test for `included()`."""
    assert result == included(one, another)


@pytest.mark.parametrize(
    "one, another, result",
    [
        ([], [], True),
        ([], [1], True),
        ([1], [], False),
        ([1], [1], True),
        (["1"], ["1"], True),
        (["1"], ["1", 1], True),
        (["1", 1], ["1"], True),  # not `False`
        ({}, {}, True),
        ({}, {"a": 1}, True),
        ({"a": 1}, {}, False),
        ({"a": 1}, {"a": 1}, True),
        ({"a": 1}, {"a": "1"}, True),  # not `False`
        ({"a": "1"}, {"a": "1"}, True),
        ({"a": "1"}, {"a": "1", "bcd": 1}, True),
        ({"a": 1}, {"a": "1", "bcd": 1}, True),  # not `False`
        ({"a": "1", "bcd": 1}, {"a": "1"}, False),
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
        ({1: "1"}, {1: "1", "bcd": 1}, True),
        ({"1": "1"}, {1: "1", "bcd": 1}, False),
        ({1: "1"}, {"1": "1", "bcd": 1}, False),
        ({1: 1}, {1: "1", "bcd": 1}, True),  # not `False`
        ({1: "1", "bcd": 1}, {1: "1"}, False),
    ],
)
def test__included__equals(
    one: Iterable[Any], another: Iterable[Any], *, result: bool
) -> None:
    """Test for `included()` with `equals` argument specified."""

    def _str_equals(one: Any, another: Any) -> bool:  # noqa: ANN401
        return str(one) == str(another)

    assert result == included(one, another, equals=_str_equals)


@pytest.mark.parametrize(
    "expected_result, args",
    [
        (
            [],
            ([],),
        ),  # 1 empty argument
        ([1], ([1],)),  # 1 single entity argument
        ([1], (1,)),  # 1 single entity argument
        ([1, 2], ([1, 2],)),  # 1 two entity argument
        ([], ([], [])),
        ([], ([1], [])),
        ([], (1, [])),
        ([[1, ()]], ([1], [()])),
        ([[1]], ([1], [[]])),
        ([[1, []]], ([1], [[[]]])),
        ([], ([], [2])),
        ([], ([], 2)),
        ([[2]], ([[]], [2])),
        ([[[], 2]], ([[[]]], [2])),
        ([[(), 2]], ([()], [2])),
        ([[(), 2]], ((), [2])),
        ([[2]], ([[]], 2)),
        ([[[], 2]], ([[[]]], 2)),
        ([[(), 2]], ([()], 2)),
        ([[3, 4]], ([[3]], [4])),
        ([[3, 4]], ([[3]], 4)),
        ([[3, 4]], (3, [4])),
        ([[3, 4]], (3, 4)),
        ([[[3], 4]], ([[[3]]], [4])),
        ([[[3], 4]], ([[[3]]], 4)),
        ([[3, 4]], (3, [[4]])),
        ([[3, [4]]], (3, [[[4]]])),
        ([[5, 7], [5, 8]], ([5], [7, 8])),
        ([[5, 7], [5, 8]], (5, [7, 8])),
        ([[5, 8], [6, 8]], ([5, 6], [8])),
        ([[5, 8], [6, 8]], ([5, 6], 8)),
        ([[5, 7], [5, 8], [6, 7], [6, 8]], ([5, 6], [7, 8])),
        (
            [[5, 6, 10], [5, 6, 7, 8], [9, 10], [9, 7, 8]],
            ([[5, 6], 9], [10, [7, 8]]),
        ),
        (
            [[(5, 6), 10], [(5, 6), (7, 8)], [9, 10], [9, (7, 8)]],
            ([(5, 6), 9], [10, (7, 8)]),
        ),
        # dict
        ([{}], ([{}],)),  # 1 single empty dict argument
        ([{}], ({},)),  # 1 single empty dict argument
        (
            [{}, {"a": 1}],
            (
                [
                    {},
                    {"a": 1},
                ],
            ),
        ),  # 1 two dict argument
        ([], ([{}], [])),
        ([], ({}, [])),
        ([[{}]], ([{}], [[]])),
        ([[{}, ()]], ([{}], [()])),
        ([], ([], [{}])),
        ([], ([], {})),
        ([[{}]], ([[]], [{}])),
        ([[(), {}]], ([()], [{}])),
        ([[{}]], ([[]], {})),
        ([[(), {}]], ([()], {})),
        ([[{}, {"a": 4}]], ([[{}]], [{"a": 4}])),
        ([[{}, {"a": 4}]], ([[{}]], {"a": 4})),
        ([[{}, {"a": 4}]], ({}, [{"a": 4}])),
        ([[{}, {"a": 4}]], ({}, {"a": 4})),
        (
            [[{"a": 5}, {"b": 7}], [{"a": 5}, {"c": 8}]],
            ([{"a": 5}], [{"b": 7}, {"c": 8}]),
        ),
        (
            [[{"a": 5}, {"b": 7}], [{"a": 5}, {"c": 8}]],
            ({"a": 5}, [{"b": 7}, {"c": 8}]),
        ),
        ([[{"a": 5}, {"c": 8}], [6, {"c": 8}]], ([{"a": 5}, 6], [{"c": 8}])),
        ([[{"a": 5}, {"c": 8}], [6, {"c": 8}]], ([{"a": 5}, 6], {"c": 8})),
        (
            [[{"a": 5}, 7], [{"a": 5}, {"c": 8}], [6, 7], [6, {"c": 8}]],
            ([{"a": 5}, 6], [7, {"c": 8}]),
        ),
        (
            [
                [{"a": 5}, 6, 10],
                [{"a": 5}, 6, 7, {"c": 8}],
                [9, 10],
                [9, 7, {"c": 8}],
            ],
            ([[{"a": 5}, 6], 9], [10, [7, {"c": 8}]]),
        ),
        (
            [
                [({"a": 5}, 6), 10],
                [({"a": 5}, 6), (7, {"c": 8})],
                [9, 10],
                [9, (7, {"c": 8})],
            ],
            ([({"a": 5}, 6), 9], [10, (7, {"c": 8})]),
        ),
        # 3 arguments
        ([], ([], [], [])),
        ([], ([1], [], [])),
        ([], ([], [2], [])),
        ([], ([], [], [3])),
        ([], ([1], [2], [])),
        ([], ([], [2], [3])),
        ([], ([1], [], [3])),
        ([[1, 2, 3]], ([1], [2], [3])),
        ([[1, 2, 3], [2, 3]], ([1, []], [2], [3])),
        ([[1, 2, 3], [(), 2, 3]], ([1, ()], [2], [3])),
        ([[1, 2, 3], [1, 3]], ([1], [[], 2], [3])),
        ([[1, 2, 3], [1, (), 3]], ([1], [(), 2], [3])),
        ([[1, 2, 3], [1, 2]], ([1], [2], [3, []])),
        ([[1, 2, 3], [1, 2, ()]], ([1], [2], [3, ()])),
        ([[1, 2, 3], [1, 3], [2, 3], [3]], ([1, []], [2, []], [3])),
        ([[1, 2, 3], [1, (), 3], [(), 2, 3], [(), (), 3]], ([1, ()], [2, ()], [3])),
        ([[1], [1, 3], [1, 2], [1, 2, 3]], ([1], [[], 2], [[], 3])),
        ([[1, (), ()], [1, (), 3], [1, 2, ()], [1, 2, 3]], ([1], [(), 2], [(), 3])),
        ([[2, 3], [2], [1, 2, 3], [1, 2]], ([[], 1], [2], [3, []])),
        ([[(), 2, 3], [(), 2, ()], [1, 2, 3], [1, 2, ()]], ([(), 1], [2], [3, ()])),
        (
            [[1, 2], [1, 2, 3], [1], [1, 3], [2], [2, 3], [], [3]],
            ([1, []], [2, []], [[], 3]),
        ),
        (
            [
                [1, 2, ()],
                [1, 2, 3],
                [1, (), ()],
                [1, (), 3],
                [(), 2, ()],
                [(), 2, 3],
                [(), (), ()],
                [(), (), 3],
            ],
            ([1, ()], [2, ()], [(), 3]),
        ),
    ],
)
def test_combine_lists(
    expected_result: list[object], args: tuple[object | list[object]]
) -> None:
    """Test for `combine_lists()`."""
    if len(expected_result) == 0:
        with pytest.raises(AssertionError):
            result_list = combine_lists(*args)

        with pytest.raises(AssertionError):
            result_list = combine_lists(*args, raise_if_empty=True)

        result_list = combine_lists(*args, raise_if_empty=False)
        assert isinstance(result_list, list)

        assert len(result_list) == 0

    else:
        for raise_if_empty in [True, False]:
            result_list = combine_lists(*args, raise_if_empty=raise_if_empty)
            assert isinstance(result_list, list)

            assert equal_set(expected_result, result_list)

    # enddef


@pytest.mark.parametrize(
    'operand',
    [
        combine_lists('c', 'd'),
        [],
        [1],
    ],
)
def test__combine_lists__add(operand: list[object]) -> None:
    """Test that `+` operator works for result of `combine_lists()`."""
    # Just make sure addition works
    assert (combine_lists('a', 'b') + operand) is not None
    assert (operand + combine_lists('a', 'b')) is not None


@pytest.mark.parametrize(
    "expected_result, args",
    [
        ([], ([],)),  # 1 empty argument
        ([(1,)], ([1],)),  # 1 single entity argument
        ([(1,)], (1,)),  # 1 single entity argument
        ([(1,), (2,)], ([1, 2],)),  # 1 two entity argument
        ([], ([], [])),
        ([], ([1], [])),
        ([], (1, [])),
        ([(1, [])], ([1], [[]])),
        ([(1,)], ([1], [()])),
        ([(1, ())], ([1], [((),)])),
        ([], ([], [2])),
        ([], ([], 2)),
        ([(2,)], ([()], [2])),
        ([([], 2)], ([([],)], [2])),
        ([([], 2)], ([[]], [2])),
        ([(2,)], ((), [2])),  # Doesn't correspond with `combine_lists()`
        ([(2,)], ([()], 2)),
        ([((), 2)], ([((),)], 2)),
        ([([], 2)], ([[]], 2)),
        ([(3, 4)], ([(3,)], [4])),
        ([(3, 4)], ([(3,)], 4)),
        ([(3, 4)], (3, [4])),
        ([(3, 4)], (3, 4)),
        ([((3,), 4)], ([((3,),)], (4,))),
        ([((3,), 4)], ([((3,),)], 4)),
        ([(3, 4)], (3, [(4,)])),
        ([(3, (4,))], (3, [((4,),)])),
        ([(5, 7), (5, 8)], ([5], [7, 8])),
        ([(5, 7), (5, 8)], (5, [7, 8])),
        ([(5, 8), (6, 8)], ([5, 6], [8])),
        ([(5, 8), (6, 8)], ([5, 6], 8)),
        ([(5, 7), (5, 8), (6, 7), (6, 8)], ([5, 6], [7, 8])),
        ([(5, 6, 10), (5, 6, 7, 8), (9, 10), (9, 7, 8)], ([(5, 6), 9], [10, (7, 8)])),
        (
            [([5, 6], 10), ([5, 6], [7, 8]), (9, 10), (9, [7, 8])],
            ([[5, 6], 9], [10, [7, 8]]),
        ),
        # dict
        ([({"abc": 1},)], ({"abc": 1},)),
        ([({},)], ([{}],)),  # 1 single empty dict argument
        ([({},)], ({},)),  # 1 single empty dict argument
        (
            [({},), ({"a": 1},)],
            (
                [
                    {},
                    {"a": 1},
                ],
            ),
        ),  # 1 two dict argument
        ([], ([{}], [])),
        ([], ({}, [])),
        ([({},)], ([{}], [()])),
        ([({}, [])], ([{}], [[]])),
        ([], ([], [{}])),
        ([], ([], {})),
        ([({},)], ([()], [{}])),
        ([([], {})], ([[]], [{}])),
        ([({},)], ([()], {})),
        ([([], {})], ([[]], {})),
        ([({}, {"a": 4})], ([({},)], [{"a": 4}])),
        ([({}, {"a": 4})], ([({},)], {"a": 4})),
        ([({}, {"a": 4})], ({}, [{"a": 4}])),
        ([({}, {"a": 4})], ({}, {"a": 4})),
        (
            [({"a": 5}, {"b": 7}), ({"a": 5}, {"c": 8})],
            ([{"a": 5}], [{"b": 7}, {"c": 8}]),
        ),
        (
            [({"a": 5}, {"b": 7}), ({"a": 5}, {"c": 8})],
            ({"a": 5}, [{"b": 7}, {"c": 8}]),
        ),
        ([({"a": 5}, {"c": 8}), (6, {"c": 8})], ([{"a": 5}, 6], [{"c": 8}])),
        ([({"a": 5}, {"c": 8}), (6, {"c": 8})], ([{"a": 5}, 6], {"c": 8})),
        (
            [({"a": 5}, 7), ({"a": 5}, {"c": 8}), (6, 7), (6, {"c": 8})],
            ([{"a": 5}, 6], [7, {"c": 8}]),
        ),
        (
            [({"a": 5}, 6, 10), ({"a": 5}, 6, 7, {"c": 8}), (9, 10), (9, 7, {"c": 8})],
            ([({"a": 5}, 6), 9], [10, (7, {"c": 8})]),
        ),
        (
            [
                ([{"a": 5}, 6], 10),
                ([{"a": 5}, 6], [7, {"c": 8}]),
                (9, 10),
                (9, [7, {"c": 8}]),
            ],
            ([[{"a": 5}, 6], 9], [10, [7, {"c": 8}]]),
        ),
        # 3 arguments
        ([], ([], [], [])),
        ([], ([1], [], [])),
        ([], ([], [2], [])),
        ([], ([], [], [3])),
        ([], ([1], [2], [])),
        ([], ([], [2], [3])),
        ([], ([1], [], [3])),
        ([(1, 2, 3)], ([1], [2], [3])),
        ([(1, 2, 3), (2, 3)], ([1, ()], [2], [3])),
        ([(1, 2, 3), ([], 2, 3)], ([1, []], [2], [3])),
        ([(1, 2, 3), (1, 3)], ([1], [(), 2], [3])),
        ([(1, 2, 3), (1, [], 3)], ((1,), [[], 2], [3])),
        ([(1, 2, 3), (1, 2)], ([1], [2], [3, ()])),
        ([(1, 2, 3), (1, 2, [])], ([1], [2], [3, []])),
        ([(1, 2, 3), (1, 3), (2, 3), (3,)], ([1, ()], [2, ()], [3])),
        ([(1, 2, 3), (1, [], 3), ([], 2, 3), ([], [], 3)], ([1, []], [2, []], [3])),
        ([(1,), (1, 3), (1, 2), (1, 2, 3)], ((1,), [(), 2], [(), 3])),
        ([(1, [], []), (1, [], 3), (1, 2, []), (1, 2, 3)], ((1,), [[], 2], [[], 3])),
        ([(2, 3), (2,), (1, 2, 3), (1, 2)], ([(), 1], [2], [3, ()])),
        ([([], 2, 3), ([], 2, []), (1, 2, 3), (1, 2, [])], ([[], 1], [2], [3, []])),
        (
            [(1, 2), (1, 2, 3), (1,), (1, 3), (2,), (2, 3), (), (3,)],
            ([1, ()], [2, ()], [(), 3]),
        ),
        (
            [
                (1, 2, []),
                (1, 2, 3),
                (1, [], []),
                (1, [], 3),
                ([], 2, []),
                ([], 2, 3),
                ([], [], []),
                ([], [], 3),
            ],
            ([1, []], [2, []], [[], 3]),
        ),
        # `str`
        ([("abc",)], ("abc",)),
        ([("abc", "de")], ("abc", "de")),
        ([("abc", "de", "f")], ("abc", "de", "f")),
        ([("abc",)], (["abc"],)),
        ([("abc", "de")], (["abc"], "de")),
        ([("abc", "de")], ("abc", ["de"])),
        ([("abc", "de", "f")], (["abc"], "de", "f")),
        ([("abc", "de", "f")], ("abc", ["de"], "f")),
        ([("abc", "de", "f")], ("abc", "de", ["f"])),
        ([("abc",), ("xy",)], (["abc", "xy"],)),
        ([("abc", "de"), ("xy", "de")], (["abc", "xy"], "de")),
        ([("abc", "de"), ("abc", "xy")], ("abc", ["de", "xy"])),
        ([("abc", "de", "f"), ("xy", "de", "f")], (["abc", "xy"], "de", "f")),
        ([("abc", "de", "f"), ("abc", "xy", "f")], ("abc", ["de", "xy"], "f")),
        ([("abc", "de", "f"), ("abc", "de", "xy")], ("abc", "de", ["f", "xy"])),
        (
            [("abc", "de"), ("abc", "z"), ("xy", "de"), ("xy", "z")],
            (["abc", "xy"], ["de", "z"]),
        ),
    ],
)
def test_combine_tuples(
    expected_result: list[tuple[object, ...]],
    args: tuple[object | list[object], ...],
) -> None:
    """Test for `combine_tuples()`."""
    if len(expected_result) == 0:
        with pytest.raises(AssertionError):
            result_list = combine_tuples(*args)

        with pytest.raises(AssertionError):
            result_list = combine_tuples(*args, raise_if_empty=True)

        result_list = combine_tuples(*args, raise_if_empty=False)
        assert isinstance(result_list, list)

        assert len(result_list) == 0

    else:
        assert isinstance(args, tuple)

        for raise_if_empty in [True, False]:
            result_list = combine_tuples(*args, raise_if_empty=raise_if_empty)
            assert isinstance(result_list, list)

            assert equal_set(expected_result, result_list)

    # enddef


@pytest.mark.parametrize(
    'operand',
    [
        combine_tuples('c', 'd'),
        [],
        [(1,)],
    ],
)
def test__combine_tuples__add(operand: list[tuple[object, ...]]) -> None:
    """Test that `+` operator works for result of `combine_tuples()`."""
    # Just make sure addition works
    assert (combine_tuples('a', 'b') + operand) is not None
    assert (operand + combine_tuples('a', 'b')) is not None


def test__current_function_name() -> None:
    """Test for `current_function_name()`."""

    def _inner_function() -> None:
        assert current_function_name() == '_inner_function'
        assert current_function_name(depth=1) == 'test__current_function_name'

    _inner_function()
