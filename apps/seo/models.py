from django.db import models


class Redirect(models.Model):
    old_path = models.CharField(max_length=500, unique=True, db_index=True)
    new_path = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Редирект"
        verbose_name_plural = "Редиректы"

    def __str__(self):
        return f"{self.old_path} → {self.new_path}"
