from django.contrib.sitemaps.views import sitemap
from django.urls import path
from .sitemaps import EventCitySitemap, StaticPageSitemap, ArticleSitemap

sitemaps = {
    "events": EventCitySitemap,
    "pages": StaticPageSitemap,
    "articles": ArticleSitemap,
}

urlpatterns = [
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", lambda r: __import__("django.http", fromlist=["HttpResponse"]).HttpResponse(
        "User-agent: *\nAllow: /\nSitemap: https://hypeglobal.pro/sitemap.xml\n",
        content_type="text/plain",
    ), name="robots"),
]
