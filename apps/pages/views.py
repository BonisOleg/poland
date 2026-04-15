from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.utils.translation import gettext as _

from .models import StaticPage
from .utils import (
    extract_images_from_html,
    split_vouchery_content_into_panels,
    strip_quick_view_from_html,
    tag_products_grid,
)


def _prepare_vouchery_content(html: str) -> str:
    html = strip_quick_view_from_html(html)
    html = tag_products_grid(html)
    return html


def _render_static_page(request, page, extra_ctx=None):
    ctx = {"page": page, **(extra_ctx or {})}
    if page.slug == "vouchery" and page.layout_version != "v2":
        ctx["vouchery_content"] = _prepare_vouchery_content(page.content)
    if page.layout_version == "v2":
        images, content_no_images = extract_images_from_html(page.content)
        content_no_images = _prepare_vouchery_content(content_no_images)
        if page.slug == "vouchery":
            content_no_images = split_vouchery_content_into_panels(
                content_no_images,
                vouchery_button_href="/cart/",
                vouchery_button_label=_("KLIKNIJ PO PREZENT"),
            )
        ctx.update({"gallery_images": images, "content_no_images": content_no_images})
        return render(request, "pages/static_page_v2.html", ctx)
    return render(request, "pages/static_page.html", ctx)


def static_page(request, slug):
    page = get_object_or_404(StaticPage, slug=slug, is_published=True)
    return _render_static_page(request, page)


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
        return _render_static_page(request, page)
    except StaticPage.DoesNotExist:
        raise Http404
