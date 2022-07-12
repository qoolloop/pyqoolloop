"""Test `parallel.py`."""

from dataclasses import dataclass
from threading import Thread
from time import sleep

import pytest

from .parallel import Guard


def test__Guard__int() -> None:
    """Test `Guard` with `int`."""
    guarded_variable = 1
    guard = Guard(guarded_variable)

    with guard as variable:
        assert variable == 1


def test__Guard__dataclass() -> None:
    """Test `Guard` with `dataclass`."""

    @dataclass
    class _Class:
        variable: int = 2

    guard = Guard(_Class())

    with guard as instance:
        assert instance.variable == 2

        instance.variable = 3
        assert instance.variable == 3

    with guard as instance:
        assert instance.variable == 3


@pytest.mark.unreliable
def test__Guard__lock() -> None:
    """Test `Guard` that guards agains parallels access."""

    @dataclass
    class _Class:
        variable: int = 0

    def _routine(guard: Guard[_Class]) -> None:
        with guard as instance:
            value = instance.variable
            sleep(0.001)
            value += 1
            instance.variable = value

    num_threads = 10

    guard = Guard(_Class())
    threads = [Thread(target=_routine, args=(guard,)) for _ in range(num_threads)]
    for each in threads:
        each.start()

    for each in threads:
        each.join()

    with guard as instance:
        assert instance.variable == num_threads
