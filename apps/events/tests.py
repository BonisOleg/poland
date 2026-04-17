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


LEGACY_CONTENT_HTML = """
<div><video autoplay loop muted></video></div>
<h2>Duplicate Hero Title</h2>
<a href="https://iframe423.biletyna.pl/event/view/id/1" target="_blank">
<span><span>KUP BILET 17:00</span></span>
</a>
<h2>Main description heading</h2>
<p>Opening paragraph with <strong>meaningful</strong> copy.</p>
<h3>● Szalona piana: wyrazisty eksperyment z setkami litrów piany</h3>
<h3>● Ciekły azot: mgła i wybuch azotowy</h3>
<div class="e-hosted-video">
  <video controls src="https://example.com/promo.mp4" poster="https://example.com/poster.jpg"></video>
</div>
<h2>Galeria</h2>
<div class="swiper" role="region">
  <div class="swiper-wrapper">
    <div class="swiper-slide"><figure><img alt="Photo1" data-src="https://example.com/img1.jpg"></figure></div>
    <div class="swiper-slide"><figure><img alt="Photo2" data-src="https://example.com/img2.jpg"></figure></div>
  </div>
  <div role="button" tabindex="0">
    <svg class="e-font-icon-svg e-eicon-chevron-left"><path d="M1"/></svg>
  </div>
  <div role="button" tabindex="0">
    <svg class="e-font-icon-svg e-eicon-chevron-right"><path d="M1"/></svg>
  </div>
  <div class="swiper-pagination"></div>
</div>
<h2>REKOMENDACJE​</h2>
<div class="swiper" role="region">
  <div class="swiper-wrapper">
    <div class="swiper-slide"><img data-src="https://example.com/recommend1.jpg"></div>
  </div>
</div>
<h2>5 POWODÓW</h2>
<ul class="content-icon-list">
  <li class="content-icon-list__item"><span class="content-icon-list__text">Świetna zabawa</span></li>
</ul>
<a href="https://example.com/more" target="_blank"><span><span>PRZEŻYJ EMOCJE</span></span></a>
"""


class EventDetailLegacyLayoutTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.city = City.objects.create(name="Warszawa", slug="warszawa")
        cls.event = Event.objects.create(
            title="Duplicate Hero Title",
            slug="legacy-layout-test",
        )
        cls.ec = EventCity.objects.create(
            event=cls.event,
            city=cls.city,
            slug="legacy-layout-test-wawa",
            is_published=True,
            use_new_layout=False,
            biletyna_url="https://iframe423.biletyna.pl/event/view/id/1",
            content_html=LEGACY_CONTENT_HTML,
        )

    def setUp(self):
        self.response = self.client.get(f"/{self.ec.slug}/")

    def test_returns_200(self):
        self.assertEqual(self.response.status_code, 200)

    def test_hero_and_schema_preserved(self):
        self.assertContains(self.response, 'class="hero__title-line"')
        self.assertContains(self.response, "Duplicate Hero Title")
        self.assertContains(self.response, '"@type": "Event"')
        self.assertContains(self.response, '"position": 1')
        self.assertContains(self.response, '"position": 3')

    def test_photo_gallery_uses_src_not_data_src(self):
        self.assertContains(self.response, "event-gallery--photo")
        self.assertContains(self.response, 'src="https://example.com/img1.jpg"')
        self.assertContains(self.response, 'src="https://example.com/img2.jpg"')
        self.assertNotContains(self.response, 'data-src="https://example.com/img1.jpg"')

    def test_video_section_rendered(self):
        self.assertContains(self.response, "event-gallery--video")
        self.assertContains(self.response, 'src="https://example.com/promo.mp4"')

    def test_elementor_cruft_stripped(self):
        self.assertNotContains(self.response, "e-eicon-chevron")
        self.assertNotContains(self.response, "swiper-slide")
        self.assertNotContains(self.response, "swiper-pagination")
        self.assertNotContains(self.response, "REKOMENDACJE")
        self.assertNotContains(self.response, "recommend1.jpg")

    def test_duplicate_cta_removed(self):
        body = self.response.content.decode()
        self.assertEqual(body.count("KUP BILET 17:00"), 0)

    def test_content_block_with_cta_rendered(self):
        self.assertContains(self.response, "event-content-block")
        self.assertContains(self.response, "5 POWODÓW")
        self.assertContains(self.response, "PRZEŻYJ EMOCJE")
        self.assertContains(self.response, "btn--outline-amber")


ORPHAN_CONTENT_HTML = """
<h2>Main description heading</h2>
<p>Important paragraph.</p>
<h2>Galeria</h2>
<p><img alt="DSC_3193"/></p>
<p><img alt="DG1P9985"/></p>
<p><img alt="IMG_0077"/></p>
"""

SIBLING_CONTENT_HTML = """
<h2>Main description heading</h2>
<p>Important paragraph.</p>
<h2>Galeria</h2>
<div class="swiper" role="region">
  <div class="swiper-wrapper">
    <div class="swiper-slide"><img alt="DSC_3193" data-src="https://sibling.example.com/a.jpg"></div>
    <div class="swiper-slide"><img alt="DG1P9985" data-src="https://sibling.example.com/b.jpg"></div>
  </div>
</div>
"""


class EventDetailOrphanImgTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.city = City.objects.create(name="Gdańsk", slug="gdansk-orphan")
        cls.event = Event.objects.create(title="Orphan Test", slug="orphan-test")
        cls.ec = EventCity.objects.create(
            event=cls.event,
            city=cls.city,
            slug="orphan-test-gdansk",
            is_published=True,
            use_new_layout=False,
            content_html=ORPHAN_CONTENT_HTML,
        )

    def test_orphan_images_do_not_leak_alt_text(self):
        response = self.client.get(f"/{self.ec.slug}/")
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()
        # Alt-only <img> without src/data-src must not render at all
        self.assertNotIn('alt="DSC_3193"', body)
        self.assertNotIn('alt="DG1P9985"', body)
        self.assertNotIn('alt="IMG_0077"', body)
        # No photo gallery without a real sibling fallback
        self.assertNotContains(response, "event-gallery--photo")


class EventDetailSiblingGalleryFallbackTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.city_a = City.objects.create(name="Szczecin", slug="szczecin-sib")
        cls.city_b = City.objects.create(name="Gdańsk", slug="gdansk-sib")
        cls.event = Event.objects.create(title="Sibling Test", slug="sibling-test")
        cls.sibling = EventCity.objects.create(
            event=cls.event,
            city=cls.city_a,
            slug="sibling-test-szczecin",
            is_published=True,
            use_new_layout=False,
            content_html=SIBLING_CONTENT_HTML,
        )
        cls.ec = EventCity.objects.create(
            event=cls.event,
            city=cls.city_b,
            slug="sibling-test-gdansk",
            is_published=True,
            use_new_layout=False,
            content_html=ORPHAN_CONTENT_HTML,
        )

    def test_sibling_gallery_falls_back_for_orphan_event(self):
        response = self.client.get(f"/{self.ec.slug}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "event-gallery--photo")
        self.assertContains(response, "https://sibling.example.com/a.jpg")
        self.assertContains(response, "https://sibling.example.com/b.jpg")
