from django import template
from django.urls import translate_url

register = template.Library()


@register.simple_tag(takes_context=True)
def switch_lang_url(context: dict, lang_code: str) -> str:
    request = context.get("request")
    if request is None:
        return "/"
    return translate_url(request.path, lang_code) or "/"
