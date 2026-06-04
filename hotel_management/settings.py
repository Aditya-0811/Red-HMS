"""
╔══════════════════════════════════════════════════════════╗
║          Red HMS – Django Settings                       ║
║          Hotel Management System – Final Year Project    ║
╚══════════════════════════════════════════════════════════╝
"""
from pathlib import Path
import os

# Load environment variables from .env file
try:
    from environs import Env
    env = Env()
    env.read_env()
    USE_ENV = True
except ImportError:
    USE_ENV = False

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── SECURITY ─────────────────────────────────────────────
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-red-hms-change-this-before-production-2024-xyz!'
)
DEBUG        = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

# ─── APPLICATIONS ─────────────────────────────────────────
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Red HMS
    'accounts',
    'rooms',
    'guests',
    'billing',
    'reports',
    # Third-party
    'import_export',
    'crispy_forms',
    'crispy_bootstrap5',
    'mathfilters',
    'taggit',
    'django_ckeditor_5',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'hotel_management.middleware.AdminAuthMiddleware',
]

ROOT_URLCONF = 'hotel_management.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.global_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'hotel_management.wsgi.application'
AUTH_USER_MODEL  = 'accounts.User'

# ─── DATABASE ─────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ─── PASSWORD VALIDATION ──────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── INTERNATIONALISATION ─────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True

# ─── STATIC & MEDIA ───────────────────────────────────────
STATIC_URL       = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT      = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL        = '/media/'
MEDIA_ROOT       = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── AUTH REDIRECTS ───────────────────────────────────────
LOGIN_URL           = '/accounts/login/'
LOGIN_REDIRECT_URL  = '/reports/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# ─── SESSION ──────────────────────────────────────────────
SESSION_COOKIE_AGE         = 86400 * 7
SESSION_SAVE_EVERY_REQUEST = True

# ─── MESSAGES → SweetAlert2 ───────────────────────────────
from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {
    message_constants.DEBUG:   'info',
    message_constants.INFO:    'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR:   'error',
}

# ─── EMAIL ────────────────────────────────────────────────
EMAIL_BACKEND      = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'Red HMS <noreply@redhms.com>')

# ─── CRISPY FORMS ─────────────────────────────────────────
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK          = 'bootstrap5'

# ─── FILE UPLOADS ─────────────────────────────────────────
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024

# ═══════════════════════════════════════════════════════════
# PAYMENT GATEWAYS
# ═══════════════════════════════════════════════════════════

# ── Stripe ────────────────────────────────────────────────
# Get keys at: https://dashboard.stripe.com/test/apikeys
# Add to your .env file, then never commit .env to git
STRIPE_PUBLIC_KEY  = os.environ.get('STRIPE_PUBLIC_KEY',  'pk_test_your_stripe_publishable_key_here')
STRIPE_SECRET_KEY  = os.environ.get('STRIPE_SECRET_KEY',  'sk_test_your_stripe_secret_key_here')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# ── PayPal ────────────────────────────────────────────────
# Get client ID at: https://developer.paypal.com/
# Use sandbox credentials for testing
PAYPAL_CLIENT_ID   = os.environ.get('PAYPAL_CLIENT_ID', 'sb')  # 'sb' = PayPal sandbox

# ── Website URL (used for payment redirect URLs) ──────────
WEBSITE_ADDRESS    = os.environ.get('WEBSITE_ADDRESS', 'http://127.0.0.1:8000')

# ─── JAZZMIN ──────────────────────────────────────────────
JAZZMIN_SETTINGS = {
    "site_title"   : "Red HMS Admin",
    "site_header"  : "Red HMS",
    "site_brand"   : "🏨 Red HMS",
    "welcome_sign" : "Welcome to Red Hotel Management System",
    "copyright"    : "Red HMS © 2024 — Final Year Project",
    "search_model" : ["accounts.User", "guests.Reservation", "rooms.Hotel"],
    "topmenu_links": [
        {"name": "Home",      "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "View Site", "url": "/",            "new_window": True},
        {"name": "Dashboard", "url": "/reports/dashboard/"},
    ],
    "order_with_respect_to": ["accounts", "rooms", "guests", "billing", "reports"],
    "icons": {
        "accounts.User"        : "fas fa-user",
        "accounts.Profile"     : "fas fa-id-card",
        "accounts.Notification": "fas fa-bell",
        "rooms.Hotel"          : "fas fa-hotel",
        "rooms.Room"           : "fas fa-bed",
        "rooms.RoomType"       : "fas fa-th-large",
        "rooms.Review"         : "fas fa-star",
        "guests.Reservation"   : "fas fa-calendar-check",
        "guests.Coupon"        : "fas fa-tag",
        "guests.Bookmark"      : "fas fa-heart",
        "guests.ActivityLog"   : "fas fa-clipboard-list",
        "billing.Invoice"      : "fas fa-file-invoice-dollar",
        "billing.Payment"      : "fas fa-credit-card",
        "billing.RoomService"  : "fas fa-concierge-bell",
        "reports.Report"       : "fas fa-chart-bar",
    },
    "default_icon_parents"  : "fas fa-chevron-circle-right",
    "default_icon_children" : "fas fa-circle",
    "related_modal_active"  : True,
    "changeform_format"     : "horizontal_tabs",
    "show_ui_builder"       : False,
}

JAZZMIN_UI_TWEAKS = {
    "brand_colour"             : "navbar-danger",
    "accent"                   : "accent-danger",
    "navbar"                   : "navbar-dark",
    "navbar_fixed"             : True,
    "sidebar"                  : "sidebar-dark-danger",
    "sidebar_fixed"            : True,
    "sidebar_nav_compact_style": True,
    "theme"                    : "default",
    "button_classes": {
        "primary"  : "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info"     : "btn-info",
        "warning"  : "btn-warning",
        "danger"   : "btn-danger",
        "success"  : "btn-outline-success",
    },
}

# ─── CKEDITOR 5 ───────────────────────────────────────────
CKEDITOR_5_UPLOAD_PATH = 'uploads/'
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': ['heading','|','bold','italic','link','|',
                    'bulletedList','numberedList','|','blockQuote','imageUpload'],
    },
    'extends': {
        'toolbar': {
            'items': ['heading','|','bold','italic','underline','strikethrough','|',
                      'link','bulletedList','numberedList','|','outdent','indent','|',
                      'blockQuote','insertImage','insertTable','|',
                      'fontSize','fontColor','fontBackgroundColor','|',
                      'removeFormat','sourceEditing'],
            'shouldNotGroupWhenFull': True,
        },
        'image': {
            'toolbar': ['imageTextAlternative','|','imageStyle:alignLeft',
                        'imageStyle:alignRight','imageStyle:alignCenter',
                        'imageStyle:side','|','toggleImageCaption'],
            'styles': ['full','side','alignLeft','alignRight','alignCenter'],
        },
        'table': {
            'contentToolbar': ['tableColumn','tableRow','mergeTableCells',
                               'tableProperties','tableCellProperties'],
        },
    },
}

# ─── SECURITY HEADERS ─────────────────────────────────────
SECURE_BROWSER_XSS_FILTER   = True
X_FRAME_OPTIONS              = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF  = True
SESSION_COOKIE_HTTPONLY      = True

# ─── LOGGING ──────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'WARNING'},
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}
