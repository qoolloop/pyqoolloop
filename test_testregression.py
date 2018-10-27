from . import testregression


def test__make_filename__float_index():
    function_name = 'test__make_filename__float_index'

    int_filename = testregression.make_filename(
        __name__, function_name, index=1)
    float_filename = testregression.make_filename(
        __name__, function_name, index=1.1)

    assert int_filename != float_filename


def test__make_filename__index():
    function_name = 'test__make_filename__float_index'

    int_filename = testregression.make_filename(
        __name__, function_name, index=1)

    assert '1.0' not in int_filename
