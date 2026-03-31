from django.db import models


class Voucher(models.Model):
    name = models.CharField(max_length=300)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="PLN")
    image = models.ImageField(upload_to="vouchers/", blank=True, null=True)
    purchase_url = models.URLField(blank=True, max_length=500)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Ваучер"
        verbose_name_plural = "Ваучеры"
        ordering = ["sort_order", "price"]

    def __str__(self):
        return f"{self.name} ({self.price} {self.currency})"
