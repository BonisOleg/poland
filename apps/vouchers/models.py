from django.db import models
from django.urls import reverse

from apps.core.labels import pl_uk


class Voucher(models.Model):
    name = models.CharField(max_length=300, verbose_name=pl_uk("Nazwa", "Назва"))
    slug = models.SlugField(unique=True, verbose_name=pl_uk("Slug", "Слаг"))
    description = models.TextField(blank=True, verbose_name=pl_uk("Opis", "Опис"))
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=pl_uk("Cena", "Ціна"))
    currency = models.CharField(max_length=3, default="PLN", verbose_name=pl_uk("Waluta", "Валюта"))
    image = models.ImageField(
        upload_to="vouchers/", blank=True, null=True, max_length=255, verbose_name=pl_uk("Obraz", "Зображення")
    )
    purchase_url = models.URLField(
        blank=True, max_length=500, verbose_name=pl_uk("URL zakupu", "URL покупки")
    )
    is_active = models.BooleanField(default=True, verbose_name=pl_uk("Aktywny", "Активний"))
    sort_order = models.IntegerField(default=0, verbose_name=pl_uk("Kolejność", "Порядок"))

    class Meta:
        verbose_name = pl_uk("Voucher", "Ваучер")
        verbose_name_plural = pl_uk("Vouchery", "Ваучери")
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

    voucher = models.ForeignKey(
        Voucher, on_delete=models.PROTECT, related_name="orders", verbose_name=pl_uk("Voucher", "Ваучер")
    )
    payu_order_id = models.CharField(
        max_length=100, blank=True, db_index=True, verbose_name=pl_uk("ID zamówienia PayU", "ID замовлення PayU")
    )
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING, verbose_name=pl_uk("Status", "Статус")
    )
    buyer_first_name = models.CharField(max_length=100, verbose_name=pl_uk("Imię kupującego", "Ім’я покупця"))
    buyer_last_name = models.CharField(max_length=100, verbose_name=pl_uk("Nazwisko kupującego", "Прізвище покупця"))
    buyer_email = models.EmailField(verbose_name=pl_uk("E-mail kupującego", "Email покупця"))
    buyer_phone = models.CharField(max_length=20, blank=True, verbose_name=pl_uk("Telefon kupującego", "Телефон покупця"))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=pl_uk("Kwota", "Сума"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=pl_uk("Utworzono", "Створено"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=pl_uk("Zaktualizowano", "Оновлено"))

    class Meta:
        verbose_name = pl_uk("Zamówienie vouchera", "Замовлення ваучера")
        verbose_name_plural = pl_uk("Zamówienia voucherów", "Замовлення ваучерів")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"#{self.pk} {self.voucher.name} — {self.buyer_email} [{self.status}]"
