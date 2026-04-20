from django.db import models

from apps.core.labels import pl_uk


class Redirect(models.Model):
    old_path = models.CharField(
        max_length=500, unique=True, db_index=True, verbose_name=pl_uk("Stary adres (ścieżka)", "Стара адреса (шлях)")
    )
    new_path = models.CharField(max_length=500, verbose_name=pl_uk("Nowy adres (ścieżka)", "Нова адреса (шлях)"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=pl_uk("Utworzono", "Створено"))

    class Meta:
        verbose_name = pl_uk("Przekierowanie", "Редирект")
        verbose_name_plural = pl_uk("Przekierowania", "Редиректи")

    def __str__(self):
        return f"{self.old_path} → {self.new_path}"
