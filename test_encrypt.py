import pytest

from . import (
    encrypt,
    testregression,
)


@pytest.mark.parametrize('index, password, salt', (
    (1, 'password', b'salt'),
))
def test__key_from_password(index, password, salt):
    save = False
    
    key = encrypt.key_from_password(password, salt)
    testregression.assert_no_change(key, save,
                                    __name__, 'test_key_from_password', index)

    # Make sure same PBKDF2HMAC is not used twice, but produces same results
    key = encrypt.key_from_password(password, salt)
    testregression.assert_no_change(key, False,
                                    __name__, 'test_key_from_password', index)
