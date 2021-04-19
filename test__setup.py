"""
Tests for settings in `setup.cfg`.
"""
import re

import pytest


# snake_case, but Capitals allowed after `__`
FUNCTION_RGX = '(([a-z_][a-z0-9_]{2,30}$)|([a-z_][a-z0-9_]*__[a-zA-Z0-9_]*$))'


@pytest.mark.parametrize('pattern', (
    'snake_case',
    'irregular__Snake_case',
    'regular__snake_case',
    '__private',
    'trailing_',
    'trailing__',
    '_preceding',
    '__preceding',
    '_both_',
    '__both__',
))
def test__function_rgx(pattern: str) -> None:
    """
    Test for `function-rgx` and `method-rgx`.
    """
    assert re.match(FUNCTION_RGX, pattern)


@pytest.mark.parametrize('pattern', (
    #FUTURE: '_',
    'non_Snake_Case',
    '__Private__',
))
def test__function_rgx__bad(pattern: str) -> None:
    """
    Test for `function-rgx` and `method-rgx`.
    """
    assert not re.match(FUNCTION_RGX, pattern)
