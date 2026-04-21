from django.db import migrations, models
from django.utils import timezone


def backfill_archived_events(apps, schema_editor):
    """Backfill is_archived=True for events from 2025 and earlier, or past events."""
    EventCity = apps.get_model("events", "EventCity")
    now = timezone.now()
    
    # Archive events from 2025 or earlier
    events_to_archive = EventCity.objects.filter(
        models.Q(event_date__year__lte=2025) | models.Q(event_date__lt=now)
    ).exclude(event_date__isnull=True)
    
    for event_city in events_to_archive:
        event_city.is_archived = True
        event_city.archive_date = now
    
    # Use bulk_update for efficiency
    EventCity.objects.bulk_update(
        events_to_archive,
        fields=["is_archived", "archive_date"],
        batch_size=1000
    )


def reverse_backfill(apps, schema_editor):
    """Reverse the backfill (unarchive all events)."""
    EventCity = apps.get_model("events", "EventCity")
    EventCity.objects.all().update(is_archived=False, archive_date=None)


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0010_eventcity_use_block_builder"),
    ]

    operations = [
        migrations.AddField(
            model_name="eventcity",
            name="is_archived",
            field=models.BooleanField(db_index=True, default=False, verbose_name="Zarchiwizowane"),
        ),
        migrations.AddField(
            model_name="eventcity",
            name="archive_date",
            field=models.DateTimeField(blank=True, db_index=True, null=True, verbose_name="Data archiwizacji"),
        ),
        migrations.RunPython(backfill_archived_events, reverse_backfill),
    ]
