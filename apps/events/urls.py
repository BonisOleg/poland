from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.event_list, name="list"),
    path("filter/", views.event_filter, name="filter"),
    path("archiwum/", views.archive_event_list, name="archive"),
]
