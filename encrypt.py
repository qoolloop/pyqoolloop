"""
Convenience functions for encrypting/decrypting via json

Pickling is not used because of concerns about security.
"""
import base64
from cryptography.fernet import (
    Fernet,
    MultiFernet,
)
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import ujson as json


import pylog
logger = pylog.getLogger(__name__)


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


class EncryptorDecryptor:

    def __init__(self, key):
        """
        Argument:
          key -- (bytes/list of bytes) The key for encryption.
            Otherwise, a list of candidate keys for decryption. Only the
            first key is used for encryption. Keys must be bytes of length 32.
        """
        if isinstance(key, bytes):
            assert len(base64.urlsafe_b64decode(key)) == 32
            self._fernet = Fernet(key)

        else:
            for each in key:
                assert len(base64.urlsafe_b64decode(each)) == 32

            self._fernet = MultiFernet(key)

        return


    def _encrypt_bytes(self, byte_array):
        TODO


    def _encrypt_str(self, string):
        TODO


    def _encrypt_dict(self, dictionary):
        """
        """
        TODO


    def encrypt(self, value, *, no_encryption=False):
        """
        Arguments:
          value -- (dict/list/tuple/int/float/bool/None) Value to encrypt
          no_encryption -- (bool) When True, don't encrypt.
            Mainly for debugging purposes.

        Returns:
          One of either:
            - (bytes) result of encryption
            - (str) json encoded `value`

        Notes:
          Currently, only the following value types are supported for dict:
            bytes, str
        """
        json_string = json.dumps({'type': str(type(value)), 'value': value})

        if no_encryption:
            result = json_string

        else:
            result = self._fernet.encrypt(json_string.encode('utf-8'))

        return result
        

    def encrypt_to_file(self, filename):
        TODO


    def decrypt(self, encrypted):
        """
        Decrypt data to same type as when the data was encrypted

        Argument:
          encrypted -- (bytes/str) result of self.encrypt()
        """
        if isinstance(encrypted, str):
            json_string = encrypted

        else:
            json_string = self._fernet.decrypt(encrypted).decode('utf-8')

        dictionary = json.loads(json_string)

        value = dictionary['value']

        assert str(type(value)) == dictionary['type'], \
            "value type (%s) != decrypted type (%s)" % \
            (str(type(value)), dictionary['type'])

        return value


    def decrypt_from_file(self, filename,
                          auto_encrypt=False, auto_rotate=False):
        """
        Arguments:
          filename: (str) path to file that stores a value
          auto_encrypt: (bool) When True, this function will encrypt the
            contents of the file, if it is not encrypted.
          auto_rotate: (bool) When True, reencrypts the file with the first
            key in the key list.
        """
        TODO
