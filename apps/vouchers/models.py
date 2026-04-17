from django.db import models
from django.urls import reverse


class Voucher(models.Model):
    name = models.CharField(max_length=300)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="PLN")
    image = models.ImageField(
        upload_to="vouchers/", blank=True, null=True, max_length=255
    )
    purchase_url = models.URLField(blank=True, max_length=500)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Ваучер"
        verbose_name_plural = "Ваучеры"
        ordering = ["sort_order", "price"]

    def __str__(self) -> str:
        return f"{self.name} ({self.price} {self.currency})"

    def get_checkout_url(self) -> str:
        return reverse("vouchers:checkout", kwargs={"slug": self.slug})


class VoucherOrder(models.Model):
    STATUS_PENDING = "PENDING"
    STATUS_WAITING = "WAITING_FOR_CONFIRMATION"
    STATUS_COMPLETED = "COMPLETED"
    STATUS_CANCELED = "CANCELED"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Oczekuje"),
        (STATUS_WAITING, "Oczekuje na potwierdzenie"),
        (STATUS_COMPLETED, "Opłacono"),
        (STATUS_CANCELED, "Anulowano"),
    ]

    voucher = models.ForeignKey(Voucher, on_delete=models.PROTECT, related_name="orders")
    payu_order_id = models.CharField(max_length=100, blank=True, db_index=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    buyer_first_name = models.CharField(max_length=100)
    buyer_last_name = models.CharField(max_length=100)
    buyer_email = models.EmailField()
    buyer_phone = models.CharField(max_length=20, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Zamówienie vouchera"
        verbose_name_plural = "Zamówienia voucherów"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"#{self.pk} {self.voucher.name} — {self.buyer_email} [{self.status}]"
