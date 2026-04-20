from django.contrib import admin
from django.conf import settings
from modeltranslation.admin import TranslationAdmin, TranslationStackedInline
from django_ckeditor_5.widgets import CKEditor5Widget

from apps.cms.admin import PageBlockInline
from apps.core.labels import pl_uk
from .models import GroupInquiry, PageMedia, StaticPage

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


@admin.register(GroupInquiry)
class GroupInquiryAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "intent",
        "email",
        "name",
        "company",
        "handled",
    )
    list_filter = ("intent", "handled", "created_at")
    search_fields = ("email", "name", "company", "message")
    readonly_fields = (
        "intent",
        "name",
        "email",
        "phone",
        "company",
        "nip",
        "ticket_count",
        "message",
        "source_page",
        "created_at",
    )
    fieldsets = (
        (
            pl_uk("Zgłoszenie", "Заявка"),
            {
                "fields": (
                    "created_at",
                    "intent",
                    "source_page",
                    "name",
                    "email",
                    "phone",
                    "company",
                    "nip",
                    "ticket_count",
                    "message",
                ),
            },
        ),
        (
            pl_uk("Obsługa", "Обробка"),
            {
                "fields": ("handled", "staff_notes"),
            },
        ),
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(StaticPage)
class StaticPageAdmin(TranslationAdmin):
    inlines = [PageBlockInline, PageMediaInline]

    list_display = (
        "title", "slug", "page_type", "layout_version", "use_block_builder",
        "is_published", "show_contact_form", "sort_order",
    )
    list_filter = ("page_type", "is_published", "use_block_builder")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_published", "use_block_builder")
    fieldsets = (
        (pl_uk("Podstawowe", "Основне"), {
            "fields": (
                "title", "slug", "page_type", "layout_version",
                "sort_order", "is_published", "show_contact_form",
                "use_block_builder",
            ),
        }),
        (pl_uk("Treść (legacy HTML)", "Контент (legacy HTML)"), {
            "fields": ("content",),
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
