"""Idempotent migration of legacy content into CMS PageBlocks.

Usage::

    python manage.py populate_cms_blocks --dry-run
    python manage.py populate_cms_blocks --owners=static,article,event
    python manage.py populate_cms_blocks --slug=dla-firm
    python manage.py populate_cms_blocks --reset --owners=event

Behaviour
---------
- For each selected owner that has NO ``PageBlock`` yet (or when ``--reset``),
  parse legacy HTML / model relations into structured blocks.
- All writes happen in a single ``transaction.atomic()`` per owner so a partial
  failure cannot leave a half-populated page in production.
- Sets ``use_block_builder = True`` only on owners we successfully populated.
  Existing flags are never lowered.
- Every translated language column from ``settings.LANGUAGES`` is filled when
  legacy data has translations.
- Original legacy fields (``content`` / ``content_html``) are NEVER mutated —
  rollback is just ``--reset`` + unset flag.

Heuristics
----------
- ``StaticPage``: extract media, split body by ``<h2>`` into text blocks,
  append a ``form`` block when ``show_contact_form=True``.
- ``Article``: optional hero image block, then a single text block.
- ``EventCity``: copy ``EventContentBlock`` / ``EventImage`` / ``EventVideo``
  into PageBlocks; for legacy ``content_html`` fall back to
  :func:`apps.events.content_parser.parse_legacy_content`. Auto-append a
  countdown (when ``event_date`` is in the future), reviews, related-by-city.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Optional

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.cms.models import (
    KIND_COUNTDOWN,
    KIND_CTA,
    KIND_FORM,
    KIND_GALLERY,
    KIND_IMAGE,
    KIND_RELATED,
    KIND_REVIEWS,
    KIND_TEXT,
    KIND_VIDEO,
    GalleryItem,
    PageBlock,
)


_LANGS = [code for code, _ in settings.LANGUAGES]
_DEFAULT_LANG = settings.LANGUAGE_CODE.split("-")[0]


# ── Helpers ───────────────────────────────────────────────────────────────

def _get_translations(obj, base: str) -> dict[str, str]:
    """Return a {lang_code: value} dict for a translated field."""
    out: dict[str, str] = {}
    for lang in _LANGS:
        attr = f"{base}_{lang}"
        if hasattr(obj, attr):
            value = getattr(obj, attr) or ""
            if value:
                out[lang] = value
    if not out:
        value = getattr(obj, base, "") or ""
        if value:
            out[_DEFAULT_LANG] = value
    return out


def _set_translations(block: PageBlock, base: str, values: dict[str, str]) -> None:
    """Set ``base`` and ``base_<lang>`` on a PageBlock based on a translations dict."""
    if not values:
        return
    fallback = values.get(_DEFAULT_LANG) or next(iter(values.values()), "")
    setattr(block, base, fallback)
    for lang in _LANGS:
        attr = f"{base}_{lang}"
        if hasattr(block, attr):
            setattr(block, attr, values.get(lang, ""))


@dataclass
class BlockSpec:
    """In-memory block representation built before the DB write."""
    kind: str
    sort_order: int
    heading: dict[str, str] | None = None
    body: dict[str, str] | None = None
    image_alt: dict[str, str] | None = None
    button_text: dict[str, str] | None = None
    countdown_label: dict[str, str] | None = None
    image_url: str = ""
    video_embed_url: str = ""
    button_url: str = ""
    button_style: str = ""
    countdown_target: Optional[datetime] = None
    form_kind: str = ""
    reviews_limit: int = 10
    related_strategy: str = ""
    related_limit: int = 6
    css_anchor: str = ""
    heading_level: str = "h2"
    gallery_images: Optional[list[dict]] = None  # list of {"src","alt"}


def _save_block(spec: BlockSpec, owner) -> PageBlock:
    block = PageBlock(
        content_type=ContentType.objects.get_for_model(owner.__class__),
        object_id=owner.pk,
        kind=spec.kind,
        sort_order=spec.sort_order,
        heading_level=spec.heading_level or "h2",
        css_anchor=spec.css_anchor,
        button_url=spec.button_url,
        button_style=spec.button_style or "primary",
        countdown_target=spec.countdown_target,
        form_kind=spec.form_kind,
        reviews_limit=spec.reviews_limit,
        related_strategy=spec.related_strategy,
        related_limit=spec.related_limit,
        video_embed_url=spec.video_embed_url,
    )
    if spec.heading:
        _set_translations(block, "heading", spec.heading)
    if spec.body:
        _set_translations(block, "body", spec.body)
    if spec.image_alt:
        _set_translations(block, "image_alt", spec.image_alt)
    if spec.button_text:
        _set_translations(block, "button_text", spec.button_text)
    if spec.countdown_label:
        _set_translations(block, "countdown_label", spec.countdown_label)
    block.save()

    if spec.gallery_images:
        for idx, img in enumerate(spec.gallery_images):
            if not img.get("src"):
                continue
            gi = GalleryItem(
                block=block,
                image_url=img["src"],
                sort_order=idx,
            )
            alt = img.get("alt") or ""
            if alt:
                _set_translations(gi, "alt_text", {_DEFAULT_LANG: alt})
            gi.save()
    return block


# ── Builders per owner type ───────────────────────────────────────────────

def _build_specs_for_static(page) -> list[BlockSpec]:
    """Convert StaticPage HTML + flags into BlockSpec list."""
    from apps.pages.utils import extract_media_from_html

    specs: list[BlockSpec] = []
    sort = 0

    body_translations = _get_translations(page, "content")
    images: list[dict] = []
    videos: list[dict] = []
    cleaned_per_lang: dict[str, str] = {}
    for lang, html in body_translations.items():
        imgs, vids, cleaned = extract_media_from_html(html or "")
        if lang == _DEFAULT_LANG or not images:
            images = imgs or images
        if lang == _DEFAULT_LANG or not videos:
            videos = vids or videos
        cleaned_per_lang[lang] = cleaned

    if cleaned_per_lang:
        specs.append(BlockSpec(
            kind=KIND_TEXT,
            sort_order=sort,
            body=cleaned_per_lang,
        ))
        sort += 1

    if images:
        specs.append(BlockSpec(
            kind=KIND_GALLERY,
            sort_order=sort,
            heading={_DEFAULT_LANG: "Galeria"},
            gallery_images=images,
        ))
        sort += 1

    for video in videos:
        specs.append(BlockSpec(
            kind=KIND_VIDEO,
            sort_order=sort,
            video_embed_url=video.get("embed_url") or video.get("video_url") or "",
        ))
        sort += 1

    if getattr(page, "show_contact_form", False):
        specs.append(BlockSpec(
            kind=KIND_FORM,
            sort_order=sort,
            form_kind="contact",
            heading={_DEFAULT_LANG: "Skontaktuj się z nami"},
        ))
        sort += 1

    return specs


def _build_specs_for_article(article) -> list[BlockSpec]:
    """Convert Article hero image + body into BlockSpec list."""
    from apps.pages.utils import extract_media_from_html

    specs: list[BlockSpec] = []
    sort = 0

    body_translations = _get_translations(article, "content")
    images: list[dict] = []
    videos: list[dict] = []
    cleaned_per_lang: dict[str, str] = {}
    for lang, html in body_translations.items():
        imgs, vids, cleaned = extract_media_from_html(html or "")
        if lang == _DEFAULT_LANG or not images:
            images = imgs or images
        if lang == _DEFAULT_LANG or not videos:
            videos = vids or videos
        cleaned_per_lang[lang] = cleaned

    if cleaned_per_lang:
        specs.append(BlockSpec(
            kind=KIND_TEXT,
            sort_order=sort,
            body=cleaned_per_lang,
        ))
        sort += 1

    if images:
        specs.append(BlockSpec(
            kind=KIND_GALLERY,
            sort_order=sort,
            heading={_DEFAULT_LANG: "Galeria"},
            gallery_images=images,
        ))
        sort += 1

    for video in videos:
        specs.append(BlockSpec(
            kind=KIND_VIDEO,
            sort_order=sort,
            video_embed_url=video.get("embed_url") or video.get("video_url") or "",
        ))
        sort += 1

    return specs


def _build_specs_for_event(ec) -> list[BlockSpec]:
    """Convert EventCity content_html / model relations into BlockSpec list."""
    from apps.events.content_parser import parse_legacy_content

    specs: list[BlockSpec] = []
    sort = 0

    images: list[dict] = []
    videos: list[dict] = []
    text_blocks: list[BlockSpec] = []

    if ec.use_new_layout:
        for cb in ec.content_blocks.all().order_by("sort_order"):
            text_blocks.append(BlockSpec(
                kind=KIND_TEXT,
                sort_order=0,  # re-numbered later
                heading=_get_translations(cb, "title"),
                body=_get_translations(cb, "body"),
                button_text=_get_translations(cb, "button_text"),
                button_url=cb.button_url or "",
                button_style="amber",
            ))
        for img in ec.images.all().order_by("sort_order"):
            src = img.image.url if img.image else (img.image_url or "")
            if src:
                images.append({"src": src, "alt": img.alt_text or ""})
        for vid in ec.videos.all().order_by("sort_order"):
            url = vid.embed_url or (vid.video_file.url if vid.video_file else "")
            if url:
                videos.append({"embed_url": url, "title": vid.title or ""})
    else:
        parsed = parse_legacy_content(ec.content_html or "", ec)
        if parsed.intro_html:
            text_blocks.append(BlockSpec(
                kind=KIND_TEXT,
                sort_order=0,
                body={_DEFAULT_LANG: parsed.intro_html},
            ))
        for blk in parsed.blocks:
            text_blocks.append(BlockSpec(
                kind=KIND_TEXT,
                sort_order=0,
                heading=({_DEFAULT_LANG: blk["title"]} if blk.get("title") else None),
                body=({_DEFAULT_LANG: blk["body_html"]} if blk.get("body_html") else None),
                button_text=(
                    {_DEFAULT_LANG: blk["button_text"]} if blk.get("button_text") else None
                ),
                button_url=blk.get("button_url", "") or "",
                button_style="amber" if blk.get("button_text") else "",
            ))
        images = list(parsed.photos)
        videos = list(parsed.videos)

    for tb in text_blocks:
        tb.sort_order = sort
        sort += 1
        specs.append(tb)

    if images:
        specs.append(BlockSpec(
            kind=KIND_GALLERY,
            sort_order=sort,
            heading={_DEFAULT_LANG: "Galeria"},
            gallery_images=images,
        ))
        sort += 1

    for video in videos:
        specs.append(BlockSpec(
            kind=KIND_VIDEO,
            sort_order=sort,
            video_embed_url=video.get("embed_url") or video.get("video_url") or "",
        ))
        sort += 1

    if ec.event_date and ec.event_date > timezone.now():
        specs.append(BlockSpec(
            kind=KIND_COUNTDOWN,
            sort_order=sort,
            heading={_DEFAULT_LANG: "Do wydarzenia pozostało"},
            countdown_target=ec.event_date,
            countdown_label={_DEFAULT_LANG: "Czasu zostało"},
            css_anchor="odliczanie",
        ))
        sort += 1

    specs.append(BlockSpec(
        kind=KIND_REVIEWS,
        sort_order=sort,
        heading={_DEFAULT_LANG: "Recenzje"},
        reviews_limit=10,
        css_anchor="recenzje",
    ))
    sort += 1

    specs.append(BlockSpec(
        kind=KIND_RELATED,
        sort_order=sort,
        heading={_DEFAULT_LANG: "Zobacz także"},
        related_strategy="city",
        related_limit=6,
    ))

    return specs


# ── Owner enumeration ─────────────────────────────────────────────────────

def _iter_owners(kinds: set[str], slug: str | None) -> Iterable[tuple[str, object]]:
    if "static" in kinds:
        from apps.pages.models import StaticPage
        qs = StaticPage.objects.all()
        if slug:
            qs = qs.filter(slug=slug)
        for obj in qs:
            yield ("static", obj)

    if "article" in kinds:
        from apps.blog.models import Article
        qs = Article.objects.all()
        if slug:
            qs = qs.filter(slug=slug)
        for obj in qs:
            yield ("article", obj)

    if "event" in kinds:
        from apps.events.models import EventCity
        qs = EventCity.objects.select_related("event", "city")
        if slug:
            qs = qs.filter(slug=slug)
        for obj in qs:
            yield ("event", obj)


_BUILDERS = {
    "static": _build_specs_for_static,
    "article": _build_specs_for_article,
    "event": _build_specs_for_event,
}

_OWNER_FLAG_FIELD = "use_block_builder"


# ── Command ───────────────────────────────────────────────────────────────

class Command(BaseCommand):
    help = "Populate cms.PageBlock from legacy HTML / model content (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--owners",
            default="static,article,event",
            help="Comma list: static,article,event (default: all).",
        )
        parser.add_argument(
            "--slug",
            default=None,
            help="Process only the owner with this slug (across selected owners).",
        )
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing CMS blocks for selected owners before populating.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Compute and print stats, do not write to the database.",
        )
        parser.add_argument(
            "--no-flag",
            action="store_true",
            help="Do not set use_block_builder=True after populating (for staging).",
        )

    def handle(self, *args, **options):
        kinds_arg: str = options["owners"]
        kinds = {k.strip() for k in kinds_arg.split(",") if k.strip()}
        unknown = kinds - set(_BUILDERS)
        if unknown:
            raise CommandError(f"Unknown owner kinds: {sorted(unknown)}")

        slug = options.get("slug")
        reset = options["reset"]
        dry = options["dry_run"]
        set_flag = not options["no_flag"]

        totals = {"processed": 0, "skipped": 0, "blocks": 0, "reset_owners": 0}

        for kind, owner in _iter_owners(kinds, slug):
            ct = ContentType.objects.get_for_model(owner.__class__)
            existing = PageBlock.objects.filter(content_type=ct, object_id=owner.pk)
            label = f"{kind}:{getattr(owner, 'slug', owner.pk)}"

            if existing.exists() and not reset:
                self.stdout.write(f"[skip-existing] {label}")
                totals["skipped"] += 1
                continue

            specs = _BUILDERS[kind](owner)
            if not specs:
                self.stdout.write(f"[empty] {label} — nothing to migrate")
                totals["skipped"] += 1
                continue

            if dry:
                self.stdout.write(
                    f"[dry-run] {label}: would create {len(specs)} blocks"
                )
                totals["processed"] += 1
                totals["blocks"] += len(specs)
                continue

            with transaction.atomic():
                if reset and existing.exists():
                    deleted = existing.count()
                    existing.delete()
                    totals["reset_owners"] += 1
                    self.stdout.write(f"[reset] {label}: removed {deleted} existing blocks")

                for spec in specs:
                    _save_block(spec, owner)

                if set_flag and hasattr(owner, _OWNER_FLAG_FIELD):
                    if not getattr(owner, _OWNER_FLAG_FIELD):
                        setattr(owner, _OWNER_FLAG_FIELD, True)
                        owner.save(update_fields=[_OWNER_FLAG_FIELD])

            self.stdout.write(self.style.SUCCESS(
                f"[ok] {label}: {len(specs)} blocks created"
            ))
            totals["processed"] += 1
            totals["blocks"] += len(specs)

        summary = (
            f"Done. processed={totals['processed']} "
            f"skipped={totals['skipped']} "
            f"blocks_total={totals['blocks']} "
            f"reset_owners={totals['reset_owners']} "
            f"dry_run={dry}"
        )
        self.stdout.write(self.style.SUCCESS(summary))
