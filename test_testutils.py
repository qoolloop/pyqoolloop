import pytest

from .testutils import (
    included,
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
def test__included(one, another, result):
    assert result == included(one, another)