from django.urls import path
from . import views

app_name = "vouchers"

# Specific paths MUST come before the slug pattern to avoid being captured as slugs.
urlpatterns = [
    path("voucher/notify/", views.notify_view, name="notify"),
    path("voucher/sukces/", views.success_view, name="success"),
    path("voucher/anulowanie/", views.cancel_view, name="cancel"),
    path("voucher/<slug:slug>/", views.checkout_view, name="checkout"),
]
