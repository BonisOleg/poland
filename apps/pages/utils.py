from __future__ import annotations

from html import escape

from bs4 import BeautifulSoup, Tag

# h2 text substrings (lowercase match) that start a new panel on vouchery v2 — PL / EN / RU
VOUCHERY_V2_SECTION_H2_MARKERS: tuple[str, ...] = (
    "jak wykorzystać",
    "how to use",
    "dlaczego voucher",
    "why the voucher",
    "why is the voucher",
    "5 powodów",
    "5 reasons",
    "chcesz zaskoczyć",
    "want to surprise",
    "surprise your children",
    "najczęściej zadawane",
    "frequently asked",
    "часто задаваемые",
    "как использовать",
    "почему подарочный",
    "5 причин",
    "хотите сделать сюрприз",
)


def strip_quick_view_from_html(html: str) -> str:
    """Remove WooCommerce / Premium Woo Quick View UI from imported HTML (voucher page)."""
    if not html or not html.strip():
        return html

    soup = BeautifulSoup(html, "html.parser")
    for el in soup.select('[class*="premium-woo-qv"]'):
        el.decompose()
    for el in soup.select(".vouchery-quick-view"):
        el.decompose()
    for el in soup.select(".yith-wcqv-button, .yith-quick-view, [data-yith-wcqv]"):
        el.decompose()
    return str(soup)


def _is_product_li(tag: Tag) -> bool:
    """Return True if a <li> looks like a voucher product item."""
    if tag.name != "li":
        return False
    # Must have a heading with a link AND an add-to-cart link
    has_heading = bool(tag.find(["h2", "h3", "h4"]))
    atc = tag.find("a", href=lambda h: h and "add-to-cart" in h)
    return has_heading and bool(atc)


def tag_products_grid(html: str) -> str:
    """Find the <ul> containing voucher product items and add the 'vouchery-products-grid' class.

    The content in the DB is already cleaned by clean_elementor_content,
    so there is no ul.products class — just a plain <ul> with <li> product rows.
    """
    if not html or not html.strip():
        return html

    soup = BeautifulSoup(html, "html.parser")
    for ul in soup.find_all("ul"):
        if not isinstance(ul, Tag):
            continue
        li_tags = [c for c in ul.children if isinstance(c, Tag) and c.name == "li"]
        if not li_tags:
            continue
        product_lis = [li for li in li_tags if _is_product_li(li)]
        # At least half of li items look like products → tag the list
        if len(product_lis) >= max(1, len(li_tags) // 2):
            existing = ul.get("class") or []
            if "vouchery-products-grid" not in existing:
                ul["class"] = list(existing) + ["vouchery-products-grid"]
    return str(soup)


_REASONS_H2_MARKERS: tuple[str, ...] = (
    "5 powodów",
    "5 reasons",
    "5 причин",
)


def tag_vouchery_reasons_list(html: str) -> str:
    """Mark the <ul> under the «5 reasons to visit…» heading for list + divider styling."""
    if not html or not html.strip():
        return html

    soup = BeautifulSoup(html, "html.parser")
    for h2 in soup.find_all("h2"):
        if not isinstance(h2, Tag):
            continue
        t = (h2.get_text() or "").strip().lower()
        if not any(m in t for m in _REASONS_H2_MARKERS):
            continue
        nxt = h2.find_next_sibling()
        if not nxt or nxt.name != "ul":
            continue
        if "vouchery-products-grid" in (nxt.get("class") or []):
            continue
        existing = nxt.get("class") or []
        if "vouchery-reasons-list" not in existing:
            nxt["class"] = list(existing) + ["vouchery-reasons-list"]
        break
    return str(soup)


def extract_images_from_html(html: str) -> tuple[list[dict[str, str]], str]:
    """Parse HTML, remove all <img> tags, and return them separately.

    Returns:
        (images, cleaned_html) where images is a list of {"src": ..., "alt": ...}
        dicts (empty src entries are skipped) and cleaned_html has the img tags removed.
    """
    if not html or not html.strip():
        return [], html

    soup = BeautifulSoup(html, "html.parser")
    images: list[dict[str, str]] = []

    for img in soup.find_all("img"):
        if not isinstance(img, Tag):
            continue
        src = (img.get("src") or "").strip()
        if not src:
            img.decompose()
            continue
        alt = (img.get("alt") or "").strip()
        images.append({"src": src, "alt": alt})
        parent = img.parent
        img.decompose()
        if parent and isinstance(parent, Tag) and parent.name in ("a", "p", "figure", "div"):
            if not parent.get_text(strip=True) and not parent.find(True):
                parent.decompose()

    return images, str(soup)


def _h2_opens_vouchery_v2_section(tag: Tag) -> bool:
    if tag.name != "h2":
        return False
    t = (tag.get_text() or "").strip().lower()
    return any(m in t for m in VOUCHERY_V2_SECTION_H2_MARKERS)


def split_vouchery_content_into_panels(
    html: str,
    *,
    vouchery_button_href: str = "/cart/",
    vouchery_button_label: str = "KLIKNIJ PO PREZENT",
) -> str:
    """Wrap top-level HTML nodes into stacked event-style panels (vouchery v2).

    Splits before each h2 whose text matches VOUCHERY_V2_SECTION_H2_MARKERS.
    The first panel gets data attributes for vouchery-cart.js.
    """
    if not html or not html.strip():
        return html

    soup = BeautifulSoup(html, "html.parser")
    nodes = [c for c in soup.children if isinstance(c, Tag)]
    if not nodes:
        return html

    panels: list[list[Tag]] = []
    current: list[Tag] = []
    for node in nodes:
        if _h2_opens_vouchery_v2_section(node) and current:
            panels.append(current)
            current = [node]
        else:
            current.append(node)
    if current:
        panels.append(current)

    out_parts: list[str] = []
    for i, panel_nodes in enumerate(panels):
        chunk = _wrap_vouchery_panel_nodes(
            panel_nodes,
            with_cart_data=(i == 0),
            vouchery_button_href=vouchery_button_href,
            vouchery_button_label=vouchery_button_label,
        )
        if chunk:
            out_parts.append(chunk)
    return "\n".join(out_parts) if out_parts else html


def _wrap_vouchery_panel_nodes(
    nodes: list[Tag],
    *,
    with_cart_data: bool,
    vouchery_button_href: str,
    vouchery_button_label: str,
) -> str:
    if not nodes:
        return ""
    inner_content = "".join(str(n) for n in nodes)
    data_attrs = ""
    if with_cart_data:
        data_attrs = (
            f' data-vouchery-button-href="{escape(vouchery_button_href, quote=True)}"'
            f' data-vouchery-button-label="{escape(vouchery_button_label, quote=True)}"'
        )
    return (
        '<section class="event-detail__panel event-content-block">'
        '<div class="event-content-block__body event-content--vouchery"'
        f"{data_attrs}>"
        f"{inner_content}</div></section>"
    )
