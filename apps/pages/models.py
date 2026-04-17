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
    layout_version = models.CharField(
        max_length=10,
        choices=[("v1", "Класична"), ("v2", "Галерея (нова)")],
        default="v1",
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


class PageMedia(models.Model):
    KIND_IMAGE = "image"
    KIND_VIDEO = "video"
    KIND_CHOICES = [(KIND_IMAGE, "Zdjęcie"), (KIND_VIDEO, "Wideo")]

    page = models.ForeignKey(StaticPage, on_delete=models.CASCADE, related_name="media")
    kind = models.CharField(max_length=10, choices=KIND_CHOICES, default=KIND_IMAGE)
    image = models.ImageField(upload_to="pages/media/", blank=True, null=True)
    video_file = models.FileField(upload_to="pages/media/", blank=True, null=True)
    video_embed_url = models.URLField(blank=True)
    caption = models.CharField(max_length=300, blank=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Медіа сторінки"
        verbose_name_plural = "Медіа сторінок"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"{self.get_kind_display()} — {self.page.slug} #{self.sort_order}"
