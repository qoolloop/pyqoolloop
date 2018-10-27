import base64
import os
import pytest

from . import (
    encrypt,
    testregression,
)

import pylog
logger = pylog.getLogger(__name__)


@pytest.mark.parametrize('index, password, salt', (
    (1, 'password', b'salt'),
    (2, 'mixed1234!@#$%^&*()_+{}|:"<>?-=[]\\;\',./',
     b'mixed1234!@#$%^&*()_+{}|:"<>?-=[]\\;\',./'),
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


@pytest.mark.parametrize('index, value', (
    (1, 'password'),
    (2, 'mixed1234!@#$%^&*()_+{}|:"<>?-=[]\\;\',./'),
))
def test__encrypt_decrypt(index, value):
    key = os.urandom(32)
    logger.info("Key: (%s) %r", type(key), key)

    encryptor = encrypt.EncryptorDecryptor(base64.urlsafe_b64encode(key))

    for no_encryption in (False, True):
        encrypted = encryptor.encrypt(value, no_encryption=no_encryption)
        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == value

    return
