import os

from django.core.management.base import BaseCommand
from django.core.management import call_command

from apps.pages.models import StaticPage

# Absolute path: …/poland/apps/core/management/commands/ → up 4 → …/poland/
_COMMANDS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_COMMANDS_DIR, *[".."] * 4))
_FIXTURE = os.path.join(_PROJECT_ROOT, "fixtures", "initial_data.json.gz")


class Command(BaseCommand):
    help = "Load fixtures only when DB is empty (idempotent)"

    def handle(self, *args, **options):
        if StaticPage.objects.exists():
            self.stdout.write("Data already loaded, skipping.")
            return
        if not os.path.exists(_FIXTURE):
            self.stderr.write(f"Fixture not found: {_FIXTURE}")
            return
        call_command("loaddata", _FIXTURE, verbosity=1)
        self.stdout.write(self.style.SUCCESS("Fixtures loaded successfully."))
