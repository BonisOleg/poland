from django.db import models

from apps.core.labels import pl_uk


class GroupInquiry(models.Model):
    """Lead from the corporate group inquiry form on /dla-firm/."""

    INTENT_CHOICES = [
        ("repertuar", "Repertuar"),
        ("rezerwacja", "Rezerwacja biletów"),
        ("specjalna_oferta", "Oferta specjalna"),
        ("event_firmowy", "Event / wyjazd"),
        ("voucher", "Voucher / prezent"),
        ("other", "Inne"),
    ]

    intent = models.CharField(max_length=32, choices=INTENT_CHOICES, db_index=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=40, blank=True)
    company = models.CharField(max_length=300, blank=True)
    nip = models.CharField(max_length=20, blank=True)
    ticket_count = models.CharField(max_length=50, blank=True)
    message = models.TextField()
    source_page = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    handled = models.BooleanField(default=False, verbose_name=pl_uk("Obsłużone", "Опрацьовано"))
    staff_notes = models.TextField(
        blank=True, verbose_name=pl_uk("Notatki wewnętrzne", "Внутрішні нотатки")
    )

    class Meta:
        verbose_name = pl_uk("Zgłoszenie grupowe", "Групова заявка")
        verbose_name_plural = pl_uk("Zgłoszenia grupowe", "Групові заявки")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.created_at:%Y-%m-%d %H:%M} — {self.email} ({self.get_intent_display()})"


class StaticPage(models.Model):
    title = models.CharField(max_length=500, verbose_name=pl_uk("Tytuł", "Заголовок"))
    slug = models.SlugField(max_length=300, unique=True, verbose_name=pl_uk("Slug", "Слаг"))
    content = models.TextField(verbose_name=pl_uk("Treść", "Вміст"))
    seo_title = models.CharField(max_length=500, blank=True, verbose_name=pl_uk("Tytuł SEO", "SEO-заголовок"))
    seo_description = models.TextField(blank=True, verbose_name=pl_uk("Opis SEO", "SEO-опис"))
    keywords = models.CharField(max_length=500, blank=True, verbose_name=pl_uk("Słowa kluczowe", "Ключові слова"))
    page_type = models.CharField(
        max_length=20,
        choices=[("static", "Статична сторінка"), ("landing", "Лендінг")],
        default="static",
        verbose_name=pl_uk("Typ strony", "Тип сторінки"),
    )
    layout_version = models.CharField(
        max_length=10,
        choices=[("v1", "Класична")],
        default="v1",
        verbose_name=pl_uk("Wersja układu", "Версія макета"),
    )
    show_contact_form = models.BooleanField(
        default=False, verbose_name=pl_uk("Pokaż formularz kontaktowy", "Показати форму контакту")
    )
    use_block_builder = models.BooleanField(
        default=False,
        help_text=pl_uk(
            "Użyj nowego konstruktora bloków (CMS). Stary HTML jest ignorowany.",
            "Використати новий блок-конструктор (CMS). Старий HTML ігнорується.",
        ),
        verbose_name=pl_uk("Konstruktor bloków (CMS)", "Блок-конструктор (CMS)"),
    )
    og_image = models.URLField(
        blank=True, max_length=500, verbose_name=pl_uk("Obraz OG", "OG-зображення")
    )
    canonical_url = models.URLField(
        blank=True, max_length=500, verbose_name=pl_uk("URL kanoniczny", "Канонічний URL")
    )
    robots_directives = models.CharField(
        max_length=100,
        blank=True,
        help_text=pl_uk(
            "Np. noindex,nofollow — pozostaw puste dla domyślnych",
            "Напр. noindex,nofollow — залиш порожнім для дефолтних",
        ),
        verbose_name=pl_uk("Dyrektywy robots", "Директиви robots"),
    )
    is_published = models.BooleanField(default=True, verbose_name=pl_uk("Opublikowane", "Опубліковано"))
    sort_order = models.IntegerField(default=0, verbose_name=pl_uk("Kolejność", "Порядок"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=pl_uk("Utworzono", "Створено"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=pl_uk("Zaktualizowano", "Оновлено"))

    class Meta:
        verbose_name = pl_uk("Strona statyczna", "Статична сторінка")
        verbose_name_plural = pl_uk("Strony statyczne", "Статичні сторінки")
        ordering = ["sort_order"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f"/{self.slug}/"


class PageMedia(models.Model):
    KIND_IMAGE = "image"
    KIND_VIDEO = "video"
    KIND_CHOICES = [(KIND_IMAGE, "Zdjęcie"), (KIND_VIDEO, "Wideo")]

    page = models.ForeignKey(
        StaticPage, on_delete=models.CASCADE, related_name="media", verbose_name=pl_uk("Strona", "Сторінка")
    )
    kind = models.CharField(
        max_length=10, choices=KIND_CHOICES, default=KIND_IMAGE, verbose_name=pl_uk("Rodzaj", "Тип")
    )
    image = models.ImageField(
        upload_to="pages/media/", blank=True, null=True, verbose_name=pl_uk("Obraz", "Зображення")
    )
    video_file = models.FileField(
        upload_to="pages/media/", blank=True, null=True, verbose_name=pl_uk("Plik wideo", "Відеофайл")
    )
    video_embed_url = models.URLField(
        blank=True, verbose_name=pl_uk("URL osadzenia wideo", "URL вбудовування відео")
    )
    caption = models.CharField(max_length=300, blank=True, verbose_name=pl_uk("Podpis", "Підпис"))
    sort_order = models.IntegerField(default=0, verbose_name=pl_uk("Kolejność", "Порядок"))

    class Meta:
        verbose_name = pl_uk("Media strony", "Медіа сторінки")
        verbose_name_plural = pl_uk("Media stron", "Медіа сторінок")
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.get_kind_display()} — {self.page.slug} #{self.sort_order}"
