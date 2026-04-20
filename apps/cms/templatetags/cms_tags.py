"""Template tags for the unified CMS page builder."""

from __future__ import annotations

from django import template
from django.contrib.contenttypes.models import ContentType
from django.utils.safestring import mark_safe

from apps.cms.models import KIND_RELATED, PageBlock
from apps.cms.utils import get_blocks_for, has_blocks, resolve_related_targets


register = template.Library()


# Allowed kinds — guard against future renames sneaking arbitrary include paths
_ALLOWED_KINDS = {
    "text", "image", "gallery", "video", "form",
    "countdown", "reviews", "related", "cta", "html",
}


def _enrich_related(block: PageBlock, owner) -> list:
    """Return a list of related entities for a 'related' block.

    Strategy ``manual``: resolve RelatedItem rows.
    Strategy ``city`` / ``category``: only meaningful when owner is an
    EventCity — defer to its own helper.
    """
    if block.related_strategy == "manual":
        items = list(block.related_items.all())
        return resolve_related_targets(items)[: block.related_limit or 6]

    # Auto strategies — only EventCity owners support them out of the box.
    from apps.events.models import EventCity  # local import to avoid cycle

    if not isinstance(owner, EventCity):
        return []

    qs = EventCity.objects.filter(is_published=True).exclude(pk=owner.pk)
    if block.related_strategy == "city" and owner.city_id:
        qs = qs.filter(city_id=owner.city_id)
    elif block.related_strategy == "category" and owner.event_id:
        qs = qs.filter(event__categories__in=owner.event.categories.all())
    return list(qs.select_related("event", "city")[: block.related_limit or 6])


def _enrich_reviews(block: PageBlock, owner) -> list:
    """Approved reviews for an EventCity owner; empty for other owner types."""
    from apps.events.models import EventCity

    if not isinstance(owner, EventCity):
        return []
    return list(owner.reviews.filter(is_approved=True)[: block.reviews_limit or 10])


@register.inclusion_tag("cms/_render.html", takes_context=True)
def render_blocks(context, owner):
    """Render all visible CMS blocks for ``owner`` in order."""
    request = context.get("request")
    blocks = list(get_blocks_for(owner))

    enriched: list[dict] = []
    for block in blocks:
        item = {"block": block}
        if block.kind == KIND_RELATED:
            item["related"] = _enrich_related(block, owner)
        elif block.kind == "reviews":
            item["reviews"] = _enrich_reviews(block, owner)
        elif block.kind == "gallery":
            item["gallery_items"] = list(block.gallery_items.all())
        enriched.append(item)

    return {
        "items": enriched,
        "owner": owner,
        "request": request,
        "allowed_kinds": _ALLOWED_KINDS,
    }


@register.simple_tag
def cms_has_blocks(owner) -> bool:
    """Cheap existence check for templates."""
    return has_blocks(owner)


@register.filter
def cms_block_template(kind: str) -> str:
    """Return safe template path for a block kind, falling back to _html.html."""
    if kind in _ALLOWED_KINDS:
        return f"cms/blocks/_{kind}.html"
    return "cms/blocks/_html.html"
