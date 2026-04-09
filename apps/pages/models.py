from django.db import models


class StaticPage(models.Model):
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=300, unique=True)
    content = models.TextField()
    seo_title = models.CharField(max_length=500, blank=True)
    seo_description = models.TextField(blank=True)
    keywords = models.CharField(max_length=500, blank=True)
    page_type = models.CharField(
        max_length=20,
        choices=[("static", "Статична сторінка"), ("landing", "Лендінг")],
        default="static",
    )
    show_contact_form = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Статическая страница"
        verbose_name_plural = "Статические страницы"
        ordering = ["sort_order"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return f"/{self.slug}/"
