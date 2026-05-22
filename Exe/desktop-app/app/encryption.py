from cryptography.fernet import Fernet
from app.config import get_settings
import base64
import hashlib

settings = get_settings()


def _get_encryption_key():
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(key)


def encrypt_credentials(credentials_json: str) -> str:
    f = Fernet(_get_encryption_key())
    encrypted = f.encrypt(credentials_json.encode())
    return encrypted.decode()


def decrypt_credentials(encrypted_credentials: str) -> str:
    f = Fernet(_get_encryption_key())
    decrypted = f.decrypt(encrypted_credentials.encode())
    return decrypted.decode()
