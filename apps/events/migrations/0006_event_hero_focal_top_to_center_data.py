# Data migration: legacy "top" focal showed only the upper band of photos; default UX is center.

from django.db import migrations


def forwards(apps, schema_editor):
    Event = apps.get_model("events", "Event")
    Event.objects.filter(hero_image_focal="top").update(hero_image_focal="center")


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0005_alter_event_hero_defaults_and_image_spec"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
