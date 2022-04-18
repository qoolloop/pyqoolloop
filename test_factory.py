"""Test `factory.py`."""

from typing import (
    Any,
    Dict,
)

from .factory import RegistryFactory


def test__RegistryFactory() -> None:
    """Test `RegistryFactory`."""

     # pylint: disable=too-few-public-methods, unused-argument

    class _SuperClass:
        ...

    registry = RegistryFactory[_SuperClass]()

    @registry.register("class")
    class _Class(_SuperClass):
        def __init__(self, parameters: Dict[str, Any]) -> None:
            ...


    @registry.register()
    class _AnotherClass(_SuperClass):
        def __init__(self, parameters: Dict[str, Any]) -> None:
            ...


    @registry.register
    class _YetAnotherClass(_SuperClass):
        def __init__(self, parameters: Dict[str, Any]) -> None:
            ...
        

    for name, klass in (
        ("class", _Class), 
        ("_AnotherClass", _AnotherClass), 
        ("_YetAnotherClass", _YetAnotherClass)
    ):
        instance = registry.create(name, {})
        assert isinstance(instance, klass)
