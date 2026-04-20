"""Admin for the unified CMS page builder.

Strategy
--------
- ``PageBlockInline`` is a GenericStackedInline used on owner admins
  (StaticPage / Article / EventCity). Only the most-used fields are visible
  inline — ``show_change_link=True`` opens the full block editor with nested
  gallery / related-item rows.
- ``PageBlockAdmin`` is the dedicated change form with TabularInlines for
  :class:`GalleryItem` and :class:`RelatedItem`.

CKEditor is wired to all translated ``body_*`` fields via the existing
``_apply_ckeditor`` pattern from the codebase.

We deliberately keep the inline visible regardless of the owner's
``use_block_builder`` flag — admins must be able to populate blocks first
and then flip the switch.
"""

from __future__ import annotations

from django.conf import settings
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline, GenericTabularInline
from django_ckeditor_5.widgets import CKEditor5Widget
from modeltranslation.admin import TranslationAdmin

from apps.core.labels import pl_uk

from .models import GalleryItem, PageBlock, RelatedItem


_LANGS = [lang for lang, _ in settings.LANGUAGES]


def _apply_ckeditor(form_or_formset, *base_field_names: str):
    """Apply CKEditor5Widget to translated variants of given base fields.

    Accepts either a Form class or a Formset class (uses ``.form`` attribute
    for the latter).
    """
    base_fields = getattr(form_or_formset, "base_fields", None)
    if base_fields is None and hasattr(form_or_formset, "form"):
        base_fields = form_or_formset.form.base_fields
    if base_fields is None:
        return form_or_formset
    for base in base_field_names:
        for lang in _LANGS:
            field_name = f"{base}_{lang}"
            if field_name in base_fields:
                base_fields[field_name].widget = CKEditor5Widget(config_name="default")
        if base in base_fields:
            base_fields[base].widget = CKEditor5Widget(config_name="default")
    return form_or_formset


# ── Inlines on PageBlock change form ──────────────────────────────────────

class GalleryItemInline(admin.TabularInline):
    model = GalleryItem
    extra = 1
    fields = ("image", "image_url", "alt_text", "sort_order")
    verbose_name = pl_uk("Element galerii", "Елемент галереї")
    verbose_name_plural = pl_uk(
        "Elementy galerii (dodaj wiele dla galerii)",
        "Елементи галереї (додайте кілька для галереї)",
    )


class RelatedItemInline(admin.TabularInline):
    model = RelatedItem
    extra = 1
    fields = ("target_content_type", "target_object_id", "sort_order")
    verbose_name = pl_uk("Powiązana strona", "Пов’язана сторінка")
    verbose_name_plural = pl_uk("Powiązane strony", "Пов’язані сторінки")


# ── Standalone PageBlock admin ────────────────────────────────────────────

@admin.register(PageBlock)
class PageBlockAdmin(TranslationAdmin):
    list_display = ("kind", "heading", "owner_link", "sort_order", "is_visible")
    list_filter = ("kind", "is_visible", "content_type")
    search_fields = ("heading", "body", "button_text", "css_anchor")
    list_editable = ("sort_order", "is_visible")
    inlines = [GalleryItemInline, RelatedItemInline]
    raw_id_fields = ("content_type",)

    fieldsets = (
        (pl_uk("Właściciel i widoczność", "Власник і видимість"), {
            "fields": ("content_type", "object_id", "kind", "sort_order", "is_visible", "css_anchor"),
        }),
        (pl_uk("Tekst / Nagłówek", "Текст / Заголовок"), {
            "fields": ("heading", "heading_level", "body"),
            "classes": ("collapse",),
        }),
        (pl_uk("Obraz / Banner", "Зображення / Банер"), {
            "fields": ("image", "image_alt"),
            "classes": ("collapse",),
        }),
        (pl_uk("Wideo", "Відео"), {
            "fields": ("video_embed_url", "video_file"),
            "classes": ("collapse",),
        }),
        (pl_uk("Przycisk / CTA", "Кнопка / CTA"), {
            "fields": ("button_text", "button_url", "button_style"),
            "classes": ("collapse",),
        }),
        (pl_uk("Timer odliczania", "Таймер відліку"), {
            "fields": ("countdown_target", "countdown_label"),
            "classes": ("collapse",),
        }),
        (pl_uk("Formularz", "Форма"), {
            "fields": ("form_kind",),
            "classes": ("collapse",),
        }),
        (pl_uk("Opinie", "Відгуки"), {
            "fields": ("reviews_limit",),
            "classes": ("collapse",),
        }),
        (pl_uk("Zobacz także", "Дивіться також"), {
            "fields": ("related_strategy", "related_limit"),
            "classes": ("collapse",),
        }),
    )

    def owner_link(self, obj):
        try:
            return str(obj.owner) if obj.owner else "—"
        except Exception:  # noqa: BLE001
            return "—"
    owner_link.short_description = pl_uk("Strona właściciela", "Сторінка-власник")

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return _apply_ckeditor(form, "body")


# ── Generic inline for owners ─────────────────────────────────────────────

_INLINE_LANG_FIELDS = (
    tuple(f"heading_{lang}" for lang in _LANGS)
    + ("heading_level",)
    + tuple(f"body_{lang}" for lang in _LANGS)
)


class PageBlockInline(GenericStackedInline):
    """Inline for PageBlock attached generically to an owner."""

    model = PageBlock
    ct_field = "content_type"
    ct_fk_field = "object_id"
    extra = 0
    show_change_link = True
    fields = (
        ("kind", "sort_order", "is_visible"),
        ("css_anchor",),
    ) + _INLINE_LANG_FIELDS + (
        ("image", "image_alt"),
        ("video_embed_url", "video_file"),
        ("button_text", "button_url", "button_style"),
        ("countdown_target", "countdown_label"),
        ("form_kind",),
        ("reviews_limit",),
        ("related_strategy", "related_limit"),
    )
    classes = ("cms-block-inline",)
    verbose_name = pl_uk("Blok strony (CMS)", "Блок сторінки (CMS)")
    verbose_name_plural = pl_uk(
        "Bloki strony (CMS — konstruktor)",
        "Блоки сторінки (CMS — конструктор)",
    )

    class Media:
        css = {"all": ("admin/cms/cms-blocks.css",)}

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        return _apply_ckeditor(formset, "body")
