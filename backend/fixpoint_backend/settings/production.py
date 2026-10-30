from .base import *

DEBUG = False

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
