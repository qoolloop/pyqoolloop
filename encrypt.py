"""
Convenience functions for encrypting/decrypting via json
"""
import base64
from typing import (
    Iterable,
    Sequence,
    Union,
)

import cryptography.fernet
from cryptography.fernet import (
    Fernet,
    MultiFernet,
)
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import msgpack  #FUTURE: Can use Packer class for speed up

from pyexception.exception import (
    Reason,
    RecoveredException,
    FileExists,
)

from .fileio import open_write_binary

import pylog  # pylint: disable=wrong-import-order
_logger = pylog.getLogger(__name__)


class InvalidToken(Reason):
    """
    Reason for exception raised when token is invalid
    """


def key_from_password(password: str, salt: bytes) -> bytes:
    """
    Obtain (hashed) key from password

    :param password: Password to hash.
    :param salt: Salt to use for hashing.
    """
    # https://cryptography.io/en/latest/fernet/#using-passwords-with-fernet
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend()
    )

    password_bytes = password.encode('utf-8')
    key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
    return key


_TUPLE_TYPE = 100
_SET_TYPE = 101


def _packb(value: object) -> bytes:
    encoded = msgpack.packb(
        value,
        use_bin_type=True, strict_types=True,
        default=_msgpack_default)
    return encoded


def _unpackb(encoded: bytes) -> object:
    value = msgpack.unpackb(encoded, raw=False, ext_hook=_msgpack_ext_hook)
    return value


def _msgpack_default(obj: Iterable[object]) -> msgpack.ExtType:
    if isinstance(obj, tuple):
        obj_type = _TUPLE_TYPE
        data = _packb(list(obj))

    elif isinstance(obj, set):
        obj_type = _SET_TYPE
        data = _packb(list(obj))

    else:
        raise TypeError("Unexpected type: %r" % (obj,))
    
    return msgpack.ExtType(obj_type, data)


def _msgpack_ext_hook(code: int, data: bytes) -> object:

    if code == _TUPLE_TYPE:
        unpacked_iterable = _unpackb(data)
        # warning: https://stackoverflow.com/a/36407550/2400328
        # Using `Iterable` to convince `mypy`
        assert isinstance(unpacked_iterable, Iterable)
        obj: object = tuple(unpacked_iterable)

    elif code == _SET_TYPE:
        unpacked_iterable = _unpackb(data)
        # warning: https://stackoverflow.com/a/36407550/2400328
        # Using `Iterable` to convince `mypy`
        assert isinstance(unpacked_iterable, Iterable)
        obj = set(unpacked_iterable)
        
    else:
        obj = msgpack.ExtType(code, data)

    return obj


class EncryptorDecryptor:
    """
    Class for encryption and decryption

    This can encrypt and decrypt various types of data.
    """

    _FernetType = Union[Fernet, MultiFernet]
    _fernet: _FernetType
    _primary_fernet: Fernet

    def __init__(self, key: Union[bytes, Sequence[bytes]]):
        """
        :param key: The key for encryption.
          Otherwise, a list of candidate keys for decryption. Only the
          first (primary) key is used for encryption. Keys must be generated
          with :func:`generate_key()`.
        """
        def _check_key(key: bytes) -> None:
            decoded_key = base64.urlsafe_b64decode(key)
            assert len(decoded_key) == 32, \
                "Key length: %d\n%s" % \
                (len(decoded_key), decoded_key)  # type:ignore[str-bytes-safe]


        if isinstance(key, bytes):
            _check_key(key)
            self._fernet = Fernet(key)
            self._primary_fernet = self._fernet

        else:
            for each in key:
                _check_key(each)

            fernets = [Fernet(each) for each in key]

            self._fernet = MultiFernet(fernets)
            self._primary_fernet = Fernet(key[0])

        # endif


    @classmethod
    def generate_key(cls) -> bytes:
        """
        Generate key for encryption and decryption

        To be used by :func:`EncryptorDecryptor()`.
        """

        
        return Fernet.generate_key()


    @staticmethod
    def _read_file(filename: str) -> bytes:
        with open(filename, 'rb') as read_file:
            encrypted = read_file.read()

        return encrypted

    
    @staticmethod
    def _write_file(
            encrypted: bytes, filename: str, overwrite: bool = False) -> None:
        try:
            with open_write_binary(filename, overwrite=overwrite) \
                 as write_file:
                write_file.write(encrypted)

        except FileExistsError as exception:
            raise RecoveredException(
                "File exists", FileExists, logger=_logger) from exception

        # endtry


    @staticmethod
    def _make__RecoveredException__InvalidToken(
            exception: cryptography.fernet.InvalidToken) -> RecoveredException:
        try:  # necessary for use with `from` below
            raise RecoveredException(
                "Could not read value",
                reason=InvalidToken,
                logger=_logger) from exception

        except RecoveredException as raised_exception:
            return raised_exception

        # enddef
        

    def encrypt(self, value: object) -> bytes:
        """
        Encrypt various types of data

        :param value: Value to encrypt
          Supported root types:
            dict, list, tuple, set, bytes, str, int, float, bool, type(None)
          Supported value types:
            dict, list, str, int, float, bool, type(None)

        :return: Result of encryption
        """
        encoded = _packb(value)
        result = self._fernet.encrypt(encoded)
        return result
        

    def encrypt_to_file(
            self, value: object, filename: str, overwrite: bool = False
    ) -> None:
        """
        Encrypt various types of data and save to file

        :param value: Value to encrypt
        :param filename: Path of file to save to.  #TODO: rename `path`
        :param overwrite: Needs to be `True` to overwrite existing file.
        """
        encrypted = self.encrypt(value)

        if isinstance(encrypted, str):
            encrypted = encrypted.encode('utf-8')

        self._write_file(encrypted, filename, overwrite=overwrite)


    @classmethod
    def _decrypt(cls, fernet: _FernetType, encrypted: bytes) -> object:

        def _get_encoded(encrypted: bytes) -> bytes:
            try:
                encoded = fernet.decrypt(encrypted)

            except cryptography.fernet.InvalidToken as exception:
                raise cls._make__RecoveredException__InvalidToken(exception)

            return encoded


        encoded = _get_encoded(encrypted)
        value = _unpackb(encoded)
        return value


    def decrypt(self, encrypted: bytes) -> object:
        """
        Decrypt data to same type as when the data was encrypted

        :param encrypted: -- (bytes/str) result of self.encrypt()

        :return: Decrypted value.

        :raises RecoveredException(InvalidToken): Could not read value.
        """
        return self._decrypt(self._fernet, encrypted)
        

    def _decrypt_from_file(
            self, fernet: _FernetType,
            filename: str,
            use_default: bool = False,
            default: object = None
    ) -> object:
        try:
            encrypted = self._read_file(filename)

        except FileNotFoundError:
            if use_default:
                return default

            raise
        
        decrypted = self._decrypt(fernet, encrypted)
        return decrypted


    def decrypt_from_file(
            self,
            filename: str,
            use_default: bool = False,
            default: object = None
    ) -> object:
        """
        Decrypt contents of file saved by :func:`encrypt_to_file()`

        :param filename: Path to file that stores a value  #TODO: rename `path`
        :param use_default: Whether to return `default` when file does not
            exist.
        :param default: (object) Value to return, when file does not exist, and
            `use_default` is True.

        :return: Decrypted value.

        :raises RecoveredException(InvalidToken): Could not read value.
        """
        return self._decrypt_from_file(
            self._fernet, filename, use_default=use_default, default=default)


    def rotate_file(self, filename: str) -> None:
        """
        Encrypt contents of a file again with the primary key

        .. note:: This makes encrypted files use the primary key even if they
          were encrypted with other keys.

        :param filename: Path to file that stores a value  #TODO: rename `path`
        """
        encrypted = self._read_file(filename)

        try:
            # try with primary key, and don't save if ok
            decrypted = self._decrypt(self._primary_fernet, encrypted)

        except RecoveredException as exception:
            if not exception.get_reason().isa(InvalidToken):
                raise

            # try with all keys
            decrypted = self.decrypt(encrypted)
            self.encrypt_to_file(decrypted, filename, overwrite=True)
