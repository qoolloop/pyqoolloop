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

        else:
            for each in key:
                _check_key(each)

            self._fernet = MultiFernet(key)

        return


    @classmethod
    def generate_key(cls):
        return Fernet.generate_key()


    def encrypt(self, value, *, no_encryption=False):
        """
        Arguments:
          value -- (dict/list/tuple/str/int/float/bool/None) Value to encrypt
          no_encryption -- (bool) When True, don't encrypt.
            Mainly for debugging purposes.

        Returns:
          One of either:
            - (bytes) result of encryption
            - (str) json encoded `value`

        Notes:
          Currently, only the following value types are supported for dict:
            dict/list/str/int/float/bool/None
          Note that tuple is not included.
        """
        def _check_top_level(value):

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

                supported_types = (
                    dict, list, str, int, float, bool, type(None))
                assert isinstance(value, supported_types)

                if isinstance(value, dict):
                    _check_types_dict(value)

                elif isinstance(value, list):
                    _check_types_list(value)

                return


            supported_types = (
                dict, list, tuple, str, int, float, bool, type(None))
            assert isinstance(value, supported_types)

            if isinstance(value, tuple):
                _check_types_list(value)

            else:
                _check_types(value)

            return
            

        _check_top_level(value)
        
        json_string = json.dumps(
            {'type': type(value).__name__, 'value': value})

        if no_encryption:
            result = json_string

        else:
            result = self._fernet.encrypt(json_string.encode('utf-8'))

        return result
        

    def encrypt_to_file(self, value, filename, *, no_encryption=False):
        encrypted = self.encrypt(value, no_encryption=no_encryption)
        with open(filename, 'wb') as f:
            f.write(encrypted)

        return


    def decrypt(self, encrypted):
        """
        Decrypt data to same type as when the data was encrypted

        Argument:
          encrypted -- (bytes/str) result of self.encrypt()
        """

        def _get_json_string(encrypted):
            if isinstance(encrypted, str):
                json_string = encrypted

            else:
                json_string = self._fernet.decrypt(encrypted).decode('utf-8')

            return json_string


        def _fix_type(value, type_string):
            if type_string == 'tuple':
                return tuple(value)

            return value


        json_string = _get_json_string(encrypted)

        dictionary = json.loads(json_string)

        value = dictionary['value']
        value = _fix_type(value, dictionary['type'])

        assert value.__class__.__name__ == dictionary['type'], \
            "value type (%s) != decrypted type (%s)" % \
            (value.__class__.__name__, dictionary['type'])

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
        assert not auto_encrypt, "TODO"
        assert not auto_rotate, "TODO"

        with open(filename, 'rb') as f:
            encrypted = f.read()

        decrypted = self.decrypt(encrypted)
        return decrypted
