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
        """
        Arguments:
          value -- (types defined in _supported_root_types) Value to encrypt
            Types supported for values in a dict are defined in
            _supported_value_types
          no_encryption -- (bool) When True, don't encrypt.
            Mainly for debugging purposes.

        Returns:
          One of either:
            - (bytes) result of encryption
            - (str) json encoded `value`
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


        def _convert(value):
            if isinstance(value, bytes):
                return value.decode('utf-8')  #TODO: Is utf-8 appropriate?

            return value
            

        _check_from_root_level(value)

        value = _convert(value)
        
        json_string = json.dumps(
            {'type': type(value).__name__, 'value': value})

        if no_encryption:
            result = json_string

        else:
            result = self._fernet.encrypt(json_string.encode('utf-8'))

        return result
        

    def encrypt_to_file(self, value, filename, *, no_encryption=False):
        encrypted = self.encrypt(value, no_encryption=no_encryption)

        if isinstance(encrypted, str):
            encrypted = encrypted.encode('utf-8')

        self._write_file(encrypted, filename)

        return


    @classmethod
    def _decrypt(cls, fernet, encrypted):

        def _get_json_string(encrypted):
            if isinstance(encrypted, str):
                json_string = encrypted

            else:
                try:
                    json_string = fernet.decrypt(encrypted).decode('utf-8')

                except cryptography.fernet.InvalidToken as e:
                    raise cls._make_RecoveredException_InvalidToken(e)

            return json_string


        def _fix_type(value, type_string):
            if type_string == 'tuple':
                return tuple(value)

            elif type_string == 'bytes':
                return value.encode('utf-8')  #TOOD: Is utf-8 appropriate?

            return value


        json_string = _get_json_string(encrypted)

        dictionary = json.loads(json_string)

        value = dictionary['value']
        value = _fix_type(value, dictionary['type'])

        assert value.__class__.__name__ == dictionary['type'], \
            "value type (%s) != decrypted type (%s)" % \
            (value.__class__.__name__, dictionary['type'])

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
        

    def _decrypt_from_file(self, fernet, filename, auto_encrypt=False):
        #TODO: remove auto_encrypt

        def _parse_json_string(json_string):
            json_string = encrypted.decode('utf-8')
            
            if not (json_string.startswith('{"type":"') or
                    json_string.startswith('{"value":"')):
                raise self._make_RecoveredException_InvalidToken(None)

            value = self._decrypt(fernet, json_string)

            if auto_encrypt:
                self.encrypt_to_file(value, filename)

            return value
            

        encrypted = self._read_file(filename)

        try:
            decrypted = self._decrypt(fernet, encrypted)

        except RecoveredException as e:
            if not e.get_reason().isa(InvalidToken):
                raise

            value = _parse_json_string(encrypted)
            return value
        
        return decrypted


    def decrypt_from_file(self, filename, auto_encrypt=False):
        """
        Arguments:
          filename: (str) path to file that stores a value
          auto_encrypt: (bool) When True, this function will encrypt the
            contents of the file, if it is not encrypted.

        Returns:
          Decrypted value.

        Raises:
          RecoveredException(InvalidToken) -- Could not read value.
        """
        return self._decrypt_from_file(
            self._fernet, filename, auto_encrypt=auto_encrypt)


    def rotate_file(self, filename):
        encrypted = self._read_file(filename)

        try:
            decrypted = self._decrypt(self._primary_fernet, encrypted)

        except RecoveredException as e:
            if not e.get_reason().isa(InvalidToken):
                raise

            try:
                decrypted = self.decrypt(encrypted)

            except RecoveredException as e:
                if not e.get_reason().isa(InvalidToken):
                    raise

                json_string = encrypted.decode('utf-8')
                decrypted = self.decrypt(json_string)
                                
            self.encrypt_to_file(decrypted, filename)

        except:
            raise
