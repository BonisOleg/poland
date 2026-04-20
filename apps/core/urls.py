from django.urls import path

from apps.pages import inquiry_views

from . import views

app_name = "core"

urlpatterns = [
    path("", views.homepage, name="homepage"),
    path("search/", views.search, name="search"),
    path("group-inquiry/", inquiry_views.group_inquiry_submit, name="group_inquiry"),
    path("contact/", inquiry_views.contact_submit, name="contact_submit"),
]
