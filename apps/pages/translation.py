from modeltranslation.translator import register, TranslationOptions
from .models import StaticPage


@register(StaticPage)
class StaticPageTO(TranslationOptions):
    fields = ("title", "content", "seo_title", "seo_description", "keywords")
