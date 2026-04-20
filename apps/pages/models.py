from django.db import models

from apps.core.labels import pl_uk


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
