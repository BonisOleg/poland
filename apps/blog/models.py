from django.db import models
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill

from apps.core.labels import pl_uk


class Article(models.Model):
    title = models.CharField(max_length=500, verbose_name=pl_uk("Tytuł", "Заголовок"))
    slug = models.SlugField(max_length=300, unique=True, verbose_name=pl_uk("Slug", "Слаг"))
    excerpt = models.TextField(blank=True, max_length=500, verbose_name=pl_uk("Zajawka", "Анонс"))
    content = models.TextField(verbose_name=pl_uk("Treść", "Вміст"))
    image = ProcessedImageField(
        upload_to="blog/",
        processors=[ResizeToFill(1200, 700)],
        format="WEBP",
        options={"quality": 85},
        blank=True,
        null=True,
        verbose_name=pl_uk("Obraz", "Зображення"),
    )
    seo_title = models.CharField(max_length=500, blank=True, verbose_name=pl_uk("Tytuł SEO", "SEO-заголовок"))
    seo_description = models.TextField(blank=True, verbose_name=pl_uk("Opis SEO", "SEO-опис"))
    og_image = models.URLField(blank=True, max_length=500, verbose_name=pl_uk("Obraz OG", "OG-зображення"))
    keywords = models.CharField(max_length=500, blank=True, verbose_name=pl_uk("Słowa kluczowe", "Ключові слова"))
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
    use_block_builder = models.BooleanField(
        default=False,
        help_text=pl_uk(
            "Użyj nowego konstruktora bloków (CMS). Stary HTML jest ignorowany.",
            "Використати новий блок-конструктор (CMS). Старий HTML ігнорується.",
        ),
        verbose_name=pl_uk("Konstruktor bloków (CMS)", "Блок-конструктор (CMS)"),
    )
    is_published = models.BooleanField(default=False, verbose_name=pl_uk("Opublikowane", "Опубліковано"))
    published_at = models.DateTimeField(null=True, blank=True, verbose_name=pl_uk("Data publikacji", "Дата публікації"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=pl_uk("Utworzono", "Створено"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=pl_uk("Zaktualizowano", "Оновлено"))

    class Meta:
        verbose_name = pl_uk("Artykuł", "Стаття")
        verbose_name_plural = pl_uk("Artykuły", "Статті")
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f"/aktualnosci/{self.slug}/"
