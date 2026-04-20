from django.contrib import admin
from django.conf import settings
from modeltranslation.admin import TranslationAdmin
from django_ckeditor_5.widgets import CKEditor5Widget

from apps.cms.admin import PageBlockInline
from apps.core.labels import pl_uk
from .models import Article

_LANGS = [lang for lang, _ in settings.LANGUAGES]


def _apply_ckeditor(form, *base_field_names):
    for base in base_field_names:
        for lang in _LANGS:
            field_name = f"{base}_{lang}"
            if field_name in form.base_fields:
                form.base_fields[field_name].widget = CKEditor5Widget(config_name="default")
    return form


@admin.register(Article)
class ArticleAdmin(TranslationAdmin):
    inlines = [PageBlockInline]
    list_display = ("title", "is_published", "use_block_builder", "published_at")
    list_filter = ("is_published", "use_block_builder")
    search_fields = ("title", "content")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_published", "use_block_builder")
    fieldsets = (
        (pl_uk("Podstawowe", "Основне"), {
            "fields": ("title", "slug", "is_published", "published_at", "use_block_builder"),
        }),
        (pl_uk("Treść (legacy HTML)", "Контент (legacy HTML)"), {
            "fields": ("excerpt", "content", "image"),
            "description": pl_uk(
                "Używane gdy 'Konstruktor bloków (CMS)' jest WYŁĄCZONY.",
                "Використовується, коли «Блок-конструктор (CMS)» ВИМКНЕНО.",
            ),
        }),
        ("SEO", {
            "fields": (
                "seo_title", "seo_description", "keywords",
                "og_image", "canonical_url", "robots_directives",
            ),
            "classes": ("collapse",),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return _apply_ckeditor(form, "content")
