from .base import *

DEBUG = True

# Database: PostgreSQL if DATABASE_URL is configured, SQLite fallback for local test/dev
database_url = env('DATABASE_URL', default='')
if database_url:
    DATABASES = {
        'default': env.db('DATABASE_URL')
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Enable BrowsableAPIRenderer in development for testing convenience
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = (
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
)

CORS_ALLOW_ALL_ORIGINS = True

# Celery fallback for local development / testing without Redis running
CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER', default=True)
CELERY_TASK_EAGER_PROPAGATES = True

# Validate FIELD_ENCRYPTION_KEY format if provided in development
field_encryption_key = env('FIELD_ENCRYPTION_KEY', default='')
if field_encryption_key:
    try:
        from cryptography.fernet import Fernet
        key_bytes = field_encryption_key.encode('utf-8') if isinstance(field_encryption_key, str) else field_encryption_key
        Fernet(key_bytes)
    except Exception:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured(
            "FIELD_ENCRYPTION_KEY is invalid. It must be a 32 url-safe base64-encoded string."
        )
