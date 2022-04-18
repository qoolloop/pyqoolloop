from typing import (
    Any,
    Dict,
)

from .factory import RegistryFactory


def test__RegistryFactory() -> None:
    """Test `RegistryFactory`."""

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
        

    for name, type in (("class", _Class), ("_AnotherClass", _AnotherClass)):
        instance = registry.create(name, {})
        assert isinstance(instance, type)

    #TODO: more tesing