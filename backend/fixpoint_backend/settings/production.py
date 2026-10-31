from cryptography.fernet import Fernet
from django.core.exceptions import ImproperlyConfigured
from .base import *

DEBUG = False

# Production requires FIELD_ENCRYPTION_KEY to be explicitly configured and valid
field_encryption_key = env('FIELD_ENCRYPTION_KEY', default='')
if not field_encryption_key:
    raise ImproperlyConfigured(
        "FIELD_ENCRYPTION_KEY environment variable is required in production."
    )

try:
    key_bytes = (
        field_encryption_key.encode('utf-8')
        if isinstance(field_encryption_key, str)
        else field_encryption_key
    )
    Fernet(key_bytes)
except Exception:
    raise ImproperlyConfigured(
        "FIELD_ENCRYPTION_KEY is invalid. It must be a 32 url-safe base64-encoded string."
    )


# Production requires PostgreSQL configured via DATABASE_URL
DATABASES = {
    'default': env.db('DATABASE_URL')
}

# Strict CORS
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS')

# Strict Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=True)
CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=True)
SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# JSON-only renderer in production
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
)
