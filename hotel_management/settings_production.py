"""
Red HMS – Production Settings
==============================
This file extends settings.py for Railway / Render / Heroku deployment.
Set the environment variable:
   DJANGO_SETTINGS_MODULE=hotel_management.settings_production
"""

from .settings import *
import os
import dj_database_url

# ── Security ──────────────────────────────────────────────
DEBUG = False

SECRET_KEY = os.environ['SECRET_KEY']   # Must be set in host env vars

ALLOWED_HOSTS = ['*']

# Railway provides RAILWAY_PUBLIC_DOMAIN; also cover .up.railway.app wildcard
_railway_domain = os.environ.get('RAILWAY_PUBLIC_DOMAIN', '')
_render_host    = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')

CSRF_TRUSTED_ORIGINS = [
    'https://*.up.railway.app',
    'https://*.railway.app',
]
if _railway_domain:
    CSRF_TRUSTED_ORIGINS.append(f'https://{_railway_domain}')
if _render_host:
    CSRF_TRUSTED_ORIGINS.append(f'https://{_render_host}')

# ── Database (auto-configured from DATABASE_URL env var) ──
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }

# ── Static files (WhiteNoise serves them directly) ────────
MIDDLEWARE = ['whitenoise.middleware.WhiteNoiseMiddleware'] + MIDDLEWARE

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# ── Media files (use AWS S3 in production) ────────────────
# Option A: Store media on S3 (recommended for production)
AWS_ACCESS_KEY_ID     = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME', '')

if AWS_STORAGE_BUCKET_NAME:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'

# Option B: No S3 — uploaded files stored on server disk
# (works on Render but files lost on each deploy — not recommended for production)

# ── Security headers ──────────────────────────────────────
# Railway terminates SSL at the proxy — don't redirect again or you get a loop
SECURE_SSL_REDIRECT             = False
SECURE_PROXY_SSL_HEADER         = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS             = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS  = True
SECURE_HSTS_PRELOAD             = True
SESSION_COOKIE_SECURE           = True
CSRF_COOKIE_SECURE              = True
SECURE_CONTENT_TYPE_NOSNIFF     = True
X_FRAME_OPTIONS                 = 'DENY'

# ── Email (use real SMTP in production) ───────────────────
EMAIL_BACKEND    = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST       = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT       = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS    = True
EMAIL_HOST_USER  = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = os.environ.get('DEFAULT_FROM_EMAIL', 'Red HMS <noreply@redhms.com>')

# ── Logging ───────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{levelname} {asctime} {module} {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
}
