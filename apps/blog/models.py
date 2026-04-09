from django.db import models
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill


class Article(models.Model):
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=300, unique=True)
    excerpt = models.TextField(blank=True, max_length=500)
    content = models.TextField()
    image = ProcessedImageField(
        upload_to="blog/",
        processors=[ResizeToFill(1200, 700)],
        format="WEBP",
        options={"quality": 85},
        blank=True,
        null=True,
    )
    seo_title = models.CharField(max_length=500, blank=True)
    seo_description = models.TextField(blank=True)
    og_image = models.URLField(blank=True, max_length=500)
    keywords = models.CharField(max_length=500, blank=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Статья"
        verbose_name_plural = "Статьи"
        ordering = ["-published_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f"/aktualnosci/{self.slug}/"
