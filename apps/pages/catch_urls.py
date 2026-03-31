from django.urls import path
from . import views

urlpatterns = [
    path("", views.catch_all_page, name="catch-all"),
]
