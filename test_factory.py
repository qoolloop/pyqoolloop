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
        def __init__(self, name: str, klass: type) -> None:
            self.name = name
            self.klass = klass


    registry = RegistryFactory[_SuperClass]()


    @registry.register("class")
    class _Class(_SuperClass):
        def __init__(self, name: str, klass: type) -> None:
            super().__init__(name, klass)


    @registry.register()
    class _AnotherClass(_SuperClass):
        def __init__(self, *, name: str, klass: type) -> None:
            super().__init__(name, klass)


    @registry.register
    class _YetAnotherClass(_SuperClass):
        def __init__(self, **kwargs: Any) -> None:
            super().__init__(kwargs['name'], kwargs['klass'])
        

    for name, klass in (
        ("class", _Class), 
        ("_AnotherClass", _AnotherClass), 
        ("_YetAnotherClass", _YetAnotherClass)
    ):
        arguments = dict(name=name, klass=klass)
        instance = registry.create(name, arguments)
        assert isinstance(instance, klass)
        assert instance.name == name
        assert instance.klass == klass
