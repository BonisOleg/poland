from __future__ import annotations

from bs4 import BeautifulSoup, Tag


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
