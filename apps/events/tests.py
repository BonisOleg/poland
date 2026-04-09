from django.test import TestCase
from django.urls import reverse


class EventListViewTests(TestCase):
    def test_event_list_returns_200(self):
        response = self.client.get(reverse("events:list"))
        self.assertEqual(response.status_code, 200)
