from __future__ import annotations

from bs4 import BeautifulSoup, Tag


def strip_quick_view_from_html(html: str) -> str:
    """Remove WooCommerce / Premium Woo Quick View UI from imported HTML (voucher page)."""
    if not html or not html.strip():
        return html

    soup = BeautifulSoup(html, "html.parser")
    # Premium Addons for Elementor (class contains premium-woo-qv…)
    for el in soup.select('[class*="premium-woo-qv"]'):
        el.decompose()
    for el in soup.select(".vouchery-quick-view"):
        el.decompose()
    for el in soup.select(".yith-wcqv-button, .yith-quick-view, [data-yith-wcqv]"):
        el.decompose()
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
        # Remove the img and any wrapper that becomes empty after removal
        parent = img.parent
        img.decompose()
        # Clean up empty wrappers: <a>, <p>, <figure>, <div> left with only whitespace
        if parent and isinstance(parent, Tag) and parent.name in ("a", "p", "figure", "div"):
            if not parent.get_text(strip=True) and not parent.find(True):
                parent.decompose()

    return images, str(soup)
