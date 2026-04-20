"""Unified CMS page builder models.

A single :class:`PageBlock` model attached to any owner via GenericForeignKey
(StaticPage, Article, EventCity) — driven by ``kind`` discriminator. Per-kind
typed columns are nullable; only the relevant subset is populated.

Heavy multi-row data (gallery items, manually picked related pages) lives in
:class:`GalleryItem` / :class:`RelatedItem` to keep PageBlock flat.
"""

from __future__ import annotations

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill

from apps.core.labels import pl_uk


KIND_TEXT = "text"
KIND_IMAGE = "image"
KIND_GALLERY = "gallery"
KIND_VIDEO = "video"
KIND_FORM = "form"
KIND_COUNTDOWN = "countdown"
KIND_REVIEWS = "reviews"
KIND_RELATED = "related"
KIND_CTA = "cta"
KIND_HTML = "html"

KIND_CHOICES = [
    (KIND_TEXT, pl_uk("Tekst / Nagłówek", "Текст / Заголовок")),
    (KIND_IMAGE, pl_uk("Pojedynczy obraz", "Окреме зображення")),
    (KIND_GALLERY, pl_uk("Galeria", "Галерея")),
    (KIND_VIDEO, pl_uk("Wideo", "Відео")),
    (KIND_FORM, pl_uk("Formularz", "Форма")),
    (KIND_COUNTDOWN, pl_uk("Timer odliczania", "Таймер зворотного відліку")),
    (KIND_REVIEWS, pl_uk("Opinie", "Відгуки")),
    (KIND_RELATED, pl_uk("Zobacz także", "Дивіться також")),
    (KIND_CTA, pl_uk("Przycisk / Banner", "Кнопка / Банер")),
    (KIND_HTML, pl_uk("Surowy HTML (legacy)", "Сирий HTML (legacy)")),
]

HEADING_LEVEL_CHOICES = [
    ("h2", "H2"),
    ("h3", "H3"),
    ("h4", "H4"),
]

BUTTON_STYLE_CHOICES = [
    ("primary", pl_uk("Primary", "Основна")),
    ("outline", pl_uk("Outline", "Контур")),
    ("amber", pl_uk("Amber", "Янтарна")),
]

FORM_KIND_CHOICES = [
    ("contact", pl_uk("Formularz kontaktowy", "Контактна форма")),
    ("group", pl_uk("Zgłoszenie grupowe", "Групова заявка")),
]

RELATED_STRATEGY_CHOICES = [
    ("manual", pl_uk("Ręcznie wybrane", "Вибрано вручну")),
    ("city", pl_uk("Według miasta (event)", "За містом (подія)")),
    ("category", pl_uk("Według kategorii (event)", "За категорією (подія)")),
]


def _allowed_owner_models() -> models.Q:
    """Limit GFK target ContentTypes to the three CMS-owner models."""
    return (
        models.Q(app_label="pages", model="staticpage")
        | models.Q(app_label="blog", model="article")
        | models.Q(app_label="events", model="eventcity")
    )


class PageBlock(models.Model):
    """Single block attached to a CMS-owner via GenericForeignKey."""

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=_allowed_owner_models,
        verbose_name=pl_uk("Typ właściciela", "Тип власника"),
    )
    object_id = models.PositiveIntegerField(verbose_name=pl_uk("ID właściciela", "ID власника"))
    owner = GenericForeignKey("content_type", "object_id")

    kind = models.CharField(
        max_length=20,
        choices=KIND_CHOICES,
        db_index=True,
        verbose_name=pl_uk("Rodzaj bloku", "Тип блоку"),
    )
    sort_order = models.IntegerField(
        default=0, db_index=True, verbose_name=pl_uk("Kolejność", "Порядок")
    )
    is_visible = models.BooleanField(
        default=True, verbose_name=pl_uk("Widoczny", "Видимий")
    )
    css_anchor = models.SlugField(
        max_length=80,
        blank=True,
        help_text=pl_uk("Identyfikator HTML dla linków #anchor", "HTML id для #anchor посилань"),
        verbose_name=pl_uk("Anchor (kotwica)", "Якір (anchor)"),
    )

    # ── text / heading ────────────────────────────────────────────────
    heading = models.CharField(
        max_length=500, blank=True, verbose_name=pl_uk("Nagłówek", "Заголовок")
    )
    heading_level = models.CharField(
        max_length=2,
        choices=HEADING_LEVEL_CHOICES,
        default="h2",
        blank=True,
        verbose_name=pl_uk("Poziom nagłówka", "Рівень заголовка"),
    )
    body = models.TextField(blank=True, verbose_name=pl_uk("Treść", "Вміст"))

    # ── single image / banner / cta media ─────────────────────────────
    image = ProcessedImageField(
        upload_to="cms/blocks/",
        processors=[ResizeToFill(1600, 900)],
        format="WEBP",
        options={"quality": 85},
        blank=True,
        null=True,
        verbose_name=pl_uk("Obraz", "Зображення"),
    )
    image_alt = models.CharField(
        max_length=300, blank=True, verbose_name=pl_uk("Tekst alternatywny", "Альтернативний текст")
    )

    # ── video ─────────────────────────────────────────────────────────
    video_embed_url = models.URLField(
        max_length=500,
        blank=True,
        help_text=pl_uk(
            "URL do osadzenia (YouTube /embed/…, Vimeo player.vimeo.com/…)",
            "URL для вбудовування (YouTube /embed/…, Vimeo …)",
        ),
        verbose_name=pl_uk("URL osadzenia wideo", "URL вбудовування відео"),
    )
    video_file = models.FileField(
        upload_to="cms/videos/",
        blank=True,
        null=True,
        verbose_name=pl_uk("Plik wideo", "Відеофайл"),
    )

    # ── cta / button (also reused inside text block) ──────────────────
    button_text = models.CharField(
        max_length=200, blank=True, verbose_name=pl_uk("Tekst przycisku", "Текст кнопки")
    )
    button_url = models.CharField(
        max_length=500,
        blank=True,
        help_text=pl_uk(
            "Pełny URL lub względna ścieżka (np. /vouchery/, #recenzje)",
            "Повний URL або відносний шлях (напр. /vouchery/, #recenzje)",
        ),
        verbose_name=pl_uk("URL przycisku", "URL кнопки"),
    )
    button_style = models.CharField(
        max_length=20,
        choices=BUTTON_STYLE_CHOICES,
        blank=True,
        default="primary",
        verbose_name=pl_uk("Styl przycisku", "Стиль кнопки"),
    )

    # ── countdown ─────────────────────────────────────────────────────
    countdown_target = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=pl_uk("Data docelowa odliczania", "Цільова дата відліку"),
    )
    countdown_label = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=pl_uk("Etykieta odliczania", "Підпис відліку"),
    )

    # ── form ──────────────────────────────────────────────────────────
    form_kind = models.CharField(
        max_length=20,
        choices=FORM_KIND_CHOICES,
        blank=True,
        verbose_name=pl_uk("Rodzaj formularza", "Тип форми"),
    )

    # ── reviews ───────────────────────────────────────────────────────
    reviews_limit = models.PositiveSmallIntegerField(
        default=10, verbose_name=pl_uk("Limit opinii", "Ліміт відгуків")
    )

    # ── related ───────────────────────────────────────────────────────
    related_strategy = models.CharField(
        max_length=20,
        choices=RELATED_STRATEGY_CHOICES,
        blank=True,
        default="manual",
        verbose_name=pl_uk("Strategia 'Zobacz także'", "Стратегія «Дивіться також»"),
    )
    related_limit = models.PositiveSmallIntegerField(
        default=6, verbose_name=pl_uk("Limit powiązanych", "Ліміт пов’язаних")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = pl_uk("Blok strony", "Блок сторінки")
        verbose_name_plural = pl_uk("Bloki strony (konstruktor)", "Блоки сторінки (конструктор)")
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(
                fields=["content_type", "object_id", "sort_order"],
                name="cms_block_owner_order_idx",
            ),
            models.Index(fields=["kind"], name="cms_block_kind_idx"),
        ]

    def __str__(self) -> str:
        label = self.heading or self.button_text or self.get_kind_display()
        return f"[{self.get_kind_display()}] {label}"


class GalleryItem(models.Model):
    """One image inside a gallery PageBlock."""

    block = models.ForeignKey(
        PageBlock,
        on_delete=models.CASCADE,
        related_name="gallery_items",
        verbose_name=pl_uk("Blok galerii", "Блок галереї"),
    )
    image = ProcessedImageField(
        upload_to="cms/gallery/",
        processors=[ResizeToFill(1600, 1067)],
        format="WEBP",
        options={"quality": 85},
        blank=True,
        null=True,
        verbose_name=pl_uk("Obraz", "Зображення"),
    )
    image_url = models.URLField(
        max_length=500,
        blank=True,
        help_text=pl_uk(
            "Zamiast pliku: bezpośredni URL obrazu",
            "Замість файлу: пряме URL зображення",
        ),
        verbose_name=pl_uk("URL obrazu", "URL зображення"),
    )
    alt_text = models.CharField(
        max_length=300, blank=True, verbose_name=pl_uk("Tekst alternatywny", "Альтернативний текст")
    )
    sort_order = models.IntegerField(default=0, verbose_name=pl_uk("Kolejność", "Порядок"))

    class Meta:
        verbose_name = pl_uk("Element galerii", "Елемент галереї")
        verbose_name_plural = pl_uk("Elementy galerii", "Елементи галереї")
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.alt_text or (self.image.name if self.image else self.image_url) or "—"

    @property
    def src(self) -> str:
        if self.image:
            return self.image.url
        return self.image_url or ""


class RelatedItem(models.Model):
    """Manually-picked related entity in a 'Zobacz także' block."""

    block = models.ForeignKey(
        PageBlock,
        on_delete=models.CASCADE,
        related_name="related_items",
        verbose_name=pl_uk("Blok 'Zobacz także'", "Блок «Дивіться також»"),
    )
    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        limit_choices_to=_allowed_owner_models,
        verbose_name=pl_uk("Typ powiązanej strony", "Тип пов’язаної сторінки"),
    )
    target_object_id = models.PositiveIntegerField(
        verbose_name=pl_uk("ID powiązanej strony", "ID пов’язаної сторінки")
    )
    target = GenericForeignKey("target_content_type", "target_object_id")
    sort_order = models.IntegerField(default=0, verbose_name=pl_uk("Kolejność", "Порядок"))

    class Meta:
        verbose_name = pl_uk("Powiązana strona", "Пов’язана сторінка")
        verbose_name_plural = pl_uk("Powiązane strony", "Пов’язані сторінки")
        ordering = ["sort_order", "id"]
        indexes = [
            models.Index(
                fields=["target_content_type", "target_object_id"],
                name="cms_related_target_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"#{self.sort_order} → {self.target}"
