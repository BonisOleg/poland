"""Strip Elementor image-carousel blocks (Swiper lazy-load; empty src) from rich HTML fields."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand

from apps.events.models import EventCity
from apps.pages.models import StaticPage

if TYPE_CHECKING:
    from bs4.element import Tag


def _class_list(tag: Tag) -> list[str]:
    raw = tag.get("class")
    if raw is None:
        return []
    if isinstance(raw, str):
        return raw.split()
    return list(raw)


def _previous_element_sibling(tag: Tag) -> Tag | None:
    sib = tag.previous_sibling
    while sib is not None:
        if getattr(sib, "name", None):
            return sib  # type: ignore[return-value]
        sib = sib.previous_sibling
    return None


def _find_e_parent_block(carousel: Tag) -> Tag | None:
    node = carousel.parent
    while node is not None:
        if node.name == "div" and "e-parent" in _class_list(node):
            return node
        node = node.parent
    return None


def _is_single_heading_parent_block(tag: Tag) -> bool:
    if tag.name != "div" or "e-parent" not in _class_list(tag):
        return False
    widgets = tag.select(".elementor-widget")
    if len(widgets) != 1:
        return False
    w0 = widgets[0]
    return "elementor-widget-heading" in _class_list(w0)


def strip_elementor_image_carousels(html: str) -> tuple[str, int]:
    """
    Remove Elementor image-carousel sections and a preceding block that is only a heading
    (e.g. \"Galeria\"). Returns (new_html, number_of_carousels_removed).
    """
    if not html or "elementor-widget-image-carousel" not in html:
        return html, 0

    soup = BeautifulSoup(html, "html.parser")
    carousels = soup.select("div.elementor-widget-image-carousel")
    if not carousels:
        return html, 0

    removed = 0
    for carousel in reversed(carousels):
        block = _find_e_parent_block(carousel)
        if block is None:
            carousel.decompose()
            removed += 1
            continue
        prev = _previous_element_sibling(block)
        if prev is not None and _is_single_heading_parent_block(prev):
            prev.decompose()
        block.decompose()
        removed += 1

    return str(soup), removed


class Command(BaseCommand):
    help = (
        "Remove Elementor image-carousel blocks (broken Swiper lazy images) from "
        "EventCity.content_html and StaticPage.content."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report changes without saving.",
        )

    def handle(self, *args, **options) -> None:
        dry_run: bool = options["dry_run"]
        ec_updated = 0
        ec_carousels = 0
        sp_updated = 0
        sp_carousels = 0

        qs_ec = EventCity.objects.exclude(content_html="").filter(
            content_html__icontains="elementor-widget-image-carousel",
        )
        for ec in qs_ec.iterator(chunk_size=100):
            new_html, n = strip_elementor_image_carousels(ec.content_html)
            if n == 0:
                continue
            ec_carousels += n
            if new_html != ec.content_html:
                ec_updated += 1
                if not dry_run:
                    ec.content_html = new_html
                    ec.save(update_fields=["content_html"])

        for page in StaticPage.objects.exclude(content="").iterator(chunk_size=50):
            if "elementor-widget-image-carousel" not in page.content:
                continue
            new_html, n = strip_elementor_image_carousels(page.content)
            if n == 0:
                continue
            sp_carousels += n
            if new_html != page.content:
                sp_updated += 1
                if not dry_run:
                    page.content = new_html
                    page.save(update_fields=["content"])

        mode = "DRY-RUN — no DB writes" if dry_run else "Done"
        self.stdout.write(
            self.style.SUCCESS(
                f"{mode}: EventCity rows touched={ec_updated}, carousels removed={ec_carousels}; "
                f"StaticPage rows touched={sp_updated}, carousels removed={sp_carousels}."
            )
        )
