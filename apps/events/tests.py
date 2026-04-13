from datetime import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import City, Event, EventCity


class EventListViewTests(TestCase):
    def test_event_list_returns_200(self):
        response = self.client.get(reverse("events:list"))
        self.assertEqual(response.status_code, 200)


class EventListDateFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        tz = timezone.get_current_timezone()
        cls.city_waw = City.objects.create(name="Warszawa", slug="warszawa")
        cls.city_krk = City.objects.create(name="Kraków", slug="krakow")
        cls.event_a = Event.objects.create(title="Alpha", slug="alpha")
        cls.event_b = Event.objects.create(title="Beta", slug="beta")
        cls.ec_2026_mar_waw = EventCity.objects.create(
            event=cls.event_a,
            city=cls.city_waw,
            slug="alpha-wawa-2026-03",
            event_date=timezone.make_aware(datetime(2026, 3, 10, 20, 0), tz),
            is_published=True,
        )
        cls.ec_2026_apr_waw = EventCity.objects.create(
            event=cls.event_b,
            city=cls.city_waw,
            slug="beta-wawa-2026-04",
            event_date=timezone.make_aware(datetime(2026, 4, 5, 19, 0), tz),
            is_published=True,
        )
        cls.ec_2025_krk = EventCity.objects.create(
            event=cls.event_a,
            city=cls.city_krk,
            slug="alpha-krakow-2025-12",
            event_date=timezone.make_aware(datetime(2025, 12, 1, 18, 0), tz),
            is_published=True,
        )

    def _slugs_from_response(self, response):
        return [ec.slug for ec in response.context["page_obj"]]

    def test_filter_year_returns_events_in_that_year(self):
        response = self.client.get(reverse("events:list"), {"year": "2026"})
        slugs = self._slugs_from_response(response)
        self.assertIn(self.ec_2026_mar_waw.slug, slugs)
        self.assertIn(self.ec_2026_apr_waw.slug, slugs)
        self.assertNotIn(self.ec_2025_krk.slug, slugs)

    def test_filter_year_and_month(self):
        response = self.client.get(reverse("events:list"), {"year": "2026", "month": "3"})
        slugs = self._slugs_from_response(response)
        self.assertEqual(slugs, [self.ec_2026_mar_waw.slug])

    def test_filter_year_with_city(self):
        response = self.client.get(
            reverse("events:list"),
            {"year": "2026", "city": "warszawa"},
        )
        slugs = self._slugs_from_response(response)
        self.assertEqual(len(slugs), 2)
        self.assertNotIn(self.ec_2025_krk.slug, slugs)

    def test_legacy_date_param_exact_day(self):
        response = self.client.get(reverse("events:list"), {"date": "2026-03-10"})
        slugs = self._slugs_from_response(response)
        self.assertEqual(slugs, [self.ec_2026_mar_waw.slug])

    def test_year_param_takes_precedence_over_legacy_date(self):
        response = self.client.get(
            reverse("events:list"),
            {"year": "2026", "month": "4", "date": "2026-03-10"},
        )
        slugs = self._slugs_from_response(response)
        self.assertEqual(slugs, [self.ec_2026_apr_waw.slug])


class EventDetailHeroFocalTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.city = City.objects.create(name="Słupsk", slug="slupsk")
        cls.event = Event.objects.create(
            title="Hero focal test",
            slug="hero-focal-test",
            hero_image_focal="bottom",
        )
        cls.event_city = EventCity.objects.create(
            event=cls.event,
            city=cls.city,
            slug="hero-focal-test-slupsk",
            is_published=True,
            og_image="https://example.com/event-poster.jpg",
        )

    def test_detail_renders_data_hero_focal_bottom(self):
        response = self.client.get(f"/{self.event_city.slug}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'data-hero-focal="bottom"')
        self.assertContains(response, "event-detail__hero-layout")
        self.assertContains(response, "hero__media hero__media--bleed")
        self.assertContains(response, 'class="hero__title-line"')
        self.assertContains(response, "Hero focal test")
        self.assertContains(response, "hero__subtitle-line")
