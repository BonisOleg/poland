from django.db import models
from django.urls import reverse
from django.utils import timezone
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill
from pilkit.processors.resize import Anchor

from apps.core.labels import pl_uk


class Category(models.Model):
    name = models.CharField(max_length=200, verbose_name=pl_uk("Nazwa", "Назва"))
    slug = models.SlugField(unique=True, verbose_name=pl_uk("Slug", "Слаг"))
    icon = models.CharField(max_length=50, blank=True, verbose_name=pl_uk("Ikona", "Іконка"))
    description = models.TextField(blank=True, verbose_name=pl_uk("Opis", "Опис"))
    sort_order = models.IntegerField(default=0, verbose_name=pl_uk("Kolejność", "Порядок"))

    class Meta:
        verbose_name = pl_uk("Kategoria", "Категорія")
        verbose_name_plural = pl_uk("Kategorie", "Категорії")
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class AgeGroup(models.Model):
    name = models.CharField(max_length=100, verbose_name=pl_uk("Nazwa", "Назва"))
    slug = models.SlugField(unique=True, verbose_name=pl_uk("Slug", "Слаг"))
    min_age = models.IntegerField(default=0, verbose_name=pl_uk("Wiek min.", "Мін. вік"))
    max_age = models.IntegerField(default=99, verbose_name=pl_uk("Wiek maks.", "Макс. вік"))

    class Meta:
        verbose_name = pl_uk("Grupa wiekowa", "Вікова група")
        verbose_name_plural = pl_uk("Grupy wiekowe", "Вікові групи")
        ordering = ["min_age"]

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=200, verbose_name=pl_uk("Nazwa", "Назва"))
    slug = models.SlugField(unique=True, verbose_name=pl_uk("Slug", "Слаг"))
    region = models.CharField(max_length=200, blank=True, verbose_name=pl_uk("Region", "Регіон"))

    class Meta:
        verbose_name = pl_uk("Miasto", "Місто")
        verbose_name_plural = pl_uk("Miasta", "Міста")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Venue(models.Model):
    name = models.CharField(max_length=300, verbose_name=pl_uk("Nazwa", "Назва"))
    city = models.ForeignKey(
        City, on_delete=models.CASCADE, related_name="venues", verbose_name=pl_uk("Miasto", "Місто")
    )
    address = models.CharField(max_length=500, blank=True, verbose_name=pl_uk("Adres", "Адреса"))
    lat = models.FloatField(null=True, blank=True, verbose_name=pl_uk("Szer. geogr.", "Широта"))
    lng = models.FloatField(null=True, blank=True, verbose_name=pl_uk("Dł. geogr.", "Довгота"))

    class Meta:
        verbose_name = pl_uk("Miejsce", "Місце проведення")
        verbose_name_plural = pl_uk("Miejsca", "Місця проведення")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.city.name})"


class Event(models.Model):
    title = models.CharField(max_length=500, verbose_name=pl_uk("Tytuł", "Заголовок"))
    slug = models.SlugField(max_length=200, unique=True, verbose_name=pl_uk("Slug", "Слаг"))
    description = models.TextField(blank=True, verbose_name=pl_uk("Opis", "Опис"))
    short_description = models.TextField(
        blank=True, max_length=500, verbose_name=pl_uk("Krótki opis", "Короткий опис")
    )
    categories = models.ManyToManyField(
        Category, blank=True, related_name="events", verbose_name=pl_uk("Kategorie", "Категорії")
    )
    age_group = models.ForeignKey(
        AgeGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
        verbose_name=pl_uk("Grupa wiekowa", "Вікова група"),
    )
    event_type = models.CharField(
        max_length=50,
        choices=[
            ("spektakl", "Spektakl"),
            ("koncert", "Koncert"),
            ("festiwal", "Festiwal"),
            ("widowisko", "Widowisko"),
            ("warsztat", "Warsztat"),
            ("inne", "Inne"),
        ],
        default="spektakl",
        verbose_name=pl_uk("Typ wydarzenia", "Тип події"),
    )
    is_active = models.BooleanField(default=True, verbose_name=pl_uk("Aktywne", "Активна"))
    target_audience = models.CharField(
        max_length=300, blank=True, verbose_name=pl_uk("Grupa docelowa", "Цільова аудиторія")
    )
    duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text=pl_uk("Czas trwania w minutach", "Тривалість у хвилинах"),
        verbose_name=pl_uk("Czas trwania (min)", "Тривалість (хв)"),
    )
    language_spoken = models.CharField(
        max_length=10,
        choices=[
            ("pl", "Polski"),
            ("en", "English"),
            ("ua", "Українська"),
            ("mixed", "Мішана мова"),
        ],
        blank=True,
        verbose_name=pl_uk("Język", "Мова"),
    )
    biletyna_base_url = models.URLField(
        blank=True, verbose_name=pl_uk("Bazowy URL Biletyna", "Базовий URL Biletyna")
    )
    image = ProcessedImageField(
        upload_to="events/",
        processors=[ResizeToFill(1200, 800, anchor=Anchor.BOTTOM)],
        format="WEBP",
        options={"quality": 85},
        blank=True,
        null=True,
        verbose_name=pl_uk("Obraz", "Зображення"),
    )
    hero_image_focal = models.CharField(
        max_length=20,
        choices=[
            ("top", "Top"),
            ("center", "Center"),
            ("bottom", "Bottom"),
        ],
        default="center",
        help_text=pl_uk(
            "Pionowe kadrowanie obrazu bohatera (object-position)",
            "Вертикальне кадрування зображення героя (object-position)",
        ),
        verbose_name=pl_uk("Ostrość obrazu bohatera", "Фокус зображення героя"),
    )
    sort_order = models.IntegerField(default=0, verbose_name=pl_uk("Kolejność", "Порядок"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=pl_uk("Utworzono", "Створено"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=pl_uk("Zaktualizowano", "Оновлено"))

    class Meta:
        verbose_name = pl_uk("Wydarzenie", "Подія")
        verbose_name_plural = pl_uk("Wydarzenia", "Події")
        ordering = ["-sort_order", "title"]

    def __str__(self):
        return self.title


class EventCity(models.Model):
    TICKET_STATUS_CHOICES = [
        ("available", "Dostępne"),
        ("few_left", "Ostatnie miejsca!"),
        ("sold_out", "WYPRZEDANE"),
        ("upcoming", "Wkrótce w sprzedaży"),
    ]

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="event_cities", verbose_name=pl_uk("Wydarzenie", "Подія")
    )
    city = models.ForeignKey(
        City, on_delete=models.CASCADE, related_name="event_cities", verbose_name=pl_uk("Miasto", "Місто")
    )
    venue = models.ForeignKey(
        Venue,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="event_cities",
        verbose_name=pl_uk("Miejsce", "Місце"),
    )
    slug = models.SlugField(max_length=300, unique=True, verbose_name=pl_uk("Slug", "Слаг"))
    custom_title = models.CharField(
        max_length=500, blank=True, verbose_name=pl_uk("Niestandardowy tytuł", "Власний заголовок")
    )
    event_date = models.DateTimeField(
        null=True, blank=True, verbose_name=pl_uk("Data wydarzenia", "Дата події")
    )
    sale_end_date = models.DateTimeField(
        null=True, blank=True, verbose_name=pl_uk("Koniec sprzedaży", "Кінець продажу")
    )
    biletyna_url = models.URLField(
        blank=True, max_length=500, verbose_name=pl_uk("URL Biletyna", "URL Biletyna")
    )
    ticket_status = models.CharField(
        max_length=20,
        choices=TICKET_STATUS_CHOICES,
        default="available",
        verbose_name=pl_uk("Status biletów", "Статус квитків"),
    )
    seats_left = models.IntegerField(
        null=True, blank=True, verbose_name=pl_uk("Pozostałe miejsca", "Залишок місць")
    )
    price_from = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=pl_uk("Cena od", "Ціна від"),
    )
    price_to = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=pl_uk("Cena do", "Ціна до"),
    )
    keywords = models.CharField(max_length=500, blank=True, verbose_name=pl_uk("Słowa kluczowe", "Ключові слова"))
    related_events_manual = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="featured_in_related",
        verbose_name=pl_uk("Powiązane wydarzenia (ręcznie)", "Пов’язані події (вручну)"),
    )

    seo_title = models.CharField(max_length=500, blank=True, verbose_name=pl_uk("Tytuł SEO", "SEO-заголовок"))
    seo_description = models.TextField(blank=True, verbose_name=pl_uk("Opis SEO", "SEO-опис"))
    og_image = models.URLField(blank=True, max_length=500, verbose_name=pl_uk("Obraz OG", "OG-зображення"))
    canonical_url = models.URLField(blank=True, max_length=500, verbose_name=pl_uk("URL kanoniczny", "Канонічний URL"))
    content_html = models.TextField(blank=True, verbose_name=pl_uk("Treść HTML", "Вміст HTML"))
    use_new_layout = models.BooleanField(
        default=False,
        help_text=pl_uk(
            "Układ strukturalny (bloki treści, wideo, galeria). Stary HTML jest ignorowany.",
            "Структурований макет (блоки контенту, відео, галерея). Старий HTML ігнорується.",
        ),
        verbose_name=pl_uk("Nowy układ strony", "Новий макет сторінки"),
    )
    use_block_builder = models.BooleanField(
        default=False,
        help_text=pl_uk(
            "Renderuj stronę z konstruktora bloków (CMS). Pomija stary układ.",
            "Рендерити сторінку з блок-конструктора (CMS). Ігнорує старий макет.",
        ),
        verbose_name=pl_uk("Konstruktor bloków (CMS)", "Блок-конструктор (CMS)"),
    )
    is_published = models.BooleanField(default=True, verbose_name=pl_uk("Opublikowane", "Опубліковано"))
    is_archived = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=pl_uk("Zarchiwizowane", "Заархівоване"),
    )
    archive_date = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name=pl_uk("Data archiwizacji", "Дата архівації"),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=pl_uk("Utworzono", "Створено"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=pl_uk("Zaktualizowano", "Оновлено"))

    class Meta:
        verbose_name = pl_uk("Wydarzenie w mieście", "Подія в місті")
        verbose_name_plural = pl_uk("Wydarzenia w miastach", "Події в містах")
        ordering = ["event_date"]
        unique_together = [("event", "city", "event_date")]

    def __str__(self):
        date_str = self.event_date.strftime("%d.%m.%Y") if self.event_date else "TBD"
        return f"{self.event.title} - {self.city.name} ({date_str})"

    def get_absolute_url(self):
        return f"/{self.slug}/"

    def get_display_title(self):
        return self.custom_title or f"{self.event.title} - {self.city.name}"

    def get_seo_title(self):
        return self.seo_title or self.get_display_title()

    def get_related_events(self, limit=6):
        return (
            EventCity.objects.filter(
                is_published=True,
                city=self.city,
            )
            .exclude(pk=self.pk)
            .select_related("event", "city")[:limit]
        )

    @property
    def is_upcoming(self):
        if not self.event_date:
            return True
        return self.event_date > timezone.now()

    @property
    def ticket_badge(self):
        if self.seats_left is not None:
            if self.seats_left <= 0:
                return "WYPRZEDANE"
            if self.seats_left < 10:
                return "WYPRZEDANE"
            if self.seats_left < 50:
                return "Ostatnie miejsca!"
        return dict(self.TICKET_STATUS_CHOICES).get(self.ticket_status, "")

    @property
    def should_be_archived(self) -> bool:
        """Check if event meets archival criteria (2025 or older, or past event)."""
        if not self.event_date:
            return False
        # Archive if event is in 2025 or earlier, OR if date is in the past
        return self.event_date.year <= 2025 or self.event_date < timezone.now()

    @classmethod
    def get_upcoming_events(cls):
        """Queryset for active/upcoming events only."""
        return cls.objects.filter(is_published=True, is_archived=False).select_related("event", "city")

    @classmethod
    def get_archived_events(cls):
        """Queryset for archived events only."""
        return cls.objects.filter(is_published=True, is_archived=True).select_related("event", "city")


class EventVideo(models.Model):
    event_city = models.ForeignKey(
        EventCity,
        on_delete=models.CASCADE,
        related_name="videos",
        verbose_name=pl_uk("Wydarzenie w mieście", "Подія в місті"),
    )
    embed_url = models.URLField(
        max_length=500,
        blank=True,
        help_text=pl_uk(
            "URL do osadzenia (YouTube /embed/…, Vimeo player.vimeo.com/…)",
            "URL для вбудовування (YouTube /embed/…, Vimeo …)",
        ),
        verbose_name=pl_uk("URL osadzenia", "URL вбудовування"),
    )
    video_file = models.FileField(
        upload_to="events/videos/",
        blank=True,
        null=True,
        help_text=pl_uk(
            "Zamiast URL: plik wideo z komputera (mp4/webm)",
            "Замість URL: відеофайл з комп’ютера (mp4/webm)",
        ),
        verbose_name=pl_uk("Plik wideo", "Відеофайл"),
    )
    title = models.CharField(max_length=300, blank=True, verbose_name=pl_uk("Tytuł", "Заголовок"))
    sort_order = models.IntegerField(default=0, verbose_name=pl_uk("Kolejność", "Порядок"))

    class Meta:
        verbose_name = pl_uk("Wideo wydarzenia", "Відео події")
        verbose_name_plural = pl_uk("Wideo wydarzeń", "Відео подій")
        ordering = ["sort_order"]

    def __str__(self):
        return self.title or self.embed_url


class EventContentBlock(models.Model):
    event_city = models.ForeignKey(
        EventCity,
        on_delete=models.CASCADE,
        related_name="content_blocks",
        verbose_name=pl_uk("Wydarzenie w mieście", "Подія в місті"),
    )
    title = models.CharField(max_length=500, blank=True, verbose_name=pl_uk("Tytuł", "Заголовок"))
    body = models.TextField(blank=True, verbose_name=pl_uk("Treść", "Вміст"))
    image = ProcessedImageField(
        upload_to="events/blocks/",
        processors=[ResizeToFill(1200, 800)],
        format="WEBP",
        options={"quality": 85},
        blank=True,
        null=True,
        verbose_name=pl_uk("Obraz", "Зображення"),
    )
    button_text = models.CharField(max_length=200, blank=True, verbose_name=pl_uk("Tekst przycisku", "Текст кнопки"))
    button_url = models.URLField(blank=True, max_length=500, verbose_name=pl_uk("URL przycisku", "URL кнопки"))
    sort_order = models.IntegerField(default=0, verbose_name=pl_uk("Kolejność", "Порядок"))

    class Meta:
        verbose_name = pl_uk("Blok treści wydarzenia", "Блок контенту події")
        verbose_name_plural = pl_uk("Bloki treści wydarzeń", "Блоки контенту подій")
        ordering = ["sort_order"]

    def __str__(self):
        return self.title or f"Block #{self.pk}"


class EventImage(models.Model):
    event_city = models.ForeignKey(
        EventCity,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name=pl_uk("Wydarzenie w mieście", "Подія в місті"),
    )
    image = ProcessedImageField(
        upload_to="events/gallery/",
        processors=[ResizeToFill(1200, 800)],
        format="WEBP",
        options={"quality": 85},
        blank=True,
        null=True,
        verbose_name=pl_uk("Obraz", "Зображення"),
    )
    image_url = models.URLField(
        blank=True,
        max_length=500,
        help_text=pl_uk(
            "Zamiast pliku: bezpośredni URL obrazu",
            "Замість файлу: пряме URL зображення",
        ),
        verbose_name=pl_uk("URL obrazu", "URL зображення"),
    )
    alt_text = models.CharField(max_length=300, blank=True, verbose_name=pl_uk("Tekst alternatywny", "Альтернативний текст"))
    sort_order = models.IntegerField(default=0, verbose_name=pl_uk("Kolejność", "Порядок"))

    class Meta:
        verbose_name = pl_uk("Zdjęcie galerii", "Фото галереї")
        verbose_name_plural = pl_uk(
            "Galeria zdjęć (dodaj wiele — pojawi się na stronie)",
            "Галерея фото (додайте кілька — з’явиться на сайті)",
        )
        ordering = ["sort_order"]

    @property
    def src(self):
        if self.image:
            return self.image.url
        return self.image_url
