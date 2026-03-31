from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("author_name", "event_city", "rating", "is_approved", "created_at")
    list_filter = ("is_approved", "rating")
    search_fields = ("author_name", "content")
    list_editable = ("is_approved",)
    raw_id_fields = ("event_city",)
