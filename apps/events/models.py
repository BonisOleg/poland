from django.db import models
from django.urls import reverse
from django.utils import timezone
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill
from pilkit.processors.resize import Anchor


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class AgeGroup(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    min_age = models.IntegerField(default=0)
    max_age = models.IntegerField(default=99)

    class Meta:
        verbose_name = "Возрастная группа"
        verbose_name_plural = "Возрастные группы"
        ordering = ["min_age"]

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    region = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Venue(models.Model):
    name = models.CharField(max_length=300)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="venues")
    address = models.CharField(max_length=500, blank=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = "Площадка"
        verbose_name_plural = "Площадки"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.city.name})"


class Event(models.Model):
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    short_description = models.TextField(blank=True, max_length=500)
    categories = models.ManyToManyField(Category, blank=True, related_name="events")
    age_group = models.ForeignKey(
        AgeGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name="events"
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
    )
    is_active = models.BooleanField(default=True)
    target_audience = models.CharField(max_length=300, blank=True)
    duration = models.PositiveIntegerField(null=True, blank=True, help_text="Тривалість у хвилинах")
    language_spoken = models.CharField(
        max_length=10,
        choices=[
            ("pl", "Polski"),
            ("en", "English"),
            ("ua", "Українська"),
            ("mixed", "Мішана мова"),
        ],
        blank=True,
    )
    biletyna_base_url = models.URLField(blank=True)
    image = ProcessedImageField(
        upload_to="events/",
        processors=[ResizeToFill(1200, 800, anchor=Anchor.BOTTOM)],
        format="WEBP",
        options={"quality": 85},
        blank=True,
        null=True,
    )
    hero_image_focal = models.CharField(
        max_length=20,
        choices=[
            ("top", "Top"),
            ("center", "Center"),
            ("bottom", "Bottom"),
        ],
        default="center",
        help_text="Vertical crop focus for the event detail hero image (object-position).",
    )
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "События"
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

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="event_cities")
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="event_cities")
    venue = models.ForeignKey(
        Venue, on_delete=models.SET_NULL, null=True, blank=True, related_name="event_cities"
    )
    slug = models.SlugField(max_length=300, unique=True)
    custom_title = models.CharField(max_length=500, blank=True)
    event_date = models.DateTimeField(null=True, blank=True)
    sale_end_date = models.DateTimeField(null=True, blank=True)
    biletyna_url = models.URLField(blank=True, max_length=500)
    ticket_status = models.CharField(
        max_length=20, choices=TICKET_STATUS_CHOICES, default="available"
    )
    seats_left = models.IntegerField(null=True, blank=True)
    price_from = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_to = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    keywords = models.CharField(max_length=500, blank=True)
    related_events_manual = models.ManyToManyField(
        "self", blank=True, symmetrical=False, related_name="featured_in_related"
    )

    seo_title = models.CharField(max_length=500, blank=True)
    seo_description = models.TextField(blank=True)
    og_image = models.URLField(blank=True, max_length=500)
    canonical_url = models.URLField(blank=True, max_length=500)
    content_html = models.TextField(blank=True)
    use_new_layout = models.BooleanField(
        default=False,
        help_text="Увімкнути структурований layout (контент-блоки, відео-, фото-галерея). Старий content_html ігнорується.",
    )
    is_published = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Событие в городе"
        verbose_name_plural = "События в городах"
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


class EventVideo(models.Model):
    event_city = models.ForeignKey(
        EventCity, on_delete=models.CASCADE, related_name="videos"
    )
    embed_url = models.URLField(max_length=500, help_text="Повний embed-URL (YouTube /embed/…, Vimeo player.vimeo.com/…)")
    title = models.CharField(max_length=300, blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Відео події"
        verbose_name_plural = "Відео подій"
        ordering = ["sort_order"]

    def __str__(self):
        return self.title or self.embed_url


class EventContentBlock(models.Model):
    event_city = models.ForeignKey(
        EventCity, on_delete=models.CASCADE, related_name="content_blocks"
    )
    title = models.CharField(max_length=500, blank=True)
    body = models.TextField(blank=True)
    image = ProcessedImageField(
        upload_to="events/blocks/",
        processors=[ResizeToFill(1200, 800)],
        format="WEBP",
        options={"quality": 85},
        blank=True,
        null=True,
    )
    button_text = models.CharField(max_length=200, blank=True)
    button_url = models.URLField(blank=True, max_length=500)
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Блок контенту події"
        verbose_name_plural = "Блоки контенту події"
        ordering = ["sort_order"]

    def __str__(self):
        return self.title or f"Block #{self.pk}"


class EventImage(models.Model):
    event_city = models.ForeignKey(
        EventCity, on_delete=models.CASCADE, related_name="images"
    )
    image = ProcessedImageField(
        upload_to="events/gallery/",
        processors=[ResizeToFill(1200, 800)],
        format="WEBP",
        options={"quality": 85},
    )
    alt_text = models.CharField(max_length=300, blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Zdjęcie galerii"
        verbose_name_plural = "Galeria zdjęć (dodaj wiele zdjęć tutaj)"
        ordering = ["sort_order"]
