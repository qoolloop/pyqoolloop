import math
import os
import pytest
import sys
import tempfile

from pyexception.exception import (
    RecoveredException,
    FileExists,
)
from pyexception import testutils


from . import (
    encrypt,
    testregression,
)

import pylog
logger = pylog.getLogger(__name__)


def _make_temporary_encryptor() -> encrypt.EncryptorDecryptor:
    key = encrypt.EncryptorDecryptor.generate_key()
        
    logger.info("Key: (%s) %r", type(key), key)

    encryptor = encrypt.EncryptorDecryptor(key)

    return encryptor
    

@pytest.mark.parametrize('index, password, salt', (
    (1, 'password', b'salt'),
    (2, 'mixed1234!@#$%^&*()_+{}|:"<>?-=[]\\;\',./',
     b'mixed1234!@#$%^&*()_+{}|:"<>?-=[]\\;\',./'),
))
def test__key_from_password(index: int, password: str, salt: bytes) -> None:
    save = False
    
    key = encrypt.key_from_password(password, salt)
    testregression.assert_no_change(key, save, index)

    # Make sure same PBKDF2HMAC is not used twice, but produces same results
    key = encrypt.key_from_password(password, salt)
    testregression.assert_no_change(key, False, index)

    assert not save, "Warning"


def test__encrypt_to_file__overwrite() -> None:
    encryptor = _make_temporary_encryptor()

    with tempfile.TemporaryDirectory() as directory:
        value_filename = os.path.join(directory, 'file.bin')

        value: object = {}
        encryptor.encrypt_to_file(value, value_filename)

        new_value = ()
        with testutils.raises(RecoveredException, FileExists):
            encryptor.encrypt_to_file(new_value, value_filename)
        
        loaded = encryptor.decrypt_from_file(value_filename)
        assert loaded == value

        encryptor.encrypt_to_file(new_value, value_filename, overwrite=True)

        loaded = encryptor.decrypt_from_file(value_filename)
        assert loaded == new_value

    return


@pytest.mark.parametrize('index, value', (
    (0.1, b'password'),
    # UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80 in position 0:
    # invalid start byte
    (0.2, b'\x80'),
    # UnicodeDecodeError: 'utf-8' codec can't decode byte 0xd0 in position 1:
    # invalid continuation byte
    (0.3, b';\xd0bi$\x9bR(\x82I\xd5\xe4\x81VL\xe3\xfds\xa4\xfaIHr\x9c'),
    # (0.4, os.urandom(24)),

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
    (3.4, float('-inf')),
    (3.5, float('inf')),
    (3.6, float('nan')),

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
    (6.4, {'this is a complex dictionary': {
        'str': 'str',
        'int': 1,
        'float': 3.5,
        'bool': True,
        'null': None,
        'dict': {'key', 'value'},
        'list': [1, 2],
        'tuple': (1, 2),
    }}),

    (7.1, []),
    (7.2, [1]),
    (7.3, [1, 2]),
    (7.4,
     ['complex list', 1, 3.5, False, None, {'key': 'value'}, [1, 2], [1, 2]]),
    (7.5,
     ['complex list', 1, 3.5, False, None, {'key', 'value'}, [1, 2], (1, 2)]),
    
    (8.1, ()),
    (8.2, (1,)),
    (8.3, (1, 2)),
    (8.4,
     ('complex tuple', 1, 3.5, False, None, {'key': 'value'}, [1, 2], [1, 2])),
    (8.5,
     ('complex tuple', 1, 3.5, False, None, {'key', 'value'}, [1, 2], (1, 2))),

    (9.1, set()),
    (9.2, {1}),
    (9.4,
     {'complex set', 1, 3.5, False, None}),
    (9.5,
     {'complex set', 1, 3.5, False, None, (1, 2)}),
))
def test__encrypt_decrypt(index: float, value: object) -> None:
    logger.info("value: %r", value)
                         
    encryptor = _make_temporary_encryptor()

    encrypted = encryptor.encrypt(value)
    decrypted = encryptor.decrypt(encrypted)
    if isinstance(value, float) and math.isnan(value):
        assert isinstance(decrypted, float)
        assert math.isnan(decrypted)

    else:
        assert decrypted == value

    return


@pytest.mark.parametrize('index, value', (
    (1.1, 'password'),
    (1.2, 'mixed1234!@#$%^&*()_+{}|:"<>?-=[]\\;\',./'),
))
def test__encrypt_decrypt_from_file(index: float, value: str) -> None:
    encryptor = _make_temporary_encryptor()

    with tempfile.TemporaryDirectory() as directory:
        value_filename = os.path.join(directory, 'value.bin')

        encryptor.encrypt_to_file(value, value_filename)

        loaded = encryptor.decrypt_from_file(value_filename)

        assert loaded == value

    return


@pytest.mark.parametrize('index, value', (
    (1.1, 'password'),
    (1.2, 'mixed1234!@#$%^&*()_+{}|:"<>?-=[]\\;\',./'),
))
def test__encrypt_decrypt_from_file__no_change(
        index: float, value: str) -> None:
    save = False

    key_filename = testregression.make_filename(
        index=index, suffix='key', extension='.bin')

    if save:
        key = encrypt.EncryptorDecryptor.generate_key()

        with open(key_filename, 'wb') as f:
            f.write(key)

        logger.info("Key length: %d" % len(key))

    with open(key_filename, 'rb') as f:
        key = f.read()
        
    logger.info("Key length: %d" % len(key))

    encryptor = encrypt.EncryptorDecryptor(key)

    value_filename = testregression.make_filename(
        index=index, extension='.bin')

    if save:
        encryptor.encrypt_to_file(value, value_filename)

    loaded = encryptor.decrypt_from_file(value_filename)

    assert loaded == value

    assert not save, "Warning"


@pytest.mark.parametrize('index, value', (
    (1.1, 'password'),
    (1.2, 'mixed1234!@#$%^&*()_+{}|:"<>?-=[]\\;\',./'),
))
def test__encrypt_decrypt_from_file__no_change__auto_rotate(
        index: float, value: str) -> None:
    primary_key = encrypt.EncryptorDecryptor.generate_key()

    primary_encryptor = encrypt.EncryptorDecryptor(primary_key)

    secondary_key = encrypt.EncryptorDecryptor.generate_key()

    secondary_encryptor = encrypt.EncryptorDecryptor(secondary_key)

    joint_encryptor = encrypt.EncryptorDecryptor((primary_key, secondary_key))

    with tempfile.TemporaryDirectory() as directory:
        value_filename = os.path.join(directory, 'value.bin')

        secondary_encryptor.encrypt_to_file(value, value_filename)

        secondary_encryptor.rotate_file(value_filename)

        loaded = secondary_encryptor.decrypt_from_file(value_filename)
        assert loaded == value

        joint_encryptor.rotate_file(value_filename)

        none_encryptor = _make_temporary_encryptor()
        with pytest.raises(RecoveredException):
            none_encryptor.decrypt_from_file(value_filename)

        with pytest.raises(RecoveredException):
            secondary_encryptor.decrypt_from_file(value_filename)

        loaded = primary_encryptor.decrypt_from_file(value_filename)
        assert loaded == value

        loaded = joint_encryptor.decrypt_from_file(value_filename)
        assert loaded == value

    return


def test__decrypt_from_file__no_file_exception() -> None:
    encryptor = _make_temporary_encryptor()

    with pytest.raises(FileNotFoundError):
        encryptor.decrypt_from_file("any file")

    return


@pytest.mark.parametrize('default', (
    None,
    'str',
))
def test__decrypt_from_file__no_file__default(default: object) -> None:
    encryptor = _make_temporary_encryptor()

    value = encryptor.decrypt_from_file(
        "any file", use_default=True, default=default)

    assert value == default
