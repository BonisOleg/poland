"""
Runtime parser: turns legacy Elementor/WP `EventCity.content_html` into the same
structured shape used by the new layout (photos / videos / blocks / intro_html).

Pure function, no DB writes. Idempotent — re-running on the same HTML returns
equivalent output. Keeps SEO-relevant markup (H2/H3/paragraphs/lists) untouched;
only Elementor cruft, duplicate CTAs, swiper chrome and the "REKOMENDACJE"
carousel are removed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup, NavigableString, Tag

from apps.pages.management.commands.clean_elementor_content import transform_html

if TYPE_CHECKING:
    from .models import EventCity


# ── constants ─────────────────────────────────────────────────────────────

# Anchor text fragments for CTA links that duplicate the hero "Kup bilet" button
_CTA_DUPLICATE_PATTERNS = re.compile(
    r"^\s*(kup\s+bilet|sprawd[źz]\s+miejsca|zapytaj\s+o\s+szczeg[óo]|zapytaj\s+o\s+ofert[ęe])",
    re.IGNORECASE,
)

# Headings whose sole role is to announce a carousel we already render differently
_DROP_HEADINGS = {"galeria", "galeria zdjęć", "rekomendacje", "galerіa"}

# Bullet markers that WP/Elementor inlines inside <h3>
_BULLET_PREFIX = re.compile(r"^[•●▪◼■◆♦►]\s*")

# Space normalisation for heading-duplicate detection
_WS = re.compile(r"\s+")

# Regex to strip "-1024x576" style WP size suffix for deduplication
_WP_SIZE_SUFFIX = re.compile(r"-\d{2,4}x\d{2,4}(?=\.(?:jpe?g|png|webp|gif|avif)(?:$|\?))", re.IGNORECASE)

# Block-level tags whose presence makes a wrapper "meaningful" when trimming empties
_MEANINGFUL_TAGS = {
    "img", "video", "iframe", "source", "svg", "ul", "ol", "li", "p",
    "h1", "h2", "h3", "h4", "h5", "h6", "blockquote", "pre", "table",
    "figure", "a", "strong", "em",
}

# SEO-sensitive attributes we strip from every node we keep
_STRIP_ATTRS = ("style", "onclick", "onload", "onerror", "onmouseover", "onfocus")


# ── public API ────────────────────────────────────────────────────────────

@dataclass
class ParsedContent:
    intro_html: str = ""
    photos: list[dict] = field(default_factory=list)
    videos: list[dict] = field(default_factory=list)
    blocks: list[dict] = field(default_factory=list)


def parse_legacy_content(html: str, ec: "EventCity | None" = None) -> ParsedContent:
    """Parse legacy Elementor/WP HTML into structured sections.

    `ec` is optional — used only to detect duplicate title/date/venue headings
    and duplicate Kup-bilet CTAs (we already render them via hero + modal).
    """
    if not html or not html.strip():
        return ParsedContent()

    pre = transform_html(html)
    soup = BeautifulSoup(pre or "", "html.parser")

    _strip_scripts_and_styles(soup)
    _strip_dangerous_attrs(soup)
    _unwrap_title_letter_soup(soup)

    photos: list[dict] = []
    videos: list[dict] = []

    _extract_and_drop_rekomendacje(soup)
    _extract_videos(soup, videos)
    _extract_swiper_galleries(soup, photos)
    _extract_wp_gallery_columns(soup, photos)
    _extract_premium_banner_images(soup, photos)
    _drop_duplicate_headings(soup, ec)
    _drop_duplicate_ctas(soup, ec)
    _drop_empty_nav_buttons(soup)
    _drop_elementor_chevron_svgs(soup)
    _bullet_h3_to_ul(soup)
    _drop_orphan_images(soup)
    _drop_empty_containers(soup)

    photos = _dedupe_photos(photos, ec)
    videos = _dedupe_videos(videos)

    intro_html, blocks = _segment_into_blocks(soup)
    return ParsedContent(intro_html=intro_html, photos=photos, videos=videos, blocks=blocks)


def build_detail_sections(ec: "EventCity") -> ParsedContent:
    """Return ParsedContent regardless of which layout the EventCity uses.

    For `use_new_layout=True` we read model relations; otherwise we parse
    `content_html`. If the event-city has no media of its own we fall back
    to the first sibling EventCity (same Event) that does, so events like
    a concert tour share gallery/video assets city-to-city even when one
    city's import was truncated.
    """
    parsed, model_blocks = _collect_sections(ec)

    if not parsed.photos or not parsed.videos:
        for sibling in _iter_siblings(ec):
            sib_photos, sib_videos = _collect_media(sibling)
            if not parsed.photos and sib_photos:
                parsed.photos = sib_photos
            if not parsed.videos and sib_videos:
                parsed.videos = sib_videos
            if parsed.photos and parsed.videos:
                break

    parsed.blocks = parsed.blocks + model_blocks
    return parsed


def _collect_sections(ec: "EventCity") -> tuple[ParsedContent, list[dict]]:
    """Build ParsedContent from the event-city's own data (content_html + model
    relations). Content blocks from the model are returned separately so the
    caller can append them after any sibling-media fallback logic."""
    model_photos, model_videos = _model_media(ec)
    model_blocks = _model_blocks(ec)

    if ec.use_new_layout:
        return (
            ParsedContent(
                intro_html="",
                photos=model_photos,
                videos=model_videos,
                blocks=[],
            ),
            model_blocks,
        )

    parsed = parse_legacy_content(ec.content_html or "", ec)
    parsed.photos = _dedupe_photos(parsed.photos + model_photos, ec)
    parsed.videos = _dedupe_videos(parsed.videos + model_videos)
    return parsed, model_blocks


def _collect_media(ec: "EventCity") -> tuple[list[dict], list[dict]]:
    """Return (photos, videos) only — used for sibling fallback. Ignores blocks
    and intro_html: sibling text stays local to that city for SEO relevance."""
    model_photos, model_videos = _model_media(ec)
    if ec.use_new_layout:
        return model_photos, model_videos
    parsed = parse_legacy_content(ec.content_html or "", ec)
    photos = _dedupe_photos(parsed.photos + model_photos, ec)
    videos = _dedupe_videos(parsed.videos + model_videos)
    return photos, videos


def _iter_siblings(ec: "EventCity"):
    """Up to 20 published sibling EventCity objects of the same Event."""
    if not ec.event_id:
        return []
    return (
        ec.__class__.objects.filter(event_id=ec.event_id, is_published=True)
        .exclude(pk=ec.pk)
        .select_related("event", "city", "venue")
        .prefetch_related("images", "videos")[:20]
    )


def _model_media(ec: "EventCity") -> tuple[list[dict], list[dict]]:
    photos = [
        {"src": p.src, "alt": p.alt_text or ec.get_display_title()}
        for p in ec.images.all()
        if p.src
    ]
    videos = [
        {
            "embed_url": v.embed_url or "",
            "video_url": v.video_file.url if v.video_file else "",
            "title": v.title or ec.get_display_title(),
        }
        for v in ec.videos.all()
        if v.embed_url or v.video_file
    ]
    return photos, videos


def _model_blocks(ec: "EventCity") -> list[dict]:
    return [
        {
            "title": b.title,
            "body_html": b.body or "",
            "button_text": b.button_text,
            "button_url": b.button_url,
        }
        for b in ec.content_blocks.all()
    ]


# ── passes ────────────────────────────────────────────────────────────────

def _strip_scripts_and_styles(soup: BeautifulSoup) -> None:
    for tag in soup.find_all(["script", "style", "noscript"]):
        tag.decompose()


def _strip_dangerous_attrs(soup: BeautifulSoup) -> None:
    for tag in soup.find_all(True):
        if not isinstance(tag, Tag):
            continue
        for attr in _STRIP_ATTRS:
            if attr in tag.attrs:
                del tag.attrs[attr]


def _unwrap_title_letter_soup(soup: BeautifulSoup) -> None:
    """Collapse premium-title-style9 <span data-letter="X">X</span> soup into plain text."""
    for container in list(soup.select(".premium-title-container, .premium-title-header")):
        text = container.get_text(" ", strip=True)
        if not text:
            container.decompose()
            continue
        replacement = soup.new_tag("h3", attrs={"class": "event-content-block__hint"})
        replacement.string = text
        container.replace_with(replacement)


def _extract_and_drop_rekomendacje(soup: BeautifulSoup) -> None:
    """Remove the legacy 'REKOMENDACJE' Elementor block — related events
    are rendered via the template's own 'Zobacz także' section."""
    for heading in list(soup.find_all(["h2", "h3"])):
        text = heading.get_text(" ", strip=True).lower().strip("\u200b \t\n")
        if not text:
            continue
        if "rekomendacje" not in text:
            continue
        # Remove following swiper/carousel siblings up to next heading
        sib = heading.next_sibling
        heading.decompose()
        while sib is not None:
            current = sib
            sib = current.next_sibling
            if not isinstance(current, Tag):
                if isinstance(current, NavigableString) and not str(current).strip():
                    continue
                continue
            if current.name in {"h1", "h2", "h3"}:
                break
            current.decompose()


def _extract_videos(soup: BeautifulSoup, videos: list[dict]) -> None:
    for vid in list(soup.find_all("video")):
        src = (vid.get("src") or "").strip()
        if not src:
            source = vid.find("source")
            if source and source.get("src"):
                src = source["src"].strip()
        title = (vid.get("title") or vid.get("data-title") or "").strip()
        if src:
            videos.append({"embed_url": "", "video_url": src, "title": title})
        vid.decompose()

    for frame in list(soup.find_all("iframe")):
        src = (frame.get("src") or "").strip()
        if not src:
            frame.decompose()
            continue
        if _looks_like_ticket_iframe(src):
            frame.decompose()
            continue
        title = (frame.get("title") or "").strip()
        videos.append({"embed_url": src, "video_url": "", "title": title})
        frame.decompose()


def _looks_like_ticket_iframe(url: str) -> bool:
    host = url.lower()
    return "biletyna" in host or "ticket" in host


def _extract_swiper_galleries(soup: BeautifulSoup, photos: list[dict]) -> None:
    """Capture <img> inside Elementor/Swiper carousels, then remove the carousel."""
    for carousel in list(soup.select("div.swiper, .swiper-wrapper")):
        for img in carousel.find_all("img"):
            src = _image_src(img)
            if not src:
                continue
            photos.append({"src": src, "alt": (img.get("alt") or "").strip()})
        # Drop preceding heading if it only says "Galeria"
        prev = carousel.find_previous_sibling()
        if isinstance(prev, Tag) and prev.name in {"h2", "h3"}:
            if prev.get_text(" ", strip=True).lower() in _DROP_HEADINGS:
                prev.decompose()
        carousel.decompose()


def _extract_wp_gallery_columns(soup: BeautifulSoup, photos: list[dict]) -> None:
    """Extract images from WordPress gallery shortcode blocks
    (`<div class="gallery galleryid-... gallery-columns-...">`) and remove the block.

    WP renders each item as:
        <figure class="gallery-item">
          <div class="gallery-icon">
            <a href="full-size.jpg"><img src="thumb.jpg" alt="..."></a>
          </div>
        </figure>

    We prefer the `href` (full-resolution) over `src` (thumbnail).
    """
    for gallery in list(soup.select("div[class*='gallery-columns']")):
        for item in gallery.select(".gallery-item"):
            anchor = item.find("a")
            img = item.find("img")
            if not img:
                continue
            # Prefer the anchor href (full image) over the thumbnail src
            href = (anchor.get("href") or "").strip() if anchor else ""
            src = href if href and not href.startswith("#") else _image_src(img)
            if not src:
                continue
            photos.append({"src": src, "alt": (img.get("alt") or "").strip()})

        # Drop a preceding "Galeria" heading
        prev = gallery.find_previous_sibling()
        # The WP gallery is sometimes wrapped in an extra <div> inserted by transform_html
        parent = gallery.parent
        if isinstance(parent, Tag) and parent.name == "div" and not parent.get("class"):
            actual_prev = parent.find_previous_sibling()
            if isinstance(actual_prev, Tag) and actual_prev.name in {"h2", "h3"}:
                if actual_prev.get_text(" ", strip=True).lower().strip() in _DROP_HEADINGS:
                    actual_prev.decompose()
            parent.decompose()
        else:
            if isinstance(prev, Tag) and prev.name in {"h2", "h3"}:
                if prev.get_text(" ", strip=True).lower().strip() in _DROP_HEADINGS:
                    prev.decompose()
            gallery.decompose()


def _extract_premium_banner_images(soup: BeautifulSoup, photos: list[dict]) -> None:
    """Premium-banner images are decorative promo frames with accompanying text.
    We clean up Elementor-specific attributes/classes, then simply unwrap the
    banner container so the image and caption text become siblings inside the
    parent content block — no wrapping <figure> that would clip the text via
    max-height/overflow."""
    for banner in list(soup.select(".premium-banner-ib")):
        for tag in banner.find_all(True):
            if not isinstance(tag, Tag):
                continue
            for attr in list(tag.attrs):
                if attr.startswith("data-") or attr in {
                    "decoding", "loading", "fetchpriority", "srcset", "sizes",
                }:
                    del tag.attrs[attr]
        # Flatten desc wrappers
        for desc in banner.select(".premium-banner-ib-desc, .premium-banner-ib-content"):
            desc.unwrap()
        # Drop Elementor-specific class names from title elements
        for el in banner.select(".premium-banner-ib-title, .premium_banner_title"):
            _set_class(el, None)
        # Unwrap the banner container itself — children become siblings in the
        # parent block, so CSS max-height/overflow on .event-content-block__figure
        # (which no longer wraps them) cannot clip the caption text.
        banner.unwrap()


def _drop_duplicate_headings(soup: BeautifulSoup, ec: "EventCity | None") -> None:
    if ec is None:
        return
    # Build a set of normalized strings that are already shown in hero/meta
    skip: set[str] = set()
    if ec.event_id:
        skip.add(_norm(ec.event.title))
    skip.add(_norm(ec.get_display_title()))
    if ec.custom_title:
        skip.add(_norm(ec.custom_title))
    if ec.event_date:
        skip.add(_norm(ec.event_date.strftime("%d.%m.%Y")))
        skip.add(_norm(ec.event_date.strftime("%d.%m.%Y, %H:%M")))
        skip.add(_norm(ec.event_date.strftime("%-d %B %Y").lower()))
        skip.add(_norm(f"{ec.event_date.strftime('%-d %B %Y')}r. w {ec.city.name}"))
    if ec.city_id:
        skip.add(_norm(ec.city.name))
    if ec.venue_id and ec.venue:
        skip.add(_norm(ec.venue.name))
    # Common Elementor-rendered city-date headings: "<day month> - <city>"
    date_city_pattern = re.compile(r"^\d{1,2}\s+\w+\s*[-–—]\s*\S", re.IGNORECASE)

    for heading in list(soup.find_all(["h1", "h2"])):
        text = _norm(heading.get_text(" ", strip=True))
        if not text:
            heading.decompose()
            continue
        if text in skip:
            heading.decompose()
            continue
        if date_city_pattern.match(text) and ec.city and _norm(ec.city.name) in text:
            heading.decompose()


def _drop_duplicate_ctas(soup: BeautifulSoup, ec: "EventCity | None") -> None:
    biletyna = (ec.biletyna_url.strip() if ec and ec.biletyna_url else "")
    for anchor in list(soup.find_all("a")):
        text = _norm(anchor.get_text(" ", strip=True))
        href = (anchor.get("href") or "").strip()
        if not text and not anchor.find("img"):
            anchor.decompose()
            continue
        if _CTA_DUPLICATE_PATTERNS.match(text or ""):
            anchor.decompose()
            continue
        if biletyna and href == biletyna:
            anchor.decompose()
            continue
        if href == "" and not anchor.find("img"):
            anchor.decompose()


def _drop_empty_nav_buttons(soup: BeautifulSoup) -> None:
    # <div role="button" tabindex="0">…SVG chevron…</div>
    for el in list(soup.find_all(attrs={"role": "button"})):
        if isinstance(el, Tag) and not el.get_text(" ", strip=True) and not el.find("img"):
            el.decompose()


def _drop_elementor_chevron_svgs(soup: BeautifulSoup) -> None:
    for svg in list(soup.find_all("svg")):
        classes = " ".join(svg.get("class") or []).lower()
        if "eicon-chevron" in classes or "chevron-left" in classes or "chevron-right" in classes:
            svg.decompose()
            continue
        # Bare SVGs inside content-icon-list__icon have already been stripped by
        # transform_html; orphan SVGs that remain usually are empty decoration.
        if not svg.get_text(" ", strip=True) and not svg.find(["image", "path", "circle", "rect"]):
            svg.decompose()


def _bullet_h3_to_ul(soup: BeautifulSoup) -> None:
    """Runs of '● text' H3 headings → a single semantic <ul class="content-icon-list">."""
    nodes = list(soup.find_all("h3"))
    i = 0
    while i < len(nodes):
        h3 = nodes[i]
        if h3.parent is None:
            i += 1
            continue
        txt = h3.get_text(" ", strip=True)
        if not _BULLET_PREFIX.match(txt):
            i += 1
            continue
        # Collect consecutive siblings that are bullet-h3s
        group = [h3]
        sib = h3.find_next_sibling()
        while sib is not None and isinstance(sib, Tag) and sib.name == "h3":
            if _BULLET_PREFIX.match(sib.get_text(" ", strip=True)):
                group.append(sib)
                sib = sib.find_next_sibling()
            else:
                break
        ul = soup.new_tag("ul", attrs={"class": "content-icon-list"})
        for node in group:
            li = soup.new_tag("li", attrs={"class": "content-icon-list__item"})
            icon = soup.new_tag("span", attrs={"class": "content-icon-list__icon"})
            text_span = soup.new_tag("span", attrs={"class": "content-icon-list__text"})
            text_span.string = _BULLET_PREFIX.sub("", node.get_text(" ", strip=True))
            li.append(icon)
            li.append(text_span)
            ul.append(li)
        h3.replace_with(ul)
        for extra in group[1:]:
            extra.decompose()
        # refresh headings list index
        nodes = list(soup.find_all("h3"))
        i = 0


def _drop_orphan_images(soup: BeautifulSoup) -> None:
    """Remove <img> tags that have no URL source — they render nothing useful
    and would otherwise leak their `alt` text into content blocks (happens on
    events with a truncated WP import, e.g. sn-gdansk)."""
    for img in list(soup.find_all("img")):
        if not isinstance(img, Tag):
            continue
        if _image_src(img):
            continue
        img.decompose()


def _drop_empty_containers(soup: BeautifulSoup) -> None:
    """Remove <div>/<span> wrappers that carry no meaningful child."""
    changed = True
    while changed:
        changed = False
        for tag in list(soup.find_all(["div", "span", "section", "p"])):
            if not isinstance(tag, Tag):
                continue
            if tag.find(list(_MEANINGFUL_TAGS)):
                continue
            if tag.get_text(" ", strip=True):
                continue
            tag.decompose()
            changed = True


# ── segmentation ──────────────────────────────────────────────────────────

def _segment_into_blocks(soup: BeautifulSoup) -> tuple[str, list[dict]]:
    """Split remaining top-level nodes by <h2> into (intro_html, blocks[])."""
    top_children = [c for c in soup.contents if isinstance(c, (Tag, NavigableString))]
    # If soup has no <body>, iterate direct children of soup
    body = soup.body if soup.body else None
    source = body.contents if body else top_children

    intro_parts: list[str] = []
    blocks: list[dict] = []
    current: dict | None = None

    for node in list(source):
        if isinstance(node, NavigableString):
            if current is None:
                intro_parts.append(str(node))
            else:
                current["body_parts"].append(str(node))
            continue
        if not isinstance(node, Tag):
            continue
        if node.name == "h2":
            if current is not None:
                blocks.append(_finalize_block(current))
            current = {
                "title": node.get_text(" ", strip=True),
                "body_parts": [],
                "button_text": "",
                "button_url": "",
            }
            continue
        if current is None:
            intro_parts.append(str(node))
        else:
            current["body_parts"].append(str(node))

    if current is not None:
        blocks.append(_finalize_block(current))

    intro_html = _compact("".join(intro_parts))
    blocks = _drop_empty_blocks(blocks)
    return intro_html, blocks


def _drop_empty_blocks(blocks: list[dict]) -> list[dict]:
    """Remove decorative title-only `<h2>` blocks (no body, no CTA)."""
    return [b for b in blocks if (b["body_html"] or b["button_url"])]


def _finalize_block(draft: dict) -> dict:
    body_html = _compact("".join(draft["body_parts"]))
    button_text = ""
    button_url = ""
    # Detect trailing standalone anchor (styled as CTA)
    bs = BeautifulSoup(body_html, "html.parser")
    last = None
    for child in bs.contents:
        if isinstance(child, Tag):
            last = child
    if last is not None and last.name == "a" and last.get("href"):
        button_text = last.get_text(" ", strip=True)
        button_url = last["href"].strip()
        last.decompose()
        body_html = _compact(str(bs))
    return {
        "title": draft["title"],
        "body_html": body_html,
        "button_text": button_text,
        "button_url": button_url,
    }


# ── helpers ───────────────────────────────────────────────────────────────

def _image_src(img: Tag) -> str:
    for attr in ("data-src", "data-lazy-src", "src"):
        val = (img.get(attr) or "").strip()
        if val and not val.startswith("data:"):
            return val
    return ""


def _dedupe_photos(photos: list[dict], ec: "EventCity | None") -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    fallback_alt = ec.get_display_title() if ec else ""
    for p in photos:
        src = p.get("src", "").strip()
        if not src:
            continue
        key = _WP_SIZE_SUFFIX.sub("", src.split("?")[0].lower())
        if key in seen:
            continue
        seen.add(key)
        out.append({"src": src, "alt": p.get("alt") or fallback_alt})
    return out


def _dedupe_videos(videos: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for v in videos:
        key = (v.get("embed_url") or v.get("video_url") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out


def _set_class(tag: Tag, classes: list[str] | None) -> None:
    if classes:
        tag["class"] = classes
    else:
        tag.attrs.pop("class", None)


def _norm(text: str) -> str:
    return _WS.sub(" ", (text or "").strip().lower())


def _compact(html: str) -> str:
    out = re.sub(r"\n{3,}", "\n\n", html or "")
    out = re.sub(r"[ \t]+\n", "\n", out)
    return out.strip()
