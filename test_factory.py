"""Test `factory.py`."""

from collections.abc import Callable
from typing import (
    Any,
    TypeAlias,
)

import pytest

from .factory import MethodRegistryFactory, RegistryFactory


def test__RegistryFactory() -> None:
    """Test `RegistryFactory`."""
    # pylint: disable=too-few-public-methods

    class _SuperClass:
        def __init__(self, name: str, klass: type) -> None:
            self.name = name
            self.klass = klass

    registry = RegistryFactory[_SuperClass]()

    @registry.register("class")
    class _Class(_SuperClass): ...

    @registry.register()
    class _AnotherClass(_SuperClass):
        def __init__(self, *, name: str, klass: type) -> None:
            super().__init__(name, klass)

    @registry.register
    class _YetAnotherClass(_SuperClass):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(kwargs['name'], kwargs['klass'])

    # Want mypy to show an error here, when warning is enabled.
    @registry.register  # type: ignore[arg-type]
    class _WrongClass:
        def __init__(self, **kwargs: Any) -> None:
            self._kwargs = kwargs

    for name, klass in (
        ("class", _Class),
        ("_AnotherClass", _AnotherClass),
        ("_YetAnotherClass", _YetAnotherClass),
    ):
        arguments = {'name': name, 'klass': klass}
        instance = registry.create(name, arguments)
        assert isinstance(instance, klass)
        assert instance.name == name
        assert instance.klass == klass


def test__RegistryFactory__KeyError() -> None:
    """Test that `RegistryFactory.create()` raises `KeyError`."""
    registry = RegistryFactory[object]()

    @registry.register("class")
    class _Class: ...

    with pytest.raises(KeyError):
        _ = registry.create('none-existent')


def test__MethodRegistryFactory() -> None:
    """Test `MethodRegistryFactory`."""

    class _Class:
        _MethodSignature: TypeAlias = Callable[['_Class', float], int]

        registry = MethodRegistryFactory[_MethodSignature]()

        @registry.register("method")
        def method(self, value: float) -> int:
            return int(value)

        # Want mypy to show an error here, when warning is enabled.
        @registry.register('wrong-signature')  # type: ignore[arg-type]
        def wrong_method(self, **kwargs: Any) -> None:
            self._kwargs = kwargs

    method = _Class.registry.create('method')

    instance = _Class()

    assert method(instance, 2.0) == 2


def test__MethodRegistryFactory__KeyError() -> None:
    """Test that `MethodRegistryFactory.create()` raises `KeyError`."""

    class _Class:
        _MethodSignature: TypeAlias = Callable[['_Class', str], None]

        registry = MethodRegistryFactory[_MethodSignature]()

        @registry.register("method")
        def method(self, _value: str) -> None:
            return

    with pytest.raises(KeyError):
        _ = _Class.registry.create('none-existent')
