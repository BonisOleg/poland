import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update admin user from DJANGO_ADMIN_USERNAME / DJANGO_ADMIN_PASSWORD"

    def handle(self, *args, **options):
        username = (os.environ.get("DJANGO_ADMIN_USERNAME") or "admin").strip()
        password = (os.environ.get("DJANGO_ADMIN_PASSWORD") or "admin").strip()
        email = (os.environ.get("DJANGO_ADMIN_EMAIL") or "").strip() or f"{username}@example.com"

        User = get_user_model()
        user, created = User.objects.update_or_create(
            username=username,
            defaults={
                "email": email,
                "is_active": True,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        user.set_password(password)
        user.save(update_fields=["password"])

        action = "Created" if created else "Updated password for"
        self.stdout.write(self.style.SUCCESS(f"ensure_superuser: {action} {username!r}"))
