from django.contrib import admin
from django.conf import settings
from modeltranslation.admin import TranslationAdmin, TranslationStackedInline
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import PageMedia, StaticPage

_LANGS = [lang for lang, _ in settings.LANGUAGES]


class PageMediaInline(TranslationStackedInline):
    model = PageMedia
    extra = 1
    fields = ("kind", "image", "video_file", "video_embed_url", "caption", "sort_order")


def _apply_ckeditor(form, *base_field_names):
    for base in base_field_names:
        for lang in _LANGS:
            field_name = f"{base}_{lang}"
            if field_name in form.base_fields:
                form.base_fields[field_name].widget = CKEditor5Widget(config_name="default")
    return form


@admin.register(StaticPage)
class StaticPageAdmin(TranslationAdmin):
    inlines = [PageMediaInline]

    list_display = ("title", "slug", "page_type", "layout_version", "is_published", "show_contact_form", "sort_order")
    list_filter = ("page_type", "is_published")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_published",)
    fieldsets = (
        ("Основне", {
            "fields": ("title", "slug", "page_type", "layout_version", "sort_order", "is_published", "show_contact_form"),
        }),
        ("Контент", {
            "fields": ("content",),
        }),
        ("SEO", {
            "fields": ("seo_title", "seo_description", "keywords"),
            "classes": ("collapse",),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return _apply_ckeditor(form, "content")
