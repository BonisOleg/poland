from modeltranslation.translator import register, TranslationOptions
from .models import Article


@register(Article)
class ArticleTO(TranslationOptions):
    fields = ("title", "excerpt", "content", "seo_title", "seo_description", "keywords")
