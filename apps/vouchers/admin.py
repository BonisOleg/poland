from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import Voucher, VoucherOrder


@admin.register(Voucher)
class VoucherAdmin(TranslationAdmin):
    list_display = ("name", "price", "currency", "is_active", "image")
    list_editable = ("is_active", "price")


@admin.register(VoucherOrder)
class VoucherOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "voucher", "buyer_email", "buyer_first_name", "buyer_last_name", "total_amount", "status", "created_at")
    list_filter = ("status", "voucher")
    search_fields = ("buyer_email", "buyer_first_name", "buyer_last_name", "payu_order_id")
    readonly_fields = ("payu_order_id", "total_amount", "created_at", "updated_at")
    ordering = ("-created_at",)
