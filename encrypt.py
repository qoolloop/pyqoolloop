"""
Convenience functions for encrypting/decrypting via json
"""
#TODO: May want to switch to a binary encoding instead of json
import base64
import cryptography.fernet
from cryptography.fernet import (
    Fernet,
    MultiFernet,
)
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import ujson as json
import msgpack  #TODO: Can use Packer class for speed up

from pyexception import (
    Reason,
    RecoveredException,
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


def msgpack_default(obj):
    if isinstance(obj, tuple):
        logger.info("packing: %r" % (obj,))  #TODO: remove
        return msgpack.ExtType(_TUPLE_TYPE, json.dumps(obj).encode('utf-8'))

    raise TypeError("Unexpected type: %r" % (obj,))


def msgpack_ext_hook(code, data):
    if code == _TUPLE_TYPE:
        obj = tuple(json.loads(data.decode('utf-8')))
        logger.info("unpacked: %r" % (obj,))  #TODO: remove

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
    def _write_file(encrypted, filename):
        with open(filename, 'wb') as f:
            f.write(encrypted)

        return


    @staticmethod
    def _make_RecoveredException_InvalidToken(e):
        return RecoveredException(
            "Could not read value",
            reason=InvalidToken,
            cause=e,
            logger=logger)
        

    _supported_root_types = (
        dict, list, tuple, bytes, str, int, float, bool, type(None))

    # Note that tuple is not included.
    _supported_value_types = (
        dict, list, str, int, float, bool, type(None)
    )

    def encrypt(self, value, *, no_encryption=False):
        #TODO: remove no_encryption
        """
        Arguments:
          value -- (types defined in _supported_root_types) Value to encrypt
            Types supported for values in a dict are defined in
            _supported_value_types  #TODO: not anymore?
          no_encryption -- (bool) When True, don't encrypt.
            Mainly for debugging purposes.

        Returns:
          One of either:
            When no_encryption=True:
              (bytes) result of encryption
            When no_encryption=False:
              (bytes) binary encoded value
        """
        def _check_from_root_level(value):

            def _check_types_list(value):
                for each in value:
                    _check_types(each)

                return


            def _check_types_dict(value):
                for key, value in value.items():
                    assert isinstance(key, str)
                    _check_types(value)

                return


            def _check_types(value):

                assert isinstance(value, self._supported_value_types), \
                    ("Values of type (%s) are not supported" %
                     type(value).__name__)

                if isinstance(value, dict):
                    _check_types_dict(value)

                elif isinstance(value, list):
                    _check_types_list(value)

                return


            assert isinstance(value, self._supported_root_types)

            if isinstance(value, tuple):
                _check_types_list(value)

            elif isinstance(value, (str, bytes)):
                return
            
            else:
                _check_types(value)

            return


        _check_from_root_level(value)

        encoded = msgpack.packb(
            value,
            use_bin_type=True, strict_types=True,
            default=msgpack_default)

        if no_encryption:
            result = encoded

        else:
            result = self._fernet.encrypt(encoded)

        return result
        

    def encrypt_to_file(self, value, filename, *, no_encryption=False):
        encrypted = self.encrypt(value, no_encryption=no_encryption)

        if isinstance(encrypted, str):
            encrypted = encrypted.encode('utf-8')

        self._write_file(encrypted, filename)

        return


    @classmethod
    def _decrypt(cls, fernet, encrypted):

        def _get_encoded(encrypted):
            try:
                encoded = fernet.decrypt(encrypted)

            except cryptography.fernet.InvalidToken as e:
                raise cls._make_RecoveredException_InvalidToken(e)

            return encoded


        logger.info("len(encrypted): %d" % len(encrypted))  #TODO: remove
        encoded = _get_encoded(encrypted)
        logger.info("len(encoded): %d" % len(encoded))  #TODO: remove
        value = msgpack.unpackb(encoded, raw=False, ext_hook=msgpack_ext_hook)
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
        

    def _decrypt_from_file(self, fernet, filename):
        encrypted = self._read_file(filename)
        decrypted = self._decrypt(fernet, encrypted)
        return decrypted


    def decrypt_from_file(self, filename):
        """
        Arguments:
          filename: (str) path to file that stores a value

        Returns:
          Decrypted value.

        Raises:
          RecoveredException(InvalidToken) -- Could not read value.
        """
        return self._decrypt_from_file(self._fernet, filename)


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
            self.encrypt_to_file(decrypted, filename)

        except:
            raise
