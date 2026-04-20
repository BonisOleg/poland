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

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericStackedInline, GenericTabularInline
from django.contrib.contenttypes.models import ContentType
from django_ckeditor_5.widgets import CKEditor5Widget
from modeltranslation.admin import TranslationAdmin

from apps.blog.models import Article
from apps.core.labels import pl_uk
from apps.events.models import EventCity
from apps.pages.models import StaticPage

from .models import KIND_GALLERY, GalleryItem, PageBlock, RelatedItem


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


class RelatedItemForm(forms.ModelForm):
    """Friendly form for RelatedItem that replaces raw GFK fields with model-choice dropdowns.

    Instead of asking the admin to know the numeric ``target_object_id``, the form
    exposes one ModelChoiceField per allowed target type. ``clean()`` and ``save()``
    resolve the selection back to the ``target_content_type`` / ``target_object_id``
    GFK pair transparently. Existing rows are pre-filled from the GFK on init.
    """

    event_city_target = forms.ModelChoiceField(
        queryset=EventCity.objects.filter(is_published=True)
            .select_related("event", "city")
            .order_by("event__title", "city__name"),
        required=False,
        label=pl_uk("Wydarzenie w mieście", "Подія в місті"),
        help_text=pl_uk(
            "Wybierz, jeśli chcesz dodać konkretne Wydarzenie w mieście.",
            "Виберіть, якщо хочете додати конкретну Подію в місті.",
        ),
    )
    static_page_target = forms.ModelChoiceField(
        queryset=StaticPage.objects.all().order_by("title"),
        required=False,
        label=pl_uk("Strona statyczna", "Статична сторінка"),
        help_text=pl_uk(
            "Wybierz, jeśli chcesz powiązać stronę statyczną.",
            "Виберіть, якщо хочете пов'язати статичну сторінку.",
        ),
    )
    article_target = forms.ModelChoiceField(
        queryset=Article.objects.all().order_by("title"),
        required=False,
        label=pl_uk("Artykuł", "Стаття"),
        help_text=pl_uk(
            "Wybierz, jeśli chcesz powiązać artykuł z bloga.",
            "Виберіть, якщо хочете пов'язати статтю з блогу.",
        ),
    )

    class Meta:
        model = RelatedItem
        fields = ("target_content_type", "target_object_id", "sort_order")
        widgets = {
            "target_content_type": forms.HiddenInput(),
            "target_object_id": forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            try:
                target = self.instance.target
            except Exception:  # noqa: BLE001
                target = None
            if isinstance(target, EventCity):
                self.fields["event_city_target"].initial = target
            elif isinstance(target, StaticPage):
                self.fields["static_page_target"].initial = target
            elif isinstance(target, Article):
                self.fields["article_target"].initial = target

    def clean(self) -> dict:
        data = super().clean()
        target = (
            data.get("event_city_target")
            or data.get("static_page_target")
            or data.get("article_target")
        )
        if target is None and not self.instance.pk:
            raise forms.ValidationError(
                pl_uk("Wybierz cel powiązania.", "Виберіть ціль пов'язання.")
            )
        if target is not None:
            data["target_content_type"] = ContentType.objects.get_for_model(type(target))
            data["target_object_id"] = target.pk
        return data

    def save(self, commit: bool = True) -> RelatedItem:
        instance = super().save(commit=False)
        target = (
            self.cleaned_data.get("event_city_target")
            or self.cleaned_data.get("static_page_target")
            or self.cleaned_data.get("article_target")
        )
        if target is not None:
            instance.target_content_type = ContentType.objects.get_for_model(type(target))
            instance.target_object_id = target.pk
        if commit:
            instance.save()
        return instance


class RelatedItemInline(admin.TabularInline):
    model = RelatedItem
    form = RelatedItemForm
    extra = 1
    fields = ("event_city_target", "static_page_target", "article_target", "sort_order")
    verbose_name = pl_uk("Powiązana strona", "Пов'язана сторінка")
    verbose_name_plural = pl_uk("Powiązane strony", "Пов'язані сторінки")


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
    readonly_fields = ("gallery_items_count",)
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
        ("gallery_items_count",),
    )
    classes = ("cms-block-inline",)
    verbose_name = pl_uk("Blok strony (CMS)", "Блок сторінки (CMS)")
    verbose_name_plural = pl_uk(
        "Bloki strony (CMS — konstruktor)",
        "Блоки sторінки (CMS — конструктор)",
    )

    class Media:
        css = {"all": ("admin/cms/cms-blocks.css",)}
        js = ("admin/cms/cms-block-kind.js",)

    def gallery_items_count(self, obj: PageBlock) -> str:
        if not obj.pk or obj.kind != KIND_GALLERY:
            return pl_uk(
                "Zapisz blok typu 'Galeria', potem kliknij 'Zmień →' aby dodać zdjęcia.",
                "Збережіть блок типу 'Галерея', потім натисніть 'Змінити →' для додавання фото.",
            )
        count = obj.gallery_items.count()
        if count == 0:
            return pl_uk(
                "Brak zdjęć. Kliknij 'Zmień →' aby dodać zdjęcia do galerii.",
                "Фото відсутні. Натисніть 'Змінити →' щоб додати фото до галереї.",
            )
        return pl_uk(
            f"Zdjęć w galerii: {count}. Kliknij 'Zmień →' aby edytować.",
            f"Фото в галереї: {count}. Натисніть 'Змінити →' для редагування.",
        )
    gallery_items_count.short_description = pl_uk("Zdjęcia galerii", "Фото галереї")

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        return _apply_ckeditor(formset, "body")
