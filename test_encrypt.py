import os
import pytest
import sys
import tempfile

from . import (
    encrypt,
    testregression,
)

import pylog
logger = pylog.getLogger(__name__)


def _make_temporary_encryptor():
    key = encrypt.EncryptorDecryptor.generate_key()
        
    logger.info("Key: (%s) %r", type(key), key)

    encryptor = encrypt.EncryptorDecryptor(key)

    return encryptor
    

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

    assert not save, "Warning"


@pytest.mark.parametrize('index, value', (
    (1.1, 'password'),
    (1.2, 'mixed1234!@#$%^&*()_+{}|:"<>?-=[]\\;\',./'),

    (2.1, 0),
    (2.2, 1),
    (2.3, -1),
    (2.4, sys.maxsize),
    (2.5, -sys.maxsize),

    (3.1, 0.0),
    (3.2, 1.0),
    (3.3, -1.0),
    # (3.4, float('-inf')),  # not allowed in json
    # (3.5, float('inf')),  # not allowed in json
    # (3.6, float('nan')),  # not allowed in json

    (4.1, True),
    (4.2, False),

    (5.1, None),

    (6.1, {}),
    (6.2, {'key': 'value'}),
    (6.3, {'this is a complex dictionary': {
        'str': 'str',
        'int': 1,
        'float': 3.5,
        'bool': True,
        'null': None,
        'dict': {'key': 'value'},
        'list': [1, 2],
    }}),
    # tuple/set not supported as value
    # (6.4, {'this is a complex dictionary': {
    #     'str': 'str',
    #     'int': 1,
    #     'float': 3.5,
    #     'bool': True,
    #     'null': None,
    #     'dict': {'key', 'value'},
    #     'list': [1, 2],
    #     'tuple': (1, 2),
    # }}),

    (7.1, []),
    (7.2, [1]),
    (7.3, [1, 2]),
    (7.4,
     ['complex list', 1, 3.5, False, None, {'key': 'value'}, [1, 2], [1, 2]]),
    # tuple/set not supported as value
    # (7.5,
    # ['complex list', 1, 3.5, False, None, {'key', 'value'}, [1, 2], (1, 2)]),

    (8.1, ()),
    (8.2, (1,)),
    (8.3, (1, 2)),
    (8.4,
     ('complex tuple', 1, 3.5, False, None, {'key': 'value'}, [1, 2], [1, 2])),
    # tuple/set not supported as element
    # (8.5,
    # ('complex tuple', 1, 3.5, False, None, {'key', 'value'}, [1, 2], (1, 2))),
))
def test__encrypt_decrypt(index, value):

    encryptor = _make_temporary_encryptor()

    for no_encryption in (False, True):
        encrypted = encryptor.encrypt(value, no_encryption=no_encryption)
        decrypted = encryptor.decrypt(encrypted)
        assert decrypted == value

    return


@pytest.mark.parametrize('index, value', (
    (1.1, 'password'),
    (1.2, 'mixed1234!@#$%^&*()_+{}|:"<>?-=[]\\;\',./'),
))
def test__encrypt_decrypt_from_file(index, value):
    encryptor = _make_temporary_encryptor()

    with tempfile.TemporaryDirectory() as directory:
        value_filename = os.path.join(directory, 'value.p')

        encryptor.encrypt_to_file(value, value_filename)

        loaded = encryptor.decrypt_from_file(value_filename)

        assert loaded == value

    return


@pytest.mark.parametrize('index, value', (
    (1.1, 'password'),
    (1.2, 'mixed1234!@#$%^&*()_+{}|:"<>?-=[]\\;\',./'),
))
def test__encrypt_decrypt_from_file__no_change(index, value):
    save = False

    function_name = 'test__encrypt_decrypt_from_file'
    
    key_filename = testregression.make_filename(
        __name__, function_name, index=index, suffix='key')

    if save:
        key = encrypt.EncryptorDecryptor.generate_key()

        with open(key_filename, 'wb') as f:
            f.write(key)

    else:
        with open(key_filename, 'rb') as f:
            key = f.read()
        
    encryptor = encrypt.EncryptorDecryptor(key)

    value_filename = testregression.make_filename(
        __name__, function_name, index=index)

    if save:
        encryptor.encrypt_to_file(value, value_filename)

    loaded = encryptor.decrypt_from_file(value_filename)

    assert loaded == value

    assert not save, "Warning"


#TODO: test optional arguments
