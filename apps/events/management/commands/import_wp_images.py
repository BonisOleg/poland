import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from apps.events.models import Event, EventCity, EventImage

BASE = "https://hypeglobal.pro/wp-content/uploads"

# event_id → WP image URL  (sets Event.image; skip if already set)
EVENT_MAIN_IMAGES = {
    10:  f"{BASE}/2026/03/APHKHAZETI-_big_dee_70.jpg",
    8:   f"{BASE}/2026/03/5.-Morandi.jpg",
    9:   f"{BASE}/2026/03/5.-Morandi.jpg",
    11:  f"{BASE}/2026/03/5.-Morandi.jpg",
    12:  f"{BASE}/2026/03/UOKRSZULA-MIX-by-Krzys-Mazurkiewicz.jpg",
    13:  f"{BASE}/2026/03/UOKRSZULA-MIX-by-Krzys-Mazurkiewicz.jpg",
    6:   f"{BASE}/2026/02/Danse-Danse-Paris-Teatr-Nowy-w-Zabrzu-i-Scena-czerwiec-2025-fot-Pawel-JaNic-Janicki-1141.jpg",
    18:  f"{BASE}/2026/02/HGDisco80.jpg",
    118: f"{BASE}/2026/03/HGDisco.jpg",
    14:  f"{BASE}/2026/02/Esteriore-Brothers-31.png",
    55:  f"{BASE}/2026/02/Esteriore-Brothers-31.png",
}

_APHKHAZETI_GALLERY = [
    f"{BASE}/2026/03/APHKHAZETI-_big_dee_25.jpg",
    f"{BASE}/2026/03/APHKHAZETI-small-22.jpg",
    f"{BASE}/2026/03/APHKHAZETI-small-10.jpg",
    f"{BASE}/2026/03/APHKHAZETI-small-6.jpg",
    f"{BASE}/2026/03/APHKHAZETI-_small_dee_56.jpg",
    f"{BASE}/2026/03/APHKHAZETI-_big_dee_259.jpg",
    f"{BASE}/2026/03/APHKHAZETI-_big_dee_257.jpg",
    f"{BASE}/2026/03/APHKHAZETI-_big_dee_253.jpg",
    f"{BASE}/2026/03/APHKHAZETI-_big_dee_251.jpg",
    f"{BASE}/2026/03/APHKHAZETI-_big_dee_250.jpg",
    f"{BASE}/2026/03/APHKHAZETI-_big_dee_161.jpg",
    f"{BASE}/2026/03/APHKHAZETI-_big_dee_112.jpg",
    f"{BASE}/2026/03/APHKHAZETI-_big_dee_72.jpg",
]

_MORANDI_GALLERY = [
    f"{BASE}/2026/03/1.-Morandi.jpg",
    f"{BASE}/2026/03/2.-Morandi-scaled.jpg",
    f"{BASE}/2026/03/3.-Morandi-scaled.jpg",
    f"{BASE}/2026/03/4.-Morandi-scaled.jpg",
]

_HGDISCO80_GALLERY = [
    f"{BASE}/2026/02/Sandra-Band001.jpg",
    f"{BASE}/2026/02/Band008.jpg",
    f"{BASE}/2026/02/Band003.jpg",
    f"{BASE}/2026/02/Sandra-Band016.jpg",
    f"{BASE}/2026/02/Sandra-Band002.jpg",
    f"{BASE}/2026/02/BoneyM-327.jpg",
    f"{BASE}/2026/02/BoneyM-326.jpg",
    f"{BASE}/2026/02/BoneyM-325.jpeg",
    f"{BASE}/2026/02/BoneyM-323.jpg",
    f"{BASE}/2026/02/BoneyM-321.jpg",
    f"{BASE}/2026/02/LONDONBEAT_RO24.jpg",
    f"{BASE}/2026/02/LONDONBEAT_PRO25.jpg",
    f"{BASE}/2026/02/LONDONBEAT_PRO24.jpg",
    f"{BASE}/2026/02/LONDONBEAT_Pop25.jpg",
    f"{BASE}/2026/02/Londonbeat_by-Marie-Staggat_.jpg",
]

_DANSE_PARIS_GALLERY = [
    f"{BASE}/2026/02/Danse-Danse-Paris-Teatr-Nowy-w-Zabrzu-i-Scena-czerwiec-2025-fot-Pawel-JaNic-Janicki-1141.jpg",
    f"{BASE}/2026/02/Danse-Danse-Paris-Teatr-Nowy-w-Zabrzu-i-Scena-czerwiec-2025-fot-Pawel-JaNic-Janicki-1113.jpg",
    f"{BASE}/2026/02/Danse-Danse-Paris-Teatr-Nowy-w-Zabrzu-i-Scena-czerwiec-2025-fot-Pawel-JaNic-Janicki-1076.jpg",
    f"{BASE}/2026/02/Danse-Danse-Paris-Teatr-Nowy-w-Zabrzu-i-Scena-czerwiec-2025-fot-Pawel-JaNic-Janicki-891.jpg",
    f"{BASE}/2026/02/Danse-Danse-Paris-Teatr-Nowy-w-Zabrzu-i-Scena-czerwiec-2025-fot-Pawel-JaNic-Janicki-643.jpg",
    f"{BASE}/2026/02/Danse-Danse-Paris-Teatr-Nowy-w-Zabrzu-i-Scena-czerwiec-2025-fot-Pawel-JaNic-Janicki-634.jpg",
    f"{BASE}/2026/02/Danse-Danse-Paris-Teatr-Nowy-w-Zabrzu-i-Scena-czerwiec-2025-fot-Pawel-JaNic-Janicki-597.jpg",
]

_FIAT_GALLERY = [
    f"{BASE}/2026/02/DSC_8733.jpg",
    f"{BASE}/2026/02/DSC_8782.jpg",
    f"{BASE}/2026/02/DSC_9182.jpg",
    f"{BASE}/2026/02/DSC_9630.jpg",
]

# event_city_id → list of WP image URLs  (adds EventImage records; skips duplicates)
GALLERY_IMAGES = {
    56: _APHKHAZETI_GALLERY,
    54: _MORANDI_GALLERY,
    55: _MORANDI_GALLERY,
    57: _MORANDI_GALLERY,
    80: _HGDISCO80_GALLERY,
    69: _DANSE_PARIS_GALLERY,
    79: _FIAT_GALLERY,
}


def _fetch(url: str, stdout) -> bytes | None:
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.content
    except Exception as exc:
        stdout.write(f"  ERROR fetching {url}: {exc}")
        return None


class Command(BaseCommand):
    help = "Import WP images (2026-02/03) into Event.image and EventImage gallery"

    def handle(self, *args, **options):
        self._import_event_images()
        self._import_gallery_images()
        self.stdout.write(self.style.SUCCESS("Done."))

    def _import_event_images(self):
        self.stdout.write("=== Event.image ===")
        for event_id, url in EVENT_MAIN_IMAGES.items():
            try:
                event = Event.objects.get(pk=event_id)
            except Event.DoesNotExist:
                self.stdout.write(f"  Event[{event_id}] NOT FOUND — skip")
                continue

            if event.image:
                self.stdout.write(f"  Event[{event_id}] already has image — skip")
                continue

            filename = url.split("/")[-1]
            self.stdout.write(f"  Event[{event_id}] {event.title[:40]} ← {filename}")
            data = _fetch(url, self.stdout)
            if data is None:
                continue
            event.image.save(filename, ContentFile(data), save=True)
            self.stdout.write(f"    saved → {event.image.name}")

    def _import_gallery_images(self):
        self.stdout.write("=== EventImage gallery ===")
        for city_id, urls in GALLERY_IMAGES.items():
            try:
                ec = EventCity.objects.get(pk=city_id)
            except EventCity.DoesNotExist:
                self.stdout.write(f"  EventCity[{city_id}] NOT FOUND — skip")
                continue

            existing_alts = set(
                EventImage.objects.filter(event_city=ec).values_list("alt_text", flat=True)
            )
            next_order = EventImage.objects.filter(event_city=ec).count()

            self.stdout.write(f"  EventCity[{city_id}] {ec} ({len(urls)} images)")
            for i, url in enumerate(urls):
                filename = url.split("/")[-1]
                alt = filename.rsplit(".", 1)[0]

                if alt in existing_alts:
                    self.stdout.write(f"    {filename} — already exists, skip")
                    continue

                data = _fetch(url, self.stdout)
                if data is None:
                    continue

                img = EventImage(
                    event_city=ec,
                    alt_text=alt,
                    sort_order=next_order + i,
                )
                img.image.save(filename, ContentFile(data), save=True)
                existing_alts.add(alt)
                self.stdout.write(f"    saved → {img.image.name}")
