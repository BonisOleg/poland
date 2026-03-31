from django.urls import path
from . import feeds

urlpatterns = [
    path("google.xml", feeds.google_feed, name="feed-google"),
    path("meta.xml", feeds.meta_feed, name="feed-meta"),
    path("edrone.json", feeds.edrone_feed, name="feed-edrone"),
]
