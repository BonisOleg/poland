from modeltranslation.translator import register, TranslationOptions
from .models import Voucher


@register(Voucher)
class VoucherTO(TranslationOptions):
    fields = ("name", "description")
