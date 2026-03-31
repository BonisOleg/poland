from django.contrib.sitemaps import Sitemap
from apps.events.models import EventCity
from apps.pages.models import StaticPage
from apps.blog.models import Article


class EventCitySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return EventCity.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class StaticPageSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5

    def items(self):
        return StaticPage.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()


class ArticleSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Article.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()
