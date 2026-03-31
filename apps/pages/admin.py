from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import StaticPage


@admin.register(StaticPage)
class StaticPageAdmin(TranslationAdmin):
    list_display = ("title", "slug", "is_published", "show_contact_form")
    prepopulated_fields = {"slug": ("title",)}
    list_editable = ("is_published",)
