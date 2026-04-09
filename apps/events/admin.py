from django.contrib import admin
from django.conf import settings
from modeltranslation.admin import TranslationAdmin
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import Category, AgeGroup, City, Venue, Event, EventCity, EventImage

_LANGS = [lang for lang, _ in settings.LANGUAGES]


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
    extra = 1


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
        ("Основне", {
            "fields": ("title", "slug", "event_type", "is_active", "sort_order"),
        }),
        ("Опис", {
            "fields": ("description", "short_description"),
        }),
        ("Деталі", {
            "fields": ("target_audience", "duration", "language_spoken"),
        }),
        ("Категорії та аудиторія", {
            "fields": ("categories", "age_group"),
        }),
        ("Зображення", {
            "fields": ("image",),
        }),
        ("Квитки", {
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
        "event", "city", "event_date", "ticket_status", "is_published", "slug"
    )
    list_filter = ("is_published", "ticket_status", "city", "event__event_type")
    search_fields = ("slug", "event__title", "city__name", "seo_title")
    raw_id_fields = ("event", "city", "venue")
    inlines = [EventImageInline]
    list_editable = ("ticket_status", "is_published")
    filter_horizontal = ("related_events_manual",)
    fieldsets = (
        ("Основне", {
            "fields": ("event", "city", "venue", "slug", "custom_title", "is_published"),
        }),
        ("Дата і квитки", {
            "fields": (
                "event_date", "sale_end_date",
                "biletyna_url", "ticket_status", "seats_left",
                "price_from", "price_to",
            ),
        }),
        ("SEO", {
            "fields": ("seo_title", "seo_description", "keywords", "og_image", "canonical_url"),
            "classes": ("collapse",),
        }),
        ("Контент", {
            "fields": ("content_html",),
            "classes": ("collapse",),
        }),
        ("Пов'язані події (ручні)", {
            "fields": ("related_events_manual",),
            "classes": ("collapse",),
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return _apply_ckeditor(form, "content_html")
