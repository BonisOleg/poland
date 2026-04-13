from django.conf import settings


def global_context(request):
    return {
        "SITE_NAME": getattr(settings, "SITE_NAME", "Hype Global Production"),
        "SITE_URL": getattr(settings, "SITE_URL", "https://hypeglobal.pro"),
        "STATIC_ASSET_VERSION": getattr(settings, "STATIC_ASSET_VERSION", "1"),
    }
