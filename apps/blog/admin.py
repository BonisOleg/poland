from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import Article


@admin.register(Article)
class ArticleAdmin(TranslationAdmin):
    list_display = ("title", "is_published", "published_at")
    list_filter = ("is_published",)
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_published",)
