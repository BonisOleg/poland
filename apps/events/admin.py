from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import Category, AgeGroup, City, Venue, Event, EventCity, EventImage


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
    list_display = ("title", "event_type", "is_active", "sort_order")
    list_filter = ("event_type", "is_active", "categories")
    search_fields = ("title",)
    prepopulated_fields = {"slug": ("title",)}
    filter_horizontal = ("categories",)
    list_editable = ("sort_order", "is_active")


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
    fieldsets = (
        ("Основное", {
            "fields": ("event", "city", "venue", "slug", "custom_title", "is_published"),
        }),
        ("Дата и билеты", {
            "fields": ("event_date", "sale_end_date", "biletyna_url", "ticket_status", "seats_left", "price_from"),
        }),
        ("SEO", {
            "fields": ("seo_title", "seo_description", "og_image", "canonical_url"),
            "classes": ("collapse",),
        }),
        ("Контент", {
            "fields": ("content_html",),
            "classes": ("collapse",),
        }),
    )
