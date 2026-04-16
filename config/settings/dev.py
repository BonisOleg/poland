from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Без manifest — локально не потрібен `collectstatic`; уникнення 500 на {% static %} при DEBUG=True.
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
