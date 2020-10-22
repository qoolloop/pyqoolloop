"""
Convenience functions for encrypting/decrypting via json
"""
import base64
import cryptography.fernet
from cryptography.fernet import (
    Fernet,
    MultiFernet,
)
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import msgpack  #TODO: Can use Packer class for speed up

from pyexception.exception import (
    Reason,
    RecoveredException,  #TODO: Use Recoveredexception in other modules
    FileExists,
)

import pylog
logger = pylog.getLogger(__name__)


class InvalidToken(Reason):
    pass


def key_from_password(password, salt):
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


def _packb(value):
    encoded = msgpack.packb(
        value,
        use_bin_type=True, strict_types=True,
        default=msgpack_default)
    return encoded


def _unpackb(encoded):
    value = msgpack.unpackb(encoded, raw=False, ext_hook=msgpack_ext_hook)
    return value


def msgpack_default(obj):
    logger.info("obj: %r" % (obj,))  #TODO: remove
    if isinstance(obj, tuple):
        obj_type = _TUPLE_TYPE
        data = _packb([each for each in obj])

    elif isinstance(obj, set):
        obj_type = _SET_TYPE
        data = _packb([each for each in obj])

    else:
        raise TypeError("Unexpected type: %r" % (obj,))
    
    return msgpack.ExtType(obj_type, data)


def msgpack_ext_hook(code, data):
    logger.info("data: %r" % (data, ))  #TODO: remove

    if code == _TUPLE_TYPE:
        obj = tuple(_unpackb(data))

    elif code == _SET_TYPE:
        obj = set(_unpackb(data))
        
    else:
        obj = msgpack.ExtType(code, data)

    return obj


class EncryptorDecryptor:

    def __init__(self, key):
        """
        Argument:
          key -- (bytes/list of bytes) The key for encryption.
            Otherwise, a list of candidate keys for decryption. Only the
            first key is used for encryption. Keys must be generated with
            generate_key().
        """
        def _check_key(key):
            decoded_key = base64.urlsafe_b64decode(key)
            assert len(decoded_key) == 32, \
                "Key length: %d\n%s" % (len(decoded_key), decoded_key)


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

        return


    @classmethod
    def generate_key(cls):
        return Fernet.generate_key()


    @staticmethod
    def _read_file(filename):
        with open(filename, 'rb') as f:
            encrypted = f.read()

        return encrypted

    
    @staticmethod
    def _write_file(encrypted, filename, overwrite=False):
        if overwrite:
            mode = 'wb'

        else:
            mode = 'xb'
            
        try:
            with open(filename, mode) as f:
                f.write(encrypted)

        except FileExistsError as e:
            raise RecoveredException(
                "File exists", FileExists, logger=logger) from e

        return


    @staticmethod
    def _make_RecoveredException_InvalidToken(e):
        try:
            raise RecoveredException(
                "Could not read value",
                reason=InvalidToken,
                logger=logger) from e

        except Exception as e:
            return e

        return
        

    _supported_root_types = (
        dict, list, tuple, bytes, str, int, float, bool, type(None))

    # Note that tuple is not included.
    _supported_value_types = (
        dict, list, str, int, float, bool, type(None)
    )

    def encrypt(self, value):
        """
        Arguments:
          value -- (object) Value to encrypt

        Returns:
          (bytes) result of encryption
        """
        encoded = _packb(value)
        result = self._fernet.encrypt(encoded)
        return result
        

    def encrypt_to_file(self, value, filename, overwrite=False):
        encrypted = self.encrypt(value)

        if isinstance(encrypted, str):
            encrypted = encrypted.encode('utf-8')

        self._write_file(encrypted, filename, overwrite=overwrite)

        return


    @classmethod
    def _decrypt(cls, fernet, encrypted):

        def _get_encoded(encrypted):
            try:
                encoded = fernet.decrypt(encrypted)

            except cryptography.fernet.InvalidToken as e:
                raise cls._make_RecoveredException_InvalidToken(e)

            return encoded


        encoded = _get_encoded(encrypted)
        value = _unpackb(encoded)
        return value


    def decrypt(self, encrypted):
        """
        Decrypt data to same type as when the data was encrypted

        Argument:
          encrypted -- (bytes/str) result of self.encrypt()

        Raises:
          RecoveredException(InvalidToken) -- Could not read value.
        """
        return self._decrypt(self._fernet, encrypted)
        

    def _decrypt_from_file(
            self, fernet, filename, use_default=False, default=None):
        try:
            encrypted = self._read_file(filename)

        except FileNotFoundError as e:
            if use_default:
                return default

            raise
        
        decrypted = self._decrypt(fernet, encrypted)
        return decrypted


    def decrypt_from_file(self, filename, use_default=False, default=None):
        """
        Arguments:
          filename: (str) Path to file that stores a value
          use_default: (bool) Whether to return `default` when file does not
            exist.
          default: (object) Value to return, when file does not exist, and
            `use_default` is True.

        Returns:
          Decrypted value.

        Raises:
          RecoveredException(InvalidToken) -- Could not read value.
        """
        return self._decrypt_from_file(
            self._fernet, filename, use_default=use_default, default=default)


    def rotate_file(self, filename):
        encrypted = self._read_file(filename)

        try:
            # try with primary key
            decrypted = self._decrypt(self._primary_fernet, encrypted)

        except RecoveredException as e:
            if not e.get_reason().isa(InvalidToken):
                raise

            # try with all keys
            decrypted = self.decrypt(encrypted)
            self.encrypt_to_file(decrypted, filename, overwrite=True)
