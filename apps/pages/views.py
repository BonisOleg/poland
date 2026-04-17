from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.utils.translation import gettext as _

from .models import StaticPage
from .utils import (
    _THEMED_SLUGS,
    extract_images_from_html,
    extract_media_from_html,
    remove_products_grid_from_html,
    replace_city_list_with_select,
    split_after_first_vouchery_panel,
    split_html_by_h2_into_panels,
    split_vouchery_content_into_panels,
    strip_dla_dzieci_panel_headings,
    strip_elementor_residue,
    strip_quick_view_from_html,
    tag_products_grid,
    tag_vouchery_faq_section,
    tag_vouchery_offer_section,
    tag_vouchery_reasons_list,
    transform_dla_dzieci_faq_to_accordion,
    transform_vouchery_faq_editor_list_to_accordion,
)


def _prepare_vouchery_content(html: str) -> str:
    html = strip_quick_view_from_html(html)
    html = tag_products_grid(html)
    html = tag_vouchery_reasons_list(html)
    html = tag_vouchery_offer_section(html)
    html = tag_vouchery_faq_section(html)
    html = transform_vouchery_faq_editor_list_to_accordion(html)
    return html


def _render_themed_page(request, page):
    """Render dla-dzieci / dla-szkol / dla-firm with the themed layout."""
    html = strip_elementor_residue(page.content)

    db_media = list(page.media.all())
    if db_media:
        # DB media is authoritative — just strip media tags from html to avoid duplication
        images_from_db = [
            {"src": m.image.url, "alt": m.caption or page.title}
            for m in db_media
            if m.kind == "image" and m.image
        ]
        videos_from_db = []
        for m in db_media:
            if m.kind != "video":
                continue
            if m.video_file:
                videos_from_db.append({"video_url": m.video_file.url})
            elif m.video_embed_url:
                videos_from_db.append({"embed_url": m.video_embed_url})
        # Strip media tags from html so they're not duplicated inside panels
        _, _, html = extract_media_from_html(html)
        images, videos = images_from_db, videos_from_db
    else:
        images, videos, html = extract_media_from_html(html)

    # dla-dzieci: strip duplicate h1 and empty Galeria panel before split,
    # then replace city lists (flat HTML level — before panels are built).
    if page.slug == "dla-dzieci":
        html = strip_dla_dzieci_panel_headings(html)
        html = replace_city_list_with_select(html)

    panels_html = split_html_by_h2_into_panels(html)

    # FAQ accordion must run AFTER split so .event-content-block sections exist.
    if page.slug == "dla-dzieci":
        panels_html = transform_dla_dzieci_faq_to_accordion(panels_html)
    # Derive slug from page.slug for a stable theme class; keep it simple
    page_theme = page.slug  # e.g. "dla-dzieci"

    ctx = {
        "page": page,
        "page_theme": page_theme,
        "panels_html": panels_html,
        "images": images,
        "videos": videos,
    }
    return render(request, "pages/static_page_themed.html", ctx)


def _render_static_page(request, page, extra_ctx=None):
    ctx = {"page": page, **(extra_ctx or {})}
    if page.slug in _THEMED_SLUGS:
        return _render_themed_page(request, page)
    if page.slug == "vouchery" and page.layout_version != "v2":
        ctx["vouchery_content"] = _prepare_vouchery_content(page.content)
    if page.layout_version == "v2":
        from apps.vouchers.models import Voucher

        images, content_no_images = extract_images_from_html(page.content)
        content_no_images = _prepare_vouchery_content(content_no_images)
        if page.slug == "vouchery":
            content_no_images = split_vouchery_content_into_panels(
                content_no_images,
                vouchery_button_href="#voucher",
                vouchery_button_label=_("KLIKNIJ PO PREZENT"),
            )
            content_no_images = remove_products_grid_from_html(content_no_images)
            vouchery_first_panel, vouchery_rest_panels = split_after_first_vouchery_panel(
                content_no_images
            )
            vouchers = Voucher.objects.filter(is_active=True).order_by("sort_order", "price")
            ctx.update(
                {
                    "gallery_images": images,
                    "vouchery_first_panel": vouchery_first_panel,
                    "vouchery_rest_panels": vouchery_rest_panels,
                    "vouchers": vouchers,
                }
            )
        else:
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
