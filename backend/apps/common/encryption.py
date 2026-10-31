"""
Field-Level Encryption Architecture for FixPoint Drive Safe-QR SOS.

Cryptographic Standard:
- Utilizes AES-128 in CBC mode with PKCS7 padding and HMAC-SHA256 for integrity verification,
  provided by the industry-standard `cryptography.fernet.Fernet` specification.
- Each ciphertext output contains a timestamp and 128-bit initialization vector (IV) generated
  cryptographically securely.

Key Management Requirements:
1. Generation: Keys must be 32 url-safe base64-encoded bytes (generated via `Fernet.generate_key()`).
2. Storage: FIELD_ENCRYPTION_KEY must never be committed to source control. In production, load from
   environment variables populated by a secure secrets manager (AWS Secrets Manager, GCP Secret Manager, or HashiCorp Vault).
3. Key Rotation: When rotating keys, a MultiFernet instance can be configured to decrypt data encrypted with
   previous keys while re-encrypting with the primary current key.
"""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models
from cryptography.fernet import Fernet, InvalidToken

class FieldEncryptionService:
    """
    Centralized service for symmetric field-level encryption and decryption.
    """
    _fernet = None
    _current_key = None

    @classmethod
    def reset_cipher(cls):
        """
        Resets cached cipher instance (useful when switching settings dynamically during tests).
        """
        cls._fernet = None
        cls._current_key = None

    @classmethod
    def get_cipher(cls) -> Fernet:
        key = getattr(settings, 'FIELD_ENCRYPTION_KEY', None)
        if not key:
            raise ImproperlyConfigured(
                "FIELD_ENCRYPTION_KEY setting is required for field-level encryption."
            )
        if isinstance(key, str):
            key_bytes = key.encode('utf-8')
        else:
            key_bytes = key

        if cls._fernet is None or cls._current_key != key_bytes:
            try:
                cls._fernet = Fernet(key_bytes)
                cls._current_key = key_bytes
            except Exception:
                raise ImproperlyConfigured(
                    "Invalid FIELD_ENCRYPTION_KEY format. Must be a valid 32 url-safe base64 key."
                )
        return cls._fernet


    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """
        Encrypts a plaintext string into a Fernet ciphertext string.
        """
        if plaintext is None or plaintext == '':
            return plaintext
        cipher = cls.get_cipher()
        encrypted_bytes = cipher.encrypt(plaintext.encode('utf-8'))
        return encrypted_bytes.decode('utf-8')

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        """
        Decrypts a Fernet ciphertext string into plaintext string.
        Gracefully returns value if not encrypted or on legacy plain values during migration.
        """
        if ciphertext is None or ciphertext == '':
            return ciphertext
        cipher = cls.get_cipher()
        try:
            decrypted_bytes = cipher.decrypt(ciphertext.encode('utf-8'))
            return decrypted_bytes.decode('utf-8')
        except InvalidToken:
            # If value cannot be decrypted (e.g. unencrypted mock/seed data during testing),
            # return as-is rather than failing catastrophically.
            return ciphertext

class EncryptedCharField(models.CharField):
    """
    CharField with automatic AES/Fernet encryption at rest in the database.
    """
    def __init__(self, *args, **kwargs):
        # Allow sufficient length for Fernet overhead (IV, HMAC, base64 encoding)
        kwargs.setdefault('max_length', 512)
        super().__init__(*args, **kwargs)

    def get_prep_value(self, value):
        val = super().get_prep_value(value)
        if val is None or val == '':
            return val
        return FieldEncryptionService.encrypt(str(val))

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return value
        return FieldEncryptionService.decrypt(value)

    def to_python(self, value):
        if value is None or value == '':
            return value
        # If the value comes from serialization or raw input
        return FieldEncryptionService.decrypt(value)

class EncryptedTextField(models.TextField):
    """
    TextField with automatic AES/Fernet encryption at rest in the database.
    """
    def get_prep_value(self, value):
        val = super().get_prep_value(value)
        if val is None or val == '':
            return val
        return FieldEncryptionService.encrypt(str(val))

    def from_db_value(self, value, expression, connection):
        if value is None or value == '':
            return value
        return FieldEncryptionService.decrypt(value)

    def to_python(self, value):
        if value is None or value == '':
            return value
        return FieldEncryptionService.decrypt(value)
