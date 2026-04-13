"""
Management command: clean_elementor_content

Transforms raw Elementor/WordPress HTML stored in StaticPage.content
(and its translated variants content_pl, content_en) into clean custom HTML.

Usage:
    python manage.py clean_elementor_content           # dry-run, shows diff count
    python manage.py clean_elementor_content --apply   # writes changes to DB
    python manage.py clean_elementor_content --slug vouchery --apply
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup, NavigableString, Tag
from django.core.management.base import BaseCommand, CommandError

from apps.pages.models import StaticPage

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Elementor class → action map
# ---------------------------------------------------------------------------

# Wrappers to fully unwrap (keep children, drop the element itself)
UNWRAP_CLASSES = {
    "elementor",            # root container <div class="elementor elementor-NNN">
    "elementor-section",
    "elementor-container",
    "elementor-row",
    "elementor-column",
    "elementor-column-wrap",
    "elementor-widget-wrap",
    "elementor-widget",
    "elementor-widget-container",
    "e-con-inner",
    "elementor-button-wrapper",
    "elementor-icon-box-content",
}

# Elementor data-attributes to strip from any element
STRIP_DATA_ATTRS = {
    "data-elementor-type",
    "data-elementor-id",
    "data-id",
    "data-element_type",
    "data-element-type",
    "data-widget_type",
    "data-widget-type",
    "data-settings",
}

# Containers to unwrap only when they have meaningful content;
# otherwise remove entirely. Handled separately below.
CONDITIONAL_UNWRAP_CLASSES = {
    "e-con",  # Elementor v3.6+ flex/grid container
}

# Elements to delete outright (no content worth keeping)
DELETE_CLASSES = {
    "elementor-widget-spacer",
    "elementor-shape",          # decorative SVG dividers
}

# Class renames: old → new  (element tag is preserved)
RENAME_MAP = {
    "elementor-icon-list-items": "content-icon-list",
    "elementor-icon-list-item": "content-icon-list__item",
    "elementor-icon-list-icon": "content-icon-list__icon",
    "elementor-icon-list-text": "content-icon-list__text",
    "elementor-icon-box-wrapper": "content-box",
    "elementor-icon-box-icon": "content-box__icon",
    "elementor-icon-box-description": "content-box__desc",
    "elementor-accordion": "content-accordion",
    "elementor-accordion-item": "content-accordion__item",
    "elementor-accordion-title": "content-accordion__title",
    "elementor-tab-content": "content-accordion__body",
    "wp-block-columns": "content-columns",
    "wp-block-column": "content-column",
}

# Button classes: add our own alongside (don't strip elementor one yet — handled later)
BUTTON_CLASSES = {"elementor-button", "elementor-button-link"}

# Heading widget: just drop the elementor class, keep the tag
HEADING_CLASS = "elementor-heading-title"

# Inline style attributes on these selectors will be stripped
STRIP_STYLE_PREFIXES = ("elementor", "e-con", "e-child", "wp-block")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _has_meaningful_content(tag: Tag) -> bool:
    """Return True if the tag contains visible content."""
    if tag.find(["video", "iframe", "img", "svg", "canvas", "object",
                 "embed", "table", "blockquote", "pre", "ul", "ol"]):
        return True
    text = tag.get_text(separator=" ", strip=True)
    return len(text) > 1


def _classes(tag) -> set[str]:
    if not isinstance(tag, Tag) or not tag.attrs:
        return set()
    cls = tag.attrs.get("class")
    return set(cls) if cls else set()


def _has_class(tag: Tag, cls: str) -> bool:
    return cls in _classes(tag)


def _has_any_class(tag: Tag, cls_set: set) -> bool:
    return bool(_classes(tag) & cls_set)


def _strip_elementor_style(tag: Tag) -> None:
    """Remove inline style="" from tags that carry Elementor classes."""
    classes = _classes(tag)
    if any(c.startswith(tuple(STRIP_STYLE_PREFIXES)) for c in classes):
        if tag.get("style"):
            del tag["style"]


def _remap_classes(tag: Tag) -> None:
    """Replace Elementor class names with custom ones in-place."""
    classes = list(_classes(tag))
    new_classes = []
    changed = False
    for c in classes:
        if c in RENAME_MAP:
            new_classes.append(RENAME_MAP[c])
            changed = True
        elif c.startswith(("elementor-", "e-con", "e-child", "wp-block-")):
            # Drop remaining internal Elementor utility classes
            changed = True
        else:
            new_classes.append(c)
    if changed:
        if new_classes:
            tag["class"] = new_classes
        else:
            del tag["class"]


def _class_tokens(tag: Tag) -> list[str]:
    cls = tag.get("class")
    if not cls:
        return []
    if isinstance(cls, str):
        return cls.split()
    return list(cls)


def _set_classes(tag: Tag, classes: list[str]) -> None:
    if classes:
        tag["class"] = classes
    else:
        tag.attrs.pop("class", None)


def _replace_angle_double_down_svgs(soup: BeautifulSoup) -> None:
    """Elementor e-font SVG chevrons → pure CSS hook (no WP/FA)."""
    for svg in list(soup.find_all("svg")):
        if not isinstance(svg, Tag):
            continue
        tokens = " ".join(_class_tokens(svg)).lower()
        if "angle-double-down" not in tokens:
            continue
        span = soup.new_tag(
            "span",
            attrs={"class": "content-decor content-decor--chevrons-down", "aria-hidden": "true"},
        )
        svg.replace_with(span)


def _normalize_content_box_svgs(soup: BeautifulSoup) -> None:
    """Strip Elementor icon class names from inline SVGs; keep paths."""
    for wrap in soup.find_all(class_="content-box__icon"):
        if not isinstance(wrap, Tag):
            continue
        for svg in wrap.find_all("svg"):
            if not isinstance(svg, Tag):
                continue
            cleaned = [
                c
                for c in _class_tokens(svg)
                if not c.startswith("e-") and c != "e-font-icon-svg"
            ]
            if "content-box__svg" not in cleaned:
                cleaned.append("content-box__svg")
            _set_classes(svg, cleaned)


def _upgrade_quick_view_rows(soup: BeautifulSoup) -> None:
    """Premium Woo 'Quick View' rows: drop FA <i>, add hook class for CSS bullet."""
    for el in soup.select(".premium-woo-qv-btn"):
        if not isinstance(el, Tag):
            continue
        for icon in el.find_all("i"):
            if isinstance(icon, Tag):
                icon.decompose()
        cls = _class_tokens(el)
        if "vouchery-quick-view" not in cls:
            cls.append("vouchery-quick-view")
        _set_classes(el, cls)


def _fix_quick_view_modal_close(soup: BeautifulSoup) -> None:
    """Replace FA window-close with project class (styled in CSS)."""
    for a in soup.select("a.premium-woo-quick-view-close"):
        if not isinstance(a, Tag):
            continue
        cls = [c for c in _class_tokens(a) if not c.startswith("fa") and c not in ("fa",)]
        if "vouchery-modal-close" not in cls:
            cls.append("vouchery-modal-close")
        _set_classes(a, cls)
        if not a.get("aria-label"):
            a["aria-label"] = "Zamknij"


def _strip_orphan_font_awesome_icons(soup: BeautifulSoup) -> None:
    """Remove leftover <i> tags that depended on Font Awesome / dashicons."""
    for tag in list(soup.find_all("i")):
        if not isinstance(tag, Tag):
            continue
        cls = _class_tokens(tag)
        if not cls:
            tag.decompose()
            continue
        joined = " ".join(cls).lower()
        if any(
            x in joined
            for x in (
                "fa-",
                "fas",
                "far",
                "fab",
                "fad",
                "fal",
                "font-awesome",
                "dashicons",
                "eicons",
            )
        ):
            tag.decompose()


def _ensure_vouchery_cart_marker(soup: BeautifulSoup) -> None:
    """If a cart CTA survives cleanup, tag it so vouchery-cart.js can find it."""
    if soup.select_one("[data-vouchery-cart-widget]"):
        return
    for a in soup.select('a[href*="cart"]'):
        if not isinstance(a, Tag):
            continue
        href = (a.get("href") or "").lower()
        if "/cart" not in href and "cart/" not in href:
            continue
        if a.find(["svg", "img"]) or len(a.get_text(strip=True)) < 48:
            a["data-vouchery-cart-widget"] = ""
            wcls = _class_tokens(a)
            if "vouchery-cart-widget" not in wcls:
                wcls.append("vouchery-cart-widget")
            _set_classes(a, wcls)
            return


def _accordion_to_details(soup: BeautifulSoup) -> None:
    """Convert .content-accordion-item + title/body into native <details>/<summary>."""
    for item in soup.find_all(class_="content-accordion__item"):
        details = soup.new_tag("details", attrs={"class": "content-accordion__item"})
        title_el = item.find(class_="content-accordion__title")
        body_el = item.find(class_="content-accordion__body")

        if title_el:
            summary = soup.new_tag("summary", attrs={"class": "content-accordion__title"})
            summary.append(title_el.get_text(strip=True))
            details.append(summary)

        if body_el:
            for child in list(body_el.children):
                details.append(child.extract())

        item.replace_with(details)


# ---------------------------------------------------------------------------
# Core transform
# ---------------------------------------------------------------------------

def transform_html(raw_html: str) -> str:
    """Parse Elementor HTML and return clean custom HTML string."""
    if not raw_html or not raw_html.strip():
        return raw_html

    soup = BeautifulSoup(raw_html, "html.parser")

    # --- Pass 1: delete spacers and decorative elements ---
    for tag in soup.find_all(True):
        if isinstance(tag, NavigableString):
            continue
        if _has_any_class(tag, DELETE_CLASSES):
            tag.decompose()

    # --- Pass 2: delete empty conditional-unwrap containers ---
    # Process innermost first to avoid operating on already-removed nodes
    for tag in reversed(soup.find_all(True)):
        if not isinstance(tag, Tag):
            continue
        if _has_any_class(tag, CONDITIONAL_UNWRAP_CLASSES):
            if not _has_meaningful_content(tag):
                tag.decompose()
            else:
                tag.unwrap()

    # --- Pass 3: unwrap structural wrappers ---
    changed = True
    while changed:
        changed = False
        for tag in soup.find_all(True):
            if not isinstance(tag, Tag):
                continue
            if _has_any_class(tag, UNWRAP_CLASSES):
                tag.unwrap()
                changed = True
                break  # restart after any mutation

    # --- Pass 4a: strip Elementor data-attributes from all remaining tags ---
    for tag in soup.find_all(True):
        if not isinstance(tag, Tag) or not tag.attrs:
            continue
        for attr in STRIP_DATA_ATTRS:
            tag.attrs.pop(attr, None)

    # --- Pass 4b: strip inline styles on remaining Elementor nodes ---
    for tag in soup.find_all(True):
        if isinstance(tag, Tag):
            _strip_elementor_style(tag)

    # --- Pass 5: rename/remap classes ---
    for tag in soup.find_all(True):
        if isinstance(tag, Tag):
            _remap_classes(tag)

    # --- Pass 6: heading-title — class already stripped in pass 5 ---
    # (elementor-heading-title is not in RENAME_MAP, will be dropped by _remap_classes)

    # --- Pass 7: map button classes ---
    for tag in soup.find_all(True):
        if not isinstance(tag, Tag):
            continue
        classes = _classes(tag)
        if classes & BUTTON_CLASSES:
            new_cls = [c for c in classes if c not in BUTTON_CLASSES]
            new_cls = ["btn", "btn--outline"] + new_cls
            tag["class"] = new_cls

    # --- Pass 8: convert accordion items to <details>/<summary> ---
    _accordion_to_details(soup)

    # --- Pass A: strip WP/FA SVGs from icon-list icon spans ---
    # Leaves the span as a CSS ::before hook; removes WordPress SVG dependency.
    for icon_span in soup.find_all(class_="content-icon-list__icon"):
        if not isinstance(icon_span, Tag):
            continue
        for svg in icon_span.find_all("svg"):
            svg.decompose()
        for inner in list(icon_span.find_all("span")):
            inner.unwrap()

    # --- Pass A2: Vouchers / Woo — replace WP-dependent icons with project hooks ---
    _replace_angle_double_down_svgs(soup)
    _normalize_content_box_svgs(soup)
    _upgrade_quick_view_rows(soup)
    _fix_quick_view_modal_close(soup)
    _strip_orphan_font_awesome_icons(soup)
    _ensure_vouchery_cart_marker(soup)

    # --- Pass B: transform .premium-button CTA links into .btn elements ---
    # Keeps href and visible text; removes SVG icon and inner div wrappers.
    for el in list(soup.find_all(class_="premium-button")):
        if not isinstance(el, Tag):
            continue
        text = el.get_text(separator=" ", strip=True)
        if not text:
            continue
        href = el.get("href") or "#"
        new_tag = soup.new_tag("a", href=href)
        new_tag["class"] = ["btn", "btn--outline", "btn--lg"]
        new_tag.string = text
        el.replace_with(new_tag)

    # --- Pass 9: collapse multiple blank lines / trailing whitespace ---
    result = str(soup)
    result = re.sub(r"\n{3,}", "\n\n", result)
    result = re.sub(r"[ \t]+\n", "\n", result)

    return result.strip()


# ---------------------------------------------------------------------------
# Command
# ---------------------------------------------------------------------------

CONTENT_FIELDS = ["content", "content_pl", "content_en"]


class Command(BaseCommand):
    help = "Strip Elementor wrappers from StaticPage.content and replace with clean HTML"

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="Write transformed HTML back to the database (default: dry-run)",
        )
        parser.add_argument(
            "--slug",
            type=str,
            default=None,
            help="Process only the page with this slug",
        )

    def handle(self, *args, **options):
        apply = options["apply"]
        slug = options["slug"]

        qs = StaticPage.objects.all()
        if slug:
            qs = qs.filter(slug=slug)
            if not qs.exists():
                raise CommandError(f"No StaticPage with slug='{slug}'")

        mode = "APPLY" if apply else "DRY-RUN"
        self.stdout.write(self.style.WARNING(f"[{mode}] Processing {qs.count()} page(s)…\n"))

        changed_pages = 0

        for page in qs:
            updates = {}
            for field in CONTENT_FIELDS:
                original = getattr(page, field) or ""
                cleaned = transform_html(original)
                if cleaned != original:
                    updates[field] = cleaned

            if updates:
                changed_pages += 1
                self.stdout.write(
                    f"  {'CHANGED' if apply else 'WOULD CHANGE'}: "
                    f"[{page.slug}] fields: {', '.join(updates)}"
                )
                if apply:
                    for field, value in updates.items():
                        setattr(page, field, value)
                    # Only update content fields — never touch seo_title/seo_description/keywords
                    page.save(update_fields=list(updates.keys()))
            else:
                self.stdout.write(f"  SKIP (no change): [{page.slug}]")

        summary = (
            f"\n[{mode}] Done. {changed_pages}/{qs.count()} page(s) "
            f"{'updated' if apply else 'would be updated'}."
        )
        self.stdout.write(self.style.SUCCESS(summary))
