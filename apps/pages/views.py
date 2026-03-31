from django.shortcuts import render, get_object_or_404
from django.http import Http404
from .models import StaticPage


def static_page(request, slug):
    page = get_object_or_404(StaticPage, slug=slug, is_published=True)
    return render(request, "pages/static_page.html", {"page": page})


def catch_all_page(request, slug):
    from apps.events.models import EventCity
    try:
        ec = EventCity.objects.select_related("event", "city", "venue").get(
            slug=slug, is_published=True
        )
        from apps.events.views import event_detail
        return event_detail(request, slug)
    except EventCity.DoesNotExist:
        pass

    try:
        page = StaticPage.objects.get(slug=slug, is_published=True)
        return render(request, "pages/static_page.html", {"page": page})
    except StaticPage.DoesNotExist:
        raise Http404
