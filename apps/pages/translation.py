from modeltranslation.translator import register, TranslationOptions
from .models import PageMedia, StaticPage


@register(StaticPage)
class StaticPageTO(TranslationOptions):
    fields = ("title", "content", "seo_title", "seo_description", "keywords")


@register(PageMedia)
class PageMediaTO(TranslationOptions):
    fields = ("caption",)
