"""
Management command: clean_event_content

Applies the full content transform (originally written for StaticPage) to
EventCity content fields, producing clean custom-class HTML with no
Elementor or WordPress block markup.

Fields cleaned: content_html, content_html_pl, content_html_en

Usage:
    python manage.py clean_event_content           # dry-run
    python manage.py clean_event_content --apply   # write to DB
    python manage.py clean_event_content --id 42 --apply
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.events.models import EventCity
from apps.pages.management.commands.clean_elementor_content import transform_html

CONTENT_FIELDS = ["content_html", "content_html_pl", "content_html_en"]


class Command(BaseCommand):
    help = "Strip Elementor/WP markup from EventCity content fields and replace with clean HTML"

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="Write changes to DB (default: dry-run)",
        )
        parser.add_argument(
            "--id",
            type=int,
            default=None,
            help="Process only EventCity with this pk",
        )

    def handle(self, *args, **options) -> None:
        apply: bool = options["apply"]
        pk: int | None = options["id"]

        qs = EventCity.objects.all()
        if pk is not None:
            qs = qs.filter(pk=pk)
            if not qs.exists():
                self.stderr.write(self.style.ERROR(f"No EventCity with id={pk}"))
                return

        mode = "APPLY" if apply else "DRY-RUN"
        self.stdout.write(self.style.WARNING(f"[{mode}] {qs.count()} record(s)\n"))

        changed_count = 0
        for obj in qs:
            updates: dict[str, str] = {}
            for field in CONTENT_FIELDS:
                original = getattr(obj, field) or ""
                cleaned = transform_html(original)
                if cleaned != original:
                    updates[field] = cleaned

            if updates:
                changed_count += 1
                self.stdout.write(
                    f"  {'CHANGED' if apply else 'WOULD CHANGE'}: "
                    f"pk={obj.pk} fields={list(updates)} — {obj}"
                )
                if apply:
                    for field, value in updates.items():
                        setattr(obj, field, value)
                    obj.save(update_fields=list(updates))
            else:
                self.stdout.write(f"  SKIP: pk={obj.pk}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n[{mode}] Done. {changed_count}/{qs.count()} record(s) "
                f"{'updated' if apply else 'would be updated'}."
            )
        )
