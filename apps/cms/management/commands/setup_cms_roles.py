"""Create / refresh the standard CMS auth groups.

Idempotent — safe to run repeatedly (post-deploy, locally).

Groups
------
- ContentManager: full CRUD on CMS / pages / blog / events content models.
- Moderator: read + change (no add/delete) on the same models, plus full
  CRUD on Reviews (moderation workflow).
- Admin = Django superuser (no group needed).
"""

from __future__ import annotations

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


CONTENT_MANAGER_MODELS = [
    ("cms", "pageblock"),
    ("cms", "galleryitem"),
    ("cms", "relateditem"),
    ("pages", "staticpage"),
    ("pages", "pagemedia"),
    ("blog", "article"),
    ("events", "eventcity"),
    ("events", "event"),
    ("events", "eventimage"),
    ("events", "eventvideo"),
    ("events", "eventcontentblock"),
    ("vouchers", "voucher"),
]

CONTENT_MANAGER_PERMS = ("add", "change", "delete", "view")

MODERATOR_MODELS = [
    ("cms", "pageblock"),
    ("pages", "staticpage"),
    ("blog", "article"),
    ("events", "eventcity"),
    ("reviews", "review"),
]

MODERATOR_PERMS = ("change", "view")
MODERATOR_FULL_MODELS = [("reviews", "review")]


def _perm(app_label: str, model: str, action: str) -> Permission | None:
    try:
        ct = ContentType.objects.get(app_label=app_label, model=model)
    except ContentType.DoesNotExist:
        return None
    codename = f"{action}_{model}"
    return Permission.objects.filter(content_type=ct, codename=codename).first()


def _collect(model_list, actions) -> list[Permission]:
    out: list[Permission] = []
    for app_label, model in model_list:
        for action in actions:
            perm = _perm(app_label, model, action)
            if perm is not None:
                out.append(perm)
    return out


class Command(BaseCommand):
    help = "Create / refresh CMS auth groups (ContentManager, Moderator)."

    def handle(self, *args, **options):
        cm_perms = _collect(CONTENT_MANAGER_MODELS, CONTENT_MANAGER_PERMS)
        cm_group, _ = Group.objects.get_or_create(name="ContentManager")
        cm_group.permissions.set(cm_perms)
        self.stdout.write(self.style.SUCCESS(
            f"ContentManager: {len(cm_perms)} permissions assigned."
        ))

        mod_perms = _collect(MODERATOR_MODELS, MODERATOR_PERMS)
        mod_perms += _collect(MODERATOR_FULL_MODELS, ("add", "delete"))
        mod_group, _ = Group.objects.get_or_create(name="Moderator")
        mod_group.permissions.set(mod_perms)
        self.stdout.write(self.style.SUCCESS(
            f"Moderator: {len(mod_perms)} permissions assigned."
        ))

        self.stdout.write(self.style.SUCCESS(
            "Done. Assign users via django admin → Użytkownicy → Grupy."
        ))
