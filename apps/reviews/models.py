from django.db import models


class Review(models.Model):
    event_city = models.ForeignKey(
        "events.EventCity", on_delete=models.CASCADE, related_name="reviews"
    )
    author_name = models.CharField(max_length=200)
    rating = models.IntegerField(
        choices=[(i, str(i)) for i in range(1, 6)], default=5
    )
    content = models.TextField(max_length=2000)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author_name} - {self.rating}/5"
