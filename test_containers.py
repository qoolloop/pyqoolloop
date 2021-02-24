from .containers import NamedFields


def test__NamedFields__init__empty() -> None:
    instance = NamedFields()

    #TODO: Not sure whether this should be a requirement
    instance.new_field = 1

    assert instance.new_field == 1
    

def test__NamedFields__init() -> None:
    instance = NamedFields(new_field=1)

    assert instance.new_field == 1
