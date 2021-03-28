"""
Tests for `encrypt` module.
"""
import math
import os
import sys
import tempfile

import pytest

from pyexception.exception import (
    RecoveredException,
    FileExists,
)
from pyexception import testutils


from . import (
    encrypt,
    testregression,
)

import pylog  # pylint: disable=wrong-import-order
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
    """
    Test that `key_from_password()` produces consistent results.
    """
    save = False
    
    key = encrypt.key_from_password(password, salt)
    testregression.assert_no_change(key, save=save, index=index)

    # Make sure same PBKDF2HMAC is not used twice, but produces same results
    key = encrypt.key_from_password(password, salt)
    testregression.assert_no_change(key, save=False, index=index)


def test__encrypt_to_file__overwrite() -> None:
    """
    Test behavior of `encrypt_to_file()` when file already exists.
    """
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

    # endwith


@pytest.mark.parametrize('_index, value', (
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
def test__encrypt_decrypt(_index: float, value: object) -> None:
    """
    Test that `decrypt()` is possible after `encrypt()`.
    """
    logger.info("value: %r", value)
                         
    encryptor = _make_temporary_encryptor()

    encrypted = encryptor.encrypt(value)
    decrypted = encryptor.decrypt(encrypted)
    if isinstance(value, float) and math.isnan(value):
        assert isinstance(decrypted, float)
        assert math.isnan(decrypted)

    else:
        assert decrypted == value

    # endif


@pytest.mark.parametrize('_index, value', (
    (1.1, 'password'),
    (1.2, 'mixed1234!@#$%^&*()_+{}|:"<>?-=[]\\;\',./'),
))
def test__encrypt_decrypt_from_file(_index: float, value: str) -> None:
    """
    Test that `decrypt_from_file()` can read a file stored by
    `encrypt_to_file()`.
    """
    encryptor = _make_temporary_encryptor()

    with tempfile.TemporaryDirectory() as directory:
        value_filename = os.path.join(directory, 'value.bin')

        encryptor.encrypt_to_file(value, value_filename)

        loaded = encryptor.decrypt_from_file(value_filename)

        assert loaded == value

    # endwith


@pytest.mark.parametrize('index, value', (
    (1.1, 'password'),
    (1.2, 'mixed1234!@#$%^&*()_+{}|:"<>?-=[]\\;\',./'),
))
def test__encrypt_decrypt_from_file__no_change(
        index: float, value: str) -> None:
    """
    Test that `decrypt_from_file()` can read a file stored in the past by
    `encrypt_to_file()`.
    """
    save = False

    key_filename = testregression.make_filename(
        index=index, suffix='key', extension='.bin')

    if save:
        key = encrypt.EncryptorDecryptor.generate_key()

        with open(key_filename, 'wb') as key_file:
            key_file.write(key)

        logger.info("Key length: %d", len(key))

    with open(key_filename, 'rb') as key_file:
        key = key_file.read()
        
    logger.info("Key length: %d", len(key))

    encryptor = encrypt.EncryptorDecryptor(key)

    value_filename = testregression.make_filename(
        index=index, extension='.bin')

    if save:
        encryptor.encrypt_to_file(value, value_filename)

    loaded = encryptor.decrypt_from_file(value_filename)

    assert loaded == value

    assert not save, "Warning"


@pytest.mark.parametrize('_index, value', (
    (1.1, 'password'),
    (1.2, 'mixed1234!@#$%^&*()_+{}|:"<>?-=[]\\;\',./'),
))
def test__encrypt_decrypt_from_file__no_change__auto_rotate(
        _index: float, value: str) -> None:
    """
    Test that `decrypt_from_file()` can read from files that are generated
    with all its keys.
    """
    primary_key = encrypt.EncryptorDecryptor.generate_key()

    primary_encryptor = encrypt.EncryptorDecryptor(primary_key)

    secondary_key = encrypt.EncryptorDecryptor.generate_key()

    secondary_encryptor = encrypt.EncryptorDecryptor(secondary_key)

    joint_encryptor = encrypt.EncryptorDecryptor((primary_key, secondary_key))

    with tempfile.TemporaryDirectory() as directory:
        value_filename = os.path.join(directory, 'value.bin')

        primary_encryptor.encrypt_to_file(
            value, value_filename)

        loaded = joint_encryptor.decrypt_from_file(value_filename)
        assert loaded == value

        secondary_encryptor.encrypt_to_file(
            value, value_filename, overwrite=True)

        loaded = joint_encryptor.decrypt_from_file(value_filename)
        assert loaded == value

    # endwith


@pytest.mark.parametrize('_index, value', (
    (1.1, 'password'),
    (1.2, 'mixed1234!@#$%^&*()_+{}|:"<>?-=[]\\;\',./'),
))
def test__security(
        _index: float, value: str) -> None:
    """
    Test that files generated with one key cannot be decrypted with another.
    """
    primary_key = encrypt.EncryptorDecryptor.generate_key()

    primary_encryptor = encrypt.EncryptorDecryptor(primary_key)

    secondary_key = encrypt.EncryptorDecryptor.generate_key()

    secondary_encryptor = encrypt.EncryptorDecryptor(secondary_key)

    with tempfile.TemporaryDirectory() as directory:
        value_filename = os.path.join(directory, 'value.bin')

        primary_encryptor.encrypt_to_file(value, value_filename)

        with pytest.raises(RecoveredException):
            secondary_encryptor.decrypt_from_file(value_filename)

        # endwith
    # endwith

    
@pytest.mark.parametrize('_index, value', (
    (1.1, 'password'),
    (1.2, 'mixed1234!@#$%^&*()_+{}|:"<>?-=[]\\;\',./'),
))
def test__rotate_file(
        _index: float, value: str) -> None:
    """
    Test that the primary key is used for encryption after `rotate_file()`.
    """
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

        with pytest.raises(RecoveredException):
            secondary_encryptor.decrypt_from_file(value_filename)

        loaded = primary_encryptor.decrypt_from_file(value_filename)
        assert loaded == value

        loaded = joint_encryptor.decrypt_from_file(value_filename)
        assert loaded == value

    # endwith
    

def test__decrypt_from_file__no_file_exception() -> None:
    """
    Test that `decrypt_from_file()` raises `FileNotFoundError`, when
    file doesn't exist.
    """
    encryptor = _make_temporary_encryptor()

    with pytest.raises(FileNotFoundError):
        encryptor.decrypt_from_file("any file")

    # endwith


@pytest.mark.parametrize('default', (
    None,
    'str',
))
def test__decrypt_from_file__no_file__default(default: object) -> None:
    """
    Test that `decrypt_from_file()` returns default value, when file doesn't
    exist.
    """
    encryptor = _make_temporary_encryptor()

    value = encryptor.decrypt_from_file(
        "any file", use_default=True, default=default)

    assert value == default
