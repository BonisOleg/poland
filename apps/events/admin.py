from django.contrib import admin
from django.conf import settings
from modeltranslation.admin import TranslationAdmin
from django_ckeditor_5.widgets import CKEditor5Widget

from apps.cms.admin import PageBlockInline
from apps.core.labels import pl_uk
from .models import Category, AgeGroup, City, Venue, Event, EventCity, EventImage, EventVideo, EventContentBlock

_LANGS = [lang for lang, _ in settings.LANGUAGES]
_EVENT_CONTENT_BLOCK_TRANSLATED = ("title", "body", "button_text")
_EVENT_CONTENT_BLOCK_INLINE_FIELDS = (
    ("sort_order",)
    + tuple(f"{base}_{lang}" for base in _EVENT_CONTENT_BLOCK_TRANSLATED for lang in _LANGS)
    + ("button_url",)
)


def _apply_ckeditor(form, *base_field_names):
    """Apply CKEditor5Widget to translated variants of given base field names."""
    for base in base_field_names:
        for lang in _LANGS:
            field_name = f"{base}_{lang}"
            if field_name in form.base_fields:
                form.base_fields[field_name].widget = CKEditor5Widget(config_name="default")
    return form


class EventImageInline(admin.TabularInline):
    model = EventImage
    extra = 3
    fields = ("image", "image_url", "alt_text", "sort_order")
    verbose_name = pl_uk("Zdjęcie galerii", "Фото галереї")
    verbose_name_plural = pl_uk(
        "Galeria zdjęć (dodaj wiele — pojawi się na stronie)",
        "Галерея фото (додайте кілька — з’явиться на сайті)",
    )


class EventVideoInline(admin.TabularInline):
    model = EventVideo
    extra = 1
    fields = ("embed_url", "video_file", "title", "sort_order")


class EventContentBlockInline(admin.StackedInline):
    model = EventContentBlock
    extra = 0
    fields = _EVENT_CONTENT_BLOCK_INLINE_FIELDS

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        for lang in _LANGS:
            field = f"body_{lang}"
            if field in formset.form.base_fields:
                formset.form.base_fields[field].widget = CKEditor5Widget(config_name="default")
        return formset


@admin.register(Category)
class CategoryAdmin(TranslationAdmin):
    list_display = ("name", "slug", "sort_order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(AgeGroup)
class AgeGroupAdmin(TranslationAdmin):
    list_display = ("name", "min_age", "max_age")


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "region")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "address")
    list_filter = ("city",)
    search_fields = ("name", "address")


@admin.register(Event)
class EventAdmin(TranslationAdmin):
    list_display = ("title", "event_type", "language_spoken", "is_active", "sort_order")
    list_filter = ("event_type", "is_active", "categories", "language_spoken")
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("categories",)
    list_editable = ("sort_order", "is_active")
    fieldsets = (
        (pl_uk("Podstawowe", "Основне"), {
            "fields": ("title", "slug", "event_type", "is_active", "sort_order"),
        }),
        (pl_uk("Opis", "Опис"), {
            "fields": ("description", "short_description"),
        }),
        (pl_uk("Szczegóły", "Деталі"), {
            "fields": ("target_audience", "duration", "language_spoken"),
        }),
        (pl_uk("Kategorie i grupa docelowa", "Категорії та аудиторія"), {
            "fields": ("categories", "age_group"),
        }),
        (pl_uk("Obraz", "Зображення"), {
            "fields": ("image", "hero_image_focal"),
        }),
        (pl_uk("Bilety", "Квитки"), {
            "fields": ("biletyna_base_url",),
            "classes": ("collapse",),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return _apply_ckeditor(form, "description")


@admin.register(EventCity)
class EventCityAdmin(TranslationAdmin):
    list_display = (
        "event", "city", "event_date", "ticket_status",
        "is_published", "is_archived", "archive_date", "use_block_builder", "slug",
    )
    list_filter = ("is_published", "is_archived", "ticket_status", "city", "event__event_type", "use_block_builder")
    search_fields = ("slug", "event__title", "city__name", "seo_title")
    raw_id_fields = ("event", "city", "venue")
    inlines = [PageBlockInline]
    list_editable = ("ticket_status", "is_published", "is_archived", "use_block_builder")
    filter_horizontal = ("related_events_manual",)
    readonly_fields = ("archive_date",)
    actions = ["archive_selected_events", "unarchive_selected_events"]
    fieldsets = (
        (pl_uk("Podstawowe", "Основне"), {
            "fields": (
                "event", "city", "venue", "slug", "custom_title",
                "is_published", "use_block_builder",
            ),
        }),
        (pl_uk("Data i bilety", "Дата і квитки"), {
            "fields": (
                "event_date", "sale_end_date",
                "biletyna_url", "ticket_status", "seats_left",
                "price_from", "price_to",
            ),
        }),
        (pl_uk("Archiwizacja", "Архівація"), {
            "fields": ("is_archived", "archive_date"),
            "classes": ("collapse",),
        }),
        ("SEO", {
            "fields": ("seo_title", "seo_description", "keywords", "og_image", "canonical_url"),
            "classes": ("collapse",),
        }),
        (pl_uk("Treść", "Контент"), {
            "fields": ("content_html",),
            "classes": ("collapse",),
        }),
        (pl_uk("Powiązane wydarzenia (ręcznie)", "Пов’язані події (вручну)"), {
            "fields": ("related_events_manual",),
            "classes": ("collapse",),
        }),
    )

    def archive_selected_events(self, request, queryset):
        """Admin action to archive selected events."""
        from django.utils import timezone as tz
        now = tz.now()
        for event_city in queryset:
            event_city.is_archived = True
            event_city.archive_date = now
            event_city.save(update_fields=["is_archived", "archive_date"])
        self.message_user(request, f"{queryset.count()} event(s) archived")

    archive_selected_events.short_description = pl_uk(
        "Archiwizuj wybrane wydarzenia",
        "Archivuj vybrani podii"
    )

    def unarchive_selected_events(self, request, queryset):
        """Admin action to unarchive selected events."""
        for event_city in queryset:
            event_city.is_archived = False
            event_city.archive_date = None
            event_city.save(update_fields=["is_archived", "archive_date"])
        self.message_user(request, f"{queryset.count()} event(s) unarchived")

    unarchive_selected_events.short_description = pl_uk(
        "Przywroc wybrane wydarzenia",
        "Vidnovyty vybrani podii"
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return _apply_ckeditor(form, "content_html")
