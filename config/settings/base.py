from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-*x!#5&7k2cqa_b&+er7g77jn(a_xkbw3p7j-31f7582t!gy+ck",
)

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
    "django_htmx",
    "imagekit",
    "django_ckeditor_5",
    "apps.core",
    "apps.events",
    "apps.blog",
    "apps.reviews",
    "apps.pages",
    "apps.vouchers",
    "apps.seo",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "apps.seo.middleware.LegacyRedirectMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "apps.core.context_processors.global_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pl"
LANGUAGES = [
    ("pl", "Polski"),
    ("en", "English"),
]
MODELTRANSLATION_DEFAULT_LANGUAGE = "pl"
MODELTRANSLATION_LANGUAGES = ("pl", "en")

TIME_ZONE = "Europe/Warsaw"
USE_I18N = True
USE_L10N = True
USE_TZ = True

LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SITE_URL = os.environ.get("SITE_URL", "https://hypeglobal.pro")
SITE_NAME = "Hype Global Production"
# Bump after CSS changes so browsers skip cached stylesheets (also run collectstatic on deploy).
STATIC_ASSET_VERSION = os.environ.get("STATIC_ASSET_VERSION", "46")

# PayU REST API 2.1 credentials (set in env; defaults point to sandbox)
PAYU_POS_ID = os.environ.get("PAYU_POS_ID", "")
PAYU_MD5_KEY = os.environ.get("PAYU_MD5_KEY", "")    # IPN signature verification
PAYU_MD5_KEY2 = os.environ.get("PAYU_MD5_KEY2", "")  # OAuth2 client_secret
PAYU_BASE_URL = os.environ.get("PAYU_BASE_URL", "https://secure.snd.payu.com")  # sandbox

CKEDITOR_5_CONFIGS = {
    "default": {
        "extraPlugins": ["Highlight", "FontSize", "SourceEditing"],
        "toolbar": {
            "items": [
                "heading", "|",
                "bold", "italic", "underline", "|",
                "fontSize", "highlight", "|",
                "link", "bulletedList", "numberedList", "|",
                "blockQuote", "insertImage", "|",
                "sourceEditing", "|",
                "undo", "redo",
            ],
        },
        "fontSize": {
            "options": [10, 12, 14, "default", 18, 20, 24],
            "supportAllValues": False,
        },
        "highlight": {
            "options": [
                {
                    "model": "yellowMarker",
                    "class": "marker-yellow",
                    "title": "Yellow",
                    "color": "var(--ck-highlight-marker-yellow)",
                    "type": "marker",
                },
                {
                    "model": "greenMarker",
                    "class": "marker-green",
                    "title": "Green",
                    "color": "var(--ck-highlight-marker-green)",
                    "type": "marker",
                },
                {
                    "model": "pinkMarker",
                    "class": "marker-pink",
                    "title": "Pink",
                    "color": "var(--ck-highlight-marker-pink)",
                    "type": "marker",
                },
                {
                    "model": "blueMarker",
                    "class": "marker-blue",
                    "title": "Blue",
                    "color": "var(--ck-highlight-marker-blue)",
                    "type": "marker",
                },
            ],
        },
        "height": "400px",
        "image": {
            "toolbar": ["imageTextAlternative", "imageStyle:inline", "imageStyle:block"],
        },
    },
}
CKEDITOR_5_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"
