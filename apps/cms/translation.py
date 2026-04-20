from modeltranslation.translator import register, TranslationOptions

from .models import GalleryItem, PageBlock


@register(PageBlock)
class PageBlockTO(TranslationOptions):
    fields = (
        "heading",
        "body",
        "image_alt",
        "button_text",
        "countdown_label",
    )


@register(GalleryItem)
class GalleryItemTO(TranslationOptions):
    fields = ("alt_text",)
