from django.db import models

from apps.core.labels import pl_uk


class Review(models.Model):
    event_city = models.ForeignKey(
        "events.EventCity",
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=pl_uk("Wydarzenie w mieście", "Подія в місті"),
    )
    author_name = models.CharField(max_length=200, verbose_name=pl_uk("Autor", "Автор"))
    rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        default=5,
        verbose_name=pl_uk("Ocena", "Оцінка"),
    )
    content = models.TextField(max_length=2000, verbose_name=pl_uk("Treść", "Вміст"))
    is_approved = models.BooleanField(default=False, verbose_name=pl_uk("Zatwierdzona", "Схвалено"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=pl_uk("Utworzono", "Створено"))

    class Meta:
        verbose_name = pl_uk("Opinia", "Відгук")
        verbose_name_plural = pl_uk("Opinie", "Відгуки")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author_name} - {self.rating}/5"
