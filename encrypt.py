"""
Convenience functions for encrypting/decrypting string serializable objects
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


class EncryptDecryptor:

    def __init__(self, key):
        """
        Argument:
          key -- (bytearray/list of bytearray) The key for encryption.
            Otherwise, a list of candidate keys for decryption. Only the
            first key is used for encryption.
        """
        self._key = key


    def _encrypt_bytearray(self, byte_array):
        TODO


    def _encrypt_str(self, string):
        TODO


    def _encrypt_dict(self, dictionary):
        """
        Notes:
          Currently, only the following value types are supported:
            bytearray, str
        """
        TODO


    def encrypt(self, value):
        TODO
        

    def encrypt_to_file(self, filename):
        TODO


    def decrypt(self, encrypted):
        TODO


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
