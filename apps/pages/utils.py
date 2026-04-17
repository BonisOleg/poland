from __future__ import annotations

from html import escape

from bs4 import BeautifulSoup, NavigableString, Tag

# h2 text substrings (lowercase match) that start a new panel on vouchery v2 — PL / EN / RU
VOUCHERY_V2_SECTION_H2_MARKERS: tuple[str, ...] = (
    "jak wykorzystać",
    "how to use",
    "dlaczego voucher",
    "why the voucher",
    "why is the voucher",
    "why is a voucher",
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


def remove_products_grid_from_html(html: str) -> str:
    """Remove WooCommerce product <ul> tagged with vouchery-products-grid (replaced by DB Voucher slider)."""
    if not html or not html.strip():
        return html

    soup = BeautifulSoup(html, "html.parser")
    for ul in soup.find_all("ul"):
        if not isinstance(ul, Tag):
            continue
        cls = ul.get("class") or []
        if isinstance(cls, str):
            has_grid = "vouchery-products-grid" in cls.split()
        else:
            has_grid = "vouchery-products-grid" in cls
        if has_grid:
            ul.decompose()
    return str(soup)


def split_after_first_vouchery_panel(html: str) -> tuple[str, str]:
    """Split vouchery v2 HTML after the first ``section.event-detail__panel`` (intro vs rest).

    Returns (first_panel_html, rest_html). Single-panel pages return (full_html, "").
    """
    if not html or not html.strip():
        return "", ""

    soup = BeautifulSoup(html, "html.parser")
    sections: list[Tag] = []
    for child in soup.children:
        if not isinstance(child, Tag) or child.name != "section":
            continue
        cls = child.get("class") or []
        if isinstance(cls, str):
            ok = "event-detail__panel" in cls.split()
        else:
            ok = "event-detail__panel" in cls
        if ok:
            sections.append(child)

    if len(sections) <= 1:
        return html, ""
    first_html = str(sections[0])
    rest_html = "".join(str(s) for s in sections[1:])
    return first_html, rest_html


_REASONS_H2_MARKERS: tuple[str, ...] = (
    "5 powodów",
    "5 reasons",
    "5 причин",
    "dlaczego voucher",
    "why the voucher",
    "why is the voucher",
    "why is a voucher",
    "почему подарочный",
    "give your loved",
)

# «CHCESZ ZASKOCZYĆ DZIECI?» — PL / EN / RU substrings (lowercase)
_OFFER_SECTION_H2_MARKERS: tuple[str, ...] = (
    "chcesz zaskoczyć dzieci",
    "want to surprise your children",
    "хотите сделать сюрприз детям",
)

# FAQ panel heading — PL / EN / RU (lowercase)
_FAQ_SECTION_H2_MARKERS: tuple[str, ...] = (
    "najczęściej zadawane",
    "frequently asked",
    "часто задаваемые",
)


def _elementor_widget_ancestor(h2: Tag) -> Tag | None:
    """Innermost div.elementor-element.elementor-widget wrapping the heading (imported Elementor HTML)."""
    el: Tag | None = h2.parent
    while el is not None:
        cls = el.get("class") or []
        if "elementor-element" in cls and "elementor-widget" in cls:
            return el
        parent = el.parent
        el = parent if isinstance(parent, Tag) else None
    return None


def _collect_nodes_after_heading(h2: Tag) -> list[Tag]:
    """Nodes to wrap under the heading: direct siblings (clean HTML) or following Elementor widget columns.

    In raw Elementor markup the <p> and CTA are *not* siblings of <h2>; they sit in the next
    ``.elementor-element`` widgets. Previously we only walked ``h2.next_sibling``, so ``to_wrap``
    was empty and no CSS hooks were emitted — the lower blocks looked unchanged.
    """
    out: list[Tag] = []
    sib = h2.next_sibling
    while sib is not None:
        nxt = sib.next_sibling
        if isinstance(sib, Tag):
            if sib.name == "h2":
                break
            out.append(sib)
        sib = nxt
    if out:
        return out

    widget = _elementor_widget_ancestor(h2)
    if widget is None:
        return []

    for s in widget.find_next_siblings():
        if not isinstance(s, Tag):
            continue
        # Next layout block that introduces its own heading — start of the following section
        if s.find("h2") is not None:
            break
        out.append(s)
    return out


def tag_vouchery_offer_section(html: str) -> str:
    """Wrap copy + CTA after the «surprise children» heading so CSS can place the divider under h2 only."""
    if not html or not html.strip():
        return html

    soup = BeautifulSoup(html, "html.parser")
    for h2 in soup.find_all("h2"):
        if not isinstance(h2, Tag):
            continue
        t = (h2.get_text() or "").strip().lower()
        if not any(m in t for m in _OFFER_SECTION_H2_MARKERS):
            continue
        if "vouchery-offer-section__title" in (h2.get("class") or []):
            continue
        to_wrap = _collect_nodes_after_heading(h2)
        if not to_wrap:
            continue
        existing = h2.get("class") or []
        h2["class"] = list(existing) + ["vouchery-offer-section__title"]
        wrapper = soup.new_tag("div", attrs={"class": "vouchery-offer-body"})
        h2.insert_after(wrapper)
        for el in to_wrap:
            wrapper.append(el.extract())
    return str(soup)


def tag_vouchery_faq_section(html: str) -> str:
    """Wrap FAQ body so the divider sits under the «Najczęściej zadawane pytania (FAQ)» h2 only."""
    if not html or not html.strip():
        return html

    soup = BeautifulSoup(html, "html.parser")
    for h2 in soup.find_all("h2"):
        if not isinstance(h2, Tag):
            continue
        t = (h2.get_text() or "").strip().lower()
        if not any(m in t for m in _FAQ_SECTION_H2_MARKERS):
            continue
        if "vouchery-faq-section__title" in (h2.get("class") or []):
            continue
        to_wrap = _collect_nodes_after_heading(h2)
        if not to_wrap:
            continue
        existing = h2.get("class") or []
        h2["class"] = list(existing) + ["vouchery-faq-section__title"]
        wrapper = soup.new_tag("div", attrs={"class": "vouchery-faq-body"})
        h2.insert_after(wrapper)
        for el in to_wrap:
            wrapper.append(el.extract())
    return str(soup)


def _faq_li_to_answer_p(soup: BeautifulSoup, ul: Tag) -> Tag:
    """Turn the first <li> of a CKEditor FAQ <ul> into a single <p> for .content-accordion styles."""
    li = ul.find("li", recursive=False)
    if not li:
        return soup.new_tag("p")
    child_tags = [c for c in li.children if isinstance(c, Tag)]
    if len(child_tags) == 1 and child_tags[0].name == "p":
        return child_tags[0].extract()
    p = soup.new_tag("p")
    for child in list(li.children):
        p.append(child.extract())
    return p


def _build_faq_details_from_p_and_ul(soup: BeautifulSoup, p_tag: Tag, ul_tag: Tag) -> Tag:
    details = soup.new_tag("details", attrs={"class": ["content-accordion__item"]})
    summary = soup.new_tag("summary", attrs={"class": ["content-accordion__title"]})
    for child in list(p_tag.children):
        summary.append(child.extract())
    p_tag.decompose()
    answer_p = _faq_li_to_answer_p(soup, ul_tag)
    ul_tag.decompose()
    details.append(summary)
    details.append(answer_p)
    return details


def transform_vouchery_faq_editor_list_to_accordion(html: str) -> str:
    """Convert CKEditor FAQ pattern (direct <p> + <ul><li>answer) into native <details> accordion.

    Skips bodies that already contain .content-accordion or legacy .elementor-accordion.
    """
    if not html or not html.strip():
        return html

    soup = BeautifulSoup(html, "html.parser")
    for body in soup.find_all("div", class_=lambda c: c and "vouchery-faq-body" in c):
        if not isinstance(body, Tag):
            continue
        if body.select_one(".content-accordion") or body.select_one(".elementor-accordion"):
            continue
        elements: list[Tag] = []
        for child in list(body.children):
            if isinstance(child, Tag):
                elements.append(child.extract())
        if not elements:
            continue
        segments: list[tuple] = []
        i = 0
        while i < len(elements):
            if (
                i + 1 < len(elements)
                and elements[i].name == "p"
                and elements[i + 1].name == "ul"
            ):
                segments.append(("pair", elements[i], elements[i + 1]))
                i += 2
            else:
                segments.append(("single", elements[i]))
                i += 1
        if not any(s[0] == "pair" for s in segments):
            for el in elements:
                body.append(el)
            continue
        new_children: list[Tag] = []
        seg_i = 0
        while seg_i < len(segments):
            seg = segments[seg_i]
            if seg[0] == "single":
                new_children.append(seg[1])
                seg_i += 1
                continue
            accordion = soup.new_tag("div", attrs={"class": ["content-accordion"]})
            while seg_i < len(segments) and segments[seg_i][0] == "pair":
                _, p_el, ul_el = segments[seg_i]
                accordion.append(_build_faq_details_from_p_and_ul(soup, p_el, ul_el))
                seg_i += 1
            new_children.append(accordion)
        for node in new_children:
            body.append(node)
    return str(soup)


def _next_element_sibling(tag: Tag) -> Tag | None:
    sib = tag.next_sibling
    while sib is not None and not isinstance(sib, Tag):
        sib = sib.next_sibling
    return sib if isinstance(sib, Tag) else None


def _is_vouchery_cta_paragraph(p: Tag) -> bool:
    """Single-link CTA paragraph (e.g. KUP VOUCHER / PRZEŻYJ) — list conversion stops before it."""
    if p.name != "p":
        return False
    strays = [c for c in p.children if isinstance(c, NavigableString) and str(c).strip()]
    if strays:
        return False
    tags = [c for c in p.children if isinstance(c, Tag)]
    return len(tags) == 1 and tags[0].name == "a"


def _convert_ps_to_vouchery_reasons_ul(soup: BeautifulSoup, h2: Tag) -> None:
    """Turn consecutive <p> blocks after h2 into <ul class='vouchery-reasons-list'> (orange bullet styling)."""
    ps: list[Tag] = []
    sib = _next_element_sibling(h2)
    while sib is not None and sib.name == "p":
        if _is_vouchery_cta_paragraph(sib):
            break
        ps.append(sib)
        sib = _next_element_sibling(sib)
    if not ps:
        return
    ul = soup.new_tag("ul", attrs={"class": ["vouchery-reasons-list"]})
    for p in ps:
        li = soup.new_tag("li")
        for child in list(p.children):
            li.append(child.extract())
        ul.append(li)
        p.decompose()
    h2.insert_after(ul)


def tag_vouchery_reasons_list(html: str) -> str:
    """Tag <ul> or build <ul> from <p> under «5 powodów…» / «Dlaczego voucher…» headings."""
    if not html or not html.strip():
        return html

    soup = BeautifulSoup(html, "html.parser")
    for h2 in soup.find_all("h2"):
        if not isinstance(h2, Tag):
            continue
        t = (h2.get_text() or "").strip().lower()
        if not any(m in t for m in _REASONS_H2_MARKERS):
            continue
        nxt = _next_element_sibling(h2)
        if not nxt:
            continue
        if nxt.name == "ul":
            if "vouchery-products-grid" in (nxt.get("class") or []):
                continue
            existing = nxt.get("class") or []
            if "vouchery-reasons-list" not in existing:
                nxt["class"] = list(existing) + ["vouchery-reasons-list"]
            continue
        if nxt.name == "p":
            _convert_ps_to_vouchery_reasons_ul(soup, h2)
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


# ---------------------------------------------------------------------------
# Themed pages helpers (dla-dzieci, dla-szkol, dla-firm)
# ---------------------------------------------------------------------------

_THEMED_SLUGS: frozenset[str] = frozenset({"dla-dzieci", "dla-szkol", "dla-firm"})


def strip_elementor_residue(html: str) -> str:
    """Remove leftover Elementor widgets that have no semantic value.

    Targets (safe to remove — purely decorative or broken):
    - .premium-title-container (animated letter spans)
    - spacer <div> / <div></div> with no content
    - <a role="button"> without href (dead CTA buttons from Elementor import)
    - empty <span> inside .content-icon-list__icon (icon placeholder)

    Leaves intact:
    - <a href="..."> even if href="#" (CTA stubs to be resolved later)
    - all h1/h2/h3/p/ul/li/video/iframe — SEO-critical nodes
    """
    if not html or not html.strip():
        return html

    soup = BeautifulSoup(html, "html.parser")

    # 1. Remove premium-title-container (animated letter-by-letter spans)
    for el in soup.select(".premium-title-container"):
        el.decompose()

    # 2. Unwrap <a role="button"> without an href (renders as nothing useful)
    for a in soup.find_all("a"):
        if not isinstance(a, Tag):
            continue
        href = (a.get("href") or "").strip()
        role = (a.get("role") or "").strip().lower()
        if role == "button" and not href:
            a.unwrap()

    # 3. Remove spacer <div> elements that have no meaningful content
    for div in soup.find_all("div"):
        if not isinstance(div, Tag):
            continue
        if div.get("class"):
            continue
        text = div.get_text(strip=True)
        if not text and not div.find(["img", "video", "iframe", "picture", "svg"]):
            div.decompose()

    # 4. Remove empty spans inside .content-icon-list__icon (icon placeholders)
    for span in soup.select(".content-icon-list__icon span"):
        if isinstance(span, Tag) and not span.get_text(strip=True) and not span.find(True):
            span.decompose()

    return str(soup)


def extract_media_from_html(html: str) -> tuple[list[dict[str, str]], list[dict[str, str]], str]:
    """Extract all <img>, <video>, and <iframe> from HTML, return them and cleaned HTML.

    Returns:
        (images, videos, cleaned_html)
        images: list of {"src": ..., "alt": ...}
        videos: list of {"video_url": ...} or {"embed_url": ...} (mutually exclusive keys)
    """
    if not html or not html.strip():
        return [], [], html

    soup = BeautifulSoup(html, "html.parser")
    images: list[dict[str, str]] = []
    videos: list[dict[str, str]] = []

    # --- images ---
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
        if parent and isinstance(parent, Tag) and parent.name in ("a", "p", "figure", "div", "li"):
            if not parent.get_text(strip=True) and not parent.find(True):
                parent.decompose()

    # --- videos ---
    for video in soup.find_all("video"):
        if not isinstance(video, Tag):
            continue
        src = (video.get("src") or "").strip()
        if not src:
            source = video.find("source")
            if isinstance(source, Tag):
                src = (source.get("src") or "").strip()
        if src:
            videos.append({"video_url": src})
        parent = video.parent
        video.decompose()
        if parent and isinstance(parent, Tag) and parent.name in ("div", "p", "figure"):
            if not parent.get_text(strip=True) and not parent.find(True):
                parent.decompose()

    # --- iframes (embeds) — only non-biletyna ones counted as gallery media ---
    _BILETYNA_HOSTS = {"biletyna.pl", "biletyna.com"}
    for iframe in soup.find_all("iframe"):
        if not isinstance(iframe, Tag):
            continue
        src = (iframe.get("src") or "").strip()
        if not src:
            continue
        from urllib.parse import urlparse
        host = urlparse(src).netloc.lstrip("www.")
        if host in _BILETYNA_HOSTS:
            continue
        videos.append({"embed_url": src})
        parent = iframe.parent
        iframe.decompose()
        if parent and isinstance(parent, Tag) and parent.name in ("div", "p", "figure"):
            if not parent.get_text(strip=True) and not parent.find(True):
                parent.decompose()

    return images, videos, str(soup)


def split_html_by_h2_into_panels(html: str) -> str:
    """Split flat HTML into stacked event-style panels, each starting at a top-level <h2>.

    Content before the first <h2> → section.event-detail__panel.page-themed__hero-intro
    Each subsequent group starting at <h2> → section.event-detail__panel.event-content-block
                                               > div.event-content-block__body

    The function works on top-level nodes only (same as split_vouchery_content_into_panels).
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
        if node.name == "h2" and current:
            panels.append(current)
            current = [node]
        else:
            current.append(node)
    if current:
        panels.append(current)

    parts: list[str] = []
    for i, panel_nodes in enumerate(panels):
        inner = "".join(str(n) for n in panel_nodes)
        if i == 0:
            parts.append(
                '<section class="event-detail__panel page-themed__hero-intro">'
                f'<div class="page-themed__hero-intro-body">{inner}</div>'
                "</section>"
            )
        else:
            parts.append(
                '<section class="event-detail__panel event-content-block">'
                f'<div class="event-content-block__body">{inner}</div>'
                "</section>"
            )

    return "\n".join(parts) if parts else html


def _h2_opens_vouchery_v2_section(tag: Tag) -> bool:
    if tag.name == "h2":
        t = (tag.get_text() or "").strip().lower()
        return any(m in t for m in VOUCHERY_V2_SECTION_H2_MARKERS)
    # Anonymous wrapper div left by clean_elementor_content (class stripped from elementor-shortcode)
    if tag.name == "div" and not tag.get("class"):
        first_h2 = next(
            (c for c in tag.children if isinstance(c, Tag) and c.name == "h2"),
            None,
        )
        if first_h2 is not None:
            t = (first_h2.get_text() or "").strip().lower()
            return any(m in t for m in VOUCHERY_V2_SECTION_H2_MARKERS)
    return False


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


def transform_dla_dzieci_faq_to_accordion(html: str) -> str:
    """Convert dla-dzieci FAQ section from h3 + p pairs into native <details> accordion.

    Detects the FAQ section by h2 or h3 text containing "najczęściej zadawane" or similar,
    then transforms following h3 (question) + p (answer) pairs into <details> elements.
    """
    if not html or not html.strip():
        return html

    soup = BeautifulSoup(html, "html.parser")
    faq_markers = ("najczęściej zadawane", "frequently asked", "часто задаваемые")

    for section in soup.find_all("section", class_=lambda c: c and "event-content-block" in c):
        if not isinstance(section, Tag):
            continue
        body = section.find("div", class_=lambda c: c and "event-content-block__body" in c)
        if not isinstance(body, Tag):
            continue
        
        # Find FAQ marker (h2 or h3 with "najczęściej zadawane" text)
        h_marker = None
        h_marker_idx = -1
        all_children = [c for c in body.children if isinstance(c, Tag)]
        
        for idx, child in enumerate(all_children):
            if child.name in ("h2", "h3"):
                text = (child.get_text() or "").strip().lower()
                if any(m in text for m in faq_markers):
                    h_marker = child
                    h_marker_idx = idx
                    break
        
        if h_marker_idx == -1:
            continue
        if body.select_one(".content-accordion"):
            continue

        # Collect h3+p pairs after the FAQ marker
        pairs: list[tuple[Tag, Tag]] = []
        i = h_marker_idx + 1
        while i + 1 < len(all_children):
            if all_children[i].name == "h3" and all_children[i + 1].name == "p":
                pairs.append((all_children[i], all_children[i + 1]))
                i += 2
            else:
                i += 1

        if not pairs:
            continue

        # Build accordion
        accordion = soup.new_tag("div", attrs={"class": ["content-accordion"]})
        for h3_el, p_el in pairs:
            details = soup.new_tag("details", attrs={"class": ["content-accordion__item"]})
            summary = soup.new_tag("summary", attrs={"class": ["content-accordion__title"]})
            # Copy h3 content to summary
            for child in list(h3_el.children):
                summary.append(child.extract())
            details.append(summary)
            # Add paragraph as body
            details.append(p_el.extract())
            accordion.append(details)
            h3_el.decompose()

        # Insert accordion after FAQ marker
        h_marker.insert_after(accordion)

    return str(soup)


def replace_city_list_with_select(html: str) -> str:
    """Replace a list of city links at the end of dla-dzieci with a dropdown <select>.

    Finds the last <ul> containing only <li><a>city</a></li> items and converts it
    into a themed <select> element for better mobile UX.
    """
    if not html or not html.strip():
        return html

    soup = BeautifulSoup(html, "html.parser")
    city_uls: list[Tag] = []
    for ul in soup.find_all("ul"):
        if not isinstance(ul, Tag):
            continue
        lis = [c for c in ul.children if isinstance(c, Tag) and c.name == "li"]
        if not lis:
            continue
        all_links = all(
            len([t for t in li.children if isinstance(t, Tag)]) == 1
            and li.find("a") is not None
            for li in lis
        )
        if all_links:
            city_uls.append(ul)

    if not city_uls:
        return html

    last_ul = city_uls[-1]
    cities: list[tuple[str, str]] = []
    for li in last_ul.find_all("li", recursive=False):
        if not isinstance(li, Tag):
            continue
        a = li.find("a")
        if a and isinstance(a, Tag):
            href = a.get("href", "#")
            text = (a.get_text() or "").strip()
            if text:
                cities.append((text, href))

    if not cities:
        return html

    select = soup.new_tag(
        "select",
        attrs={"class": ["dla-dzieci-cities-select"], "data-cities": "true"},
    )
    option_placeholder = soup.new_tag("option", attrs={"value": "", "selected": ""})
    option_placeholder.string = "Wybierz miasto..."
    select.append(option_placeholder)

    for city_name, city_href in cities:
        option = soup.new_tag("option", attrs={"value": city_href})
        option.string = city_name
        select.append(option)

    last_ul.replace_with(select)
    return str(soup)
