from .containers import NamedFields


def test__NamedFields__init__empty():
    instance = NamedFields()

    #TODO: Not sure whether this should be a requirement
    instance.new_field = 1

    assert instance.new_field == 1
    

def test__NamedFields__init():
    instance = NamedFields(new_field=1)

    assert instance.new_field == 1
