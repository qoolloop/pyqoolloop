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

    instance = registry.create("class", {})

    assert isinstance(instance, _Class)