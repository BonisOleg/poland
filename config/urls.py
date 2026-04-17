from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("feeds/", include("apps.events.feed_urls")),
]

# 1) django.conf.urls.static.static() is a no-op when DEBUG=False (Django 5+), so never use it for prod media.
# 2) Must be before `<slug:slug>/` — "media" is a valid slug and would steal /media/vouchers/…
_media = settings.MEDIA_URL.strip("/")
urlpatterns += [
    re_path(
        rf"^{_media}/(?P<path>.*)$",
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]

urlpatterns += i18n_patterns(
    path("", include("apps.core.urls")),
    path("wydarzenia/", include("apps.events.urls")),
    path("aktualnosci/", include("apps.blog.urls")),
    path("reviews/", include("apps.reviews.urls")),
    path("platnosci/", include("apps.vouchers.urls")),
    path("<slug:slug>/", include("apps.pages.catch_urls")),
    prefix_default_language=False,
)

urlpatterns += [
    path("", include("apps.seo.urls")),
]
