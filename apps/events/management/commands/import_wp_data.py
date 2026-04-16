import json
import os
import re
import shutil
from datetime import datetime

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify
from html import unescape

from apps.events.models import AgeGroup, Category, City, Event, EventCity
from apps.pages.models import StaticPage
from apps.vouchers.models import Voucher
from apps.vouchers.utils import fetch_url_bytes, voucher_image_filename_from_url

# Slug-pattern → category slug + age_group slug
SLUG_CATEGORY_MAP = [
    ("dzieci",  "dla-dzieci",    "dla-dzieci"),
    ("dorosl",  "dla-doroslych", "dla-doroslych"),
]

# event_type choice value → category slug (fallback when no slug match)
EVENT_TYPE_CATEGORY_MAP = {
    "spektakl": "spektakl",
    "koncert":  "koncert",
    "festiwal": "festiwal",
    "warsztat": "warsztat",
}

POLISH_CITIES = {
    "warszawa": "Warszawa", "krakow": "Kraków", "gdansk": "Gdańsk",
    "wroclaw": "Wrocław", "poznan": "Poznań", "lodz": "Łódź",
    "katowice": "Katowice", "szczecin": "Szczecin", "bydgoszcz": "Bydgoszcz",
    "lublin": "Lublin", "bialystok": "Białystok", "rzeszow": "Rzeszów",
    "torun": "Toruń", "kielce": "Kielce", "olsztyn": "Olsztyn",
    "opole": "Opole", "gdynia": "Gdynia", "sopot": "Sopot",
    "slupsk": "Słupsk", "koszalin": "Koszalin", "siedlce": "Siedlce",
    "lomza": "Łomża", "leszno": "Leszno", "radom": "Radom",
    "plock": "Płock", "tarnow": "Tarnów", "zielona-gora": "Zielona Góra",
    "wloclawek": "Włocławek", "grudziadz": "Grudziądz", "legnica": "Legnica",
    "elblag": "Elbląg", "stalowa-wola": "Stalowa Wola",
    "bielsko-biala": "Bielsko-Biała", "nowy-targ": "Nowy Targ",
    "tychy": "Tychy", "zabrze": "Zabrze", "gliwice": "Gliwice",
    "czestochowa": "Częstochowa", "sosnowiec": "Sosnowiec",
    "bielany-wroclawskie": "Bielany Wrocławskie",
    "nowy-sacz": "Nowy Sącz", "konin": "Konin", "kalisz": "Kalisz",
    "przemysl": "Przemyśl", "suwałki": "Suwałki", "suwalki": "Suwałki",
    "tarnobrzeg": "Tarnobrzeg", "zamość": "Zamość", "zamosc": "Zamość",
}

STATIC_SLUGS = {
    "regulaminy", "vouchery", "shop", "cart", "checkout", "my-account",
    "dla-szkol", "dla-firm", "dla-dzieci", "polityka-prywatnosci",
    "refund_returns", "eventy", "warsztaty", "bilety-na-wydarzenia-teatr-koncerty-spektakle-widowiska-w-twoim-miescie",
}

# WooCommerce product category slug for gift vouchers (not concerts / other products).
WOOCOMMERCE_VOUCHER_CATEGORY_SLUG = "voucher"


class Command(BaseCommand):
    help = "Import pages from scraped WordPress data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-dir",
            default=os.path.join(settings.BASE_DIR, "scraped_data"),
            help="Path to scraped_data directory",
        )
        parser.add_argument(
            "--force-voucher-images",
            action="store_true",
            help="Re-download voucher images even if already set",
        )

    def handle(self, *args, **options):
        data_dir = options["data_dir"]
        # Pre-load lookups so every page-loop doesn't hit the DB
        self._categories = {c.slug: c for c in Category.objects.all()}
        self._age_groups = {a.slug: a for a in AgeGroup.objects.all()}
        self.import_pages(data_dir)
        self.import_products(data_dir, force_voucher_images=options["force_voucher_images"])
        self.import_menus(data_dir)
        self.stdout.write(self.style.SUCCESS("Import complete!"))

    def import_pages(self, data_dir):
        pages_file = os.path.join(data_dir, "pages.json")
        if not os.path.exists(pages_file):
            self.stderr.write(f"File not found: {pages_file}")
            return

        with open(pages_file, "r", encoding="utf-8") as f:
            pages = json.load(f)

        self.stdout.write(f"Importing {len(pages)} pages...")

        events_created = 0
        ec_created = 0
        static_created = 0
        skipped = 0

        for page in pages:
            slug = page.get("slug", "")
            if not slug:
                skipped += 1
                continue

            title = self._clean_html(page.get("title", ""))
            yoast = page.get("yoast_seo", {})
            content = page.get("content_html", "")

            if slug in STATIC_SLUGS:
                StaticPage.objects.update_or_create(
                    slug=slug,
                    defaults={
                        "title_pl": title,
                        "content_pl": content,
                        "seo_title_pl": yoast.get("title", ""),
                        "seo_description_pl": yoast.get("description", ""),
                        "is_published": True,
                    },
                )
                static_created += 1
                continue

            event_prefix, city_slug = self._split_slug(slug)
            if not event_prefix:
                StaticPage.objects.update_or_create(
                    slug=slug,
                    defaults={
                        "title_pl": title,
                        "content_pl": content,
                        "seo_title_pl": yoast.get("title", ""),
                        "seo_description_pl": yoast.get("description", ""),
                        "is_published": True,
                    },
                )
                static_created += 1
                continue

            event, created = Event.objects.get_or_create(
                slug=event_prefix,
                defaults={
                    "title_pl": self._event_title_from_prefix(event_prefix, title),
                    "is_active": True,
                },
            )
            if created:
                events_created += 1

            self._assign_category_and_age(event, event_prefix)

            city = None
            if city_slug:
                city_name = POLISH_CITIES.get(city_slug, city_slug.replace("-", " ").title())
                city, _ = City.objects.get_or_create(
                    slug=city_slug,
                    defaults={"name": city_name},
                )

            if not city:
                city, _ = City.objects.get_or_create(
                    slug="ogolne",
                    defaults={"name": "Ogólne"},
                )

            og_images = yoast.get("og_image", [])
            og_url = ""
            if og_images and isinstance(og_images, list) and len(og_images) > 0:
                og_url = og_images[0].get("url", "")

            date_str = self._extract_date_from_title(title)

            EventCity.objects.update_or_create(
                slug=slug,
                defaults={
                    "event": event,
                    "city": city,
                    "custom_title_pl": title,
                    "content_html_pl": content,
                    "seo_title_pl": yoast.get("title", ""),
                    "seo_description_pl": yoast.get("description", ""),
                    "og_image": og_url,
                    "canonical_url": yoast.get("canonical", ""),
                    "event_date": date_str,
                    "is_published": True,
                },
            )
            ec_created += 1

        self.stdout.write(
            f"  Events: {events_created}, EventCities: {ec_created}, "
            f"Static: {static_created}, Skipped: {skipped}"
        )

    def import_products(self, data_dir, *, force_voucher_images=False):
        products_file = os.path.join(data_dir, "products.json")
        if not os.path.exists(products_file):
            return

        with open(products_file, "r", encoding="utf-8") as f:
            products = json.load(f)

        count = 0
        images_ok = 0
        deactivated = 0
        for p in products:
            name = p.get("name", "")
            slug = slugify(name)
            prices = p.get("prices", {})
            price_raw = prices.get("price", "0")
            price = int(price_raw) / 100 if price_raw else 0

            if not self._is_woocommerce_voucher_product(p):
                n = Voucher.objects.filter(slug=slug).update(is_active=False)
                if n:
                    deactivated += n
                continue

            voucher, _ = Voucher.objects.update_or_create(
                slug=slug,
                defaults={
                    "name_pl": name,
                    "price": price,
                    "currency": prices.get("currency_code", "PLN"),
                    "is_active": True,
                },
            )
            if self._attach_voucher_image_from_product(
                voucher, p, force=force_voucher_images
            ):
                images_ok += 1
            count += 1

        self.stdout.write(f"  Products/Vouchers: {count}")
        self.stdout.write(f"  Non-voucher rows deactivated: {deactivated}")
        self.stdout.write(f"  Voucher images downloaded: {images_ok}")

    def _is_woocommerce_voucher_product(self, product):
        """True if product is in WooCommerce category ``voucher`` (excludes concerts, tests, etc.)."""
        for cat in product.get("categories") or []:
            if cat.get("slug") == WOOCOMMERCE_VOUCHER_CATEGORY_SLUG:
                return True
        return False

    def _attach_voucher_image_from_product(self, voucher, product, *, force):
        """Save first WooCommerce product image to ``voucher.image`` when available."""
        imgs = product.get("images") or []
        if not imgs:
            return False
        src = imgs[0].get("src")
        if not src:
            return False
        if voucher.image and not force:
            return False
        try:
            data = fetch_url_bytes(src)
        except requests.RequestException as exc:
            self.stderr.write(f"  Voucher image failed [{voucher.slug}]: {exc}")
            return False
        filename = voucher_image_filename_from_url(src, voucher.slug)
        if voucher.image and force:
            voucher.image.delete(save=False)
        voucher.image.save(filename, ContentFile(data), save=True)
        return True

    def import_menus(self, data_dir):
        menus_file = os.path.join(data_dir, "menus.json")
        if not os.path.exists(menus_file):
            return

        with open(menus_file, "r", encoding="utf-8") as f:
            menus = json.load(f)

        self.stdout.write(f"  Menu items: {len(menus)}")

    def _assign_category_and_age(self, event, event_prefix):
        cat_slug = None
        age_slug = None

        for keyword, c_slug, a_slug in SLUG_CATEGORY_MAP:
            if keyword in event_prefix:
                cat_slug, age_slug = c_slug, a_slug
                break

        if cat_slug is None:
            et_slug = EVENT_TYPE_CATEGORY_MAP.get(event.event_type)
            if et_slug:
                cat_slug = et_slug

        if cat_slug and cat_slug in self._categories:
            event.categories.add(self._categories[cat_slug])

        if age_slug and age_slug in self._age_groups:
            if event.age_group_id is None:
                event.age_group = self._age_groups[age_slug]
                event.save(update_fields=["age_group"])

    def _split_slug(self, slug):
        for city_slug in sorted(POLISH_CITIES.keys(), key=len, reverse=True):
            if slug.endswith(f"-{city_slug}"):
                prefix = slug[: -(len(city_slug) + 1)]
                if prefix:
                    return prefix, city_slug

        suffix_patterns = [
            r"-w-(.+)$",
            r"-(\w+\d+)$",
        ]
        for pat in suffix_patterns:
            m = re.search(pat, slug)
            if m:
                city_candidate = m.group(1)
                if city_candidate in POLISH_CITIES:
                    prefix = slug[: m.start()]
                    return prefix, city_candidate

        return slug, ""

    def _event_title_from_prefix(self, prefix, full_title):
        city_names = list(POLISH_CITIES.values())
        title = full_title
        for cname in city_names:
            title = title.replace(f" w {cname}", "").replace(f" - {cname}", "")
        date_pattern = r"\d{1,2}\s+\w+\s+\d{4}r?\."
        title = re.sub(date_pattern, "", title).strip()
        return title if title else prefix.upper()

    def _extract_date_from_title(self, title):
        months_pl = {
            "stycznia": 1, "lutego": 2, "marca": 3, "kwietnia": 4,
            "maja": 5, "czerwca": 6, "lipca": 7, "sierpnia": 8,
            "września": 9, "października": 10, "listopada": 11, "grudnia": 12,
        }
        pattern = r"(\d{1,2})\s+(\w+)\s+(\d{4})"
        match = re.search(pattern, title)
        if match:
            day = int(match.group(1))
            month_name = match.group(2).lower()
            year = int(match.group(3))
            month = months_pl.get(month_name)
            if month:
                try:
                    return datetime(year, month, day, 19, 0)
                except ValueError:
                    pass
        return None

    def _clean_html(self, text):
        text = unescape(text)
        text = re.sub(r"<[^>]+>", "", text)
        return text.strip()
