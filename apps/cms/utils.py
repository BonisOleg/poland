"""Helpers to fetch and render CMS blocks for any owner."""

from __future__ import annotations

from typing import Iterable

from django.contrib.contenttypes.models import ContentType
from django.db.models import QuerySet

from .models import PageBlock


def get_blocks_for(owner) -> QuerySet[PageBlock]:
    """Return ordered visible blocks for a given owner instance."""
    if owner is None or owner.pk is None:
        return PageBlock.objects.none()
    ct = ContentType.objects.get_for_model(owner.__class__)
    return (
        PageBlock.objects.filter(
            content_type=ct,
            object_id=owner.pk,
            is_visible=True,
        )
        .select_related("content_type")
        .prefetch_related(
            "gallery_items",
            "related_items__target_content_type",
        )
        .order_by("sort_order", "id")
    )


def has_blocks(owner) -> bool:
    """Cheap existence check used by templates to switch to the new layout."""
    if owner is None or owner.pk is None:
        return False
    ct = ContentType.objects.get_for_model(owner.__class__)
    return PageBlock.objects.filter(
        content_type=ct, object_id=owner.pk, is_visible=True
    ).exists()


def resolve_related_targets(items: Iterable) -> list:
    """Resolve generic ``RelatedItem`` rows to their concrete model instances.

    Avoids per-row queries by grouping object ids per content_type.
    """
    grouped: dict[int, list[int]] = {}
    order: list[tuple[int, int, int]] = []
    for idx, item in enumerate(items):
        grouped.setdefault(item.target_content_type_id, []).append(item.target_object_id)
        order.append((idx, item.target_content_type_id, item.target_object_id))

    cache: dict[tuple[int, int], object] = {}
    for ct_id, ids in grouped.items():
        ct = ContentType.objects.get_for_id(ct_id)
        model = ct.model_class()
        if model is None:
            continue
        for obj in model._default_manager.filter(pk__in=ids):
            cache[(ct_id, obj.pk)] = obj

    out: list = []
    for _idx, ct_id, obj_id in order:
        obj = cache.get((ct_id, obj_id))
        if obj is not None:
            out.append(obj)
    return out
