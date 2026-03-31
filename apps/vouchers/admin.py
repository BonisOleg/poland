from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import Voucher


@admin.register(Voucher)
class VoucherAdmin(TranslationAdmin):
    list_display = ("name", "price", "currency", "is_active")
    list_editable = ("is_active", "price")
