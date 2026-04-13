from modeltranslation.translator import register, TranslationOptions
from .models import Category, AgeGroup, Event, EventCity, EventContentBlock


@register(Category)
class CategoryTO(TranslationOptions):
    fields = ("name", "description")


@register(AgeGroup)
class AgeGroupTO(TranslationOptions):
    fields = ("name",)


@register(Event)
class EventTO(TranslationOptions):
    fields = ("title", "description", "short_description", "target_audience")


@register(EventCity)
class EventCityTO(TranslationOptions):
    fields = ("custom_title", "content_html", "seo_title", "seo_description", "keywords")


@register(EventContentBlock)
class EventContentBlockTO(TranslationOptions):
    fields = ("title", "body", "button_text")
