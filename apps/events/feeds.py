from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.template.loader import render_to_string
from .models import EventCity


def _get_active_events():
    return (
        EventCity.objects.filter(is_published=True)
        .select_related("event", "city", "venue")
        .order_by("event_date")
    )


def google_feed(request):
    events = _get_active_events()
    site_url = settings.SITE_URL

    items = []
    for ec in events:
        items.append(
            f"<item>"
            f"<g:id>{ec.pk}</g:id>"
            f"<g:title><![CDATA[{ec.get_display_title()}]]></g:title>"
            f"<g:description><![CDATA[{ec.seo_description or ''}]]></g:description>"
            f"<g:link>{site_url}{ec.get_absolute_url()}</g:link>"
            f"<g:image_link>{ec.og_image or ''}</g:image_link>"
            f"<g:availability>{'in stock' if ec.ticket_status != 'sold_out' else 'out of stock'}</g:availability>"
            f"<g:price>{ec.price_from or '0.00'} PLN</g:price>"
            f"<g:condition>new</g:condition>"
            f"<g:brand>Hype Global Production</g:brand>"
            f"</item>"
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">'
        "<channel>"
        "<title>Hype Global Production - Events</title>"
        f"<link>{site_url}</link>"
        "<description>Bilety na wydarzenia kulturalne w Polsce</description>"
        + "".join(items)
        + "</channel></rss>"
    )
    return HttpResponse(xml, content_type="application/xml")


def meta_feed(request):
    events = _get_active_events()
    site_url = settings.SITE_URL

    items = []
    for ec in events:
        items.append(
            f"<item>"
            f"<id>{ec.pk}</id>"
            f"<title><![CDATA[{ec.get_display_title()}]]></title>"
            f"<description><![CDATA[{ec.seo_description or ''}]]></description>"
            f"<availability>{'in stock' if ec.ticket_status != 'sold_out' else 'out of stock'}</availability>"
            f"<condition>new</condition>"
            f"<price>{ec.price_from or '0.00'} PLN</price>"
            f"<link>{site_url}{ec.get_absolute_url()}</link>"
            f"<image_link>{ec.og_image or ''}</image_link>"
            f"<brand>Hype Global Production</brand>"
            f"</item>"
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        "<rss><channel>"
        + "".join(items)
        + "</channel></rss>"
    )
    return HttpResponse(xml, content_type="application/xml")


def edrone_feed(request):
    events = _get_active_events()
    site_url = settings.SITE_URL

    products = []
    for ec in events:
        products.append({
            "id": str(ec.pk),
            "title": ec.get_display_title(),
            "description": ec.seo_description or "",
            "url": f"{site_url}{ec.get_absolute_url()}",
            "image_url": ec.og_image or "",
            "price": str(ec.price_from or "0.00"),
            "currency": "PLN",
            "availability": "available" if ec.ticket_status != "sold_out" else "unavailable",
            "category": ec.event.event_type if ec.event else "",
            "city": ec.city.name if ec.city else "",
        })

    return JsonResponse({"products": products}, json_dumps_params={"ensure_ascii": False})
