from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("feeds/", include("apps.events.feed_urls")),
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

# User uploads (voucher images, etc.): stable /media/… URLs for SEO; avoid hashed static names.
# On high traffic, move to S3 and set MEDIA_URL; keep same path suffixes to preserve rankings.
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
