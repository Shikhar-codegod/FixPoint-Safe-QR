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
