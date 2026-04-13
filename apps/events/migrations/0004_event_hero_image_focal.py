# Generated manually for hero_image_focal

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0003_event_duration_event_language_spoken_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="hero_image_focal",
            field=models.CharField(
                choices=[("top", "Top"), ("center", "Center"), ("bottom", "Bottom")],
                default="top",
                help_text="Vertical crop focus for the event detail hero image (object-position).",
                max_length=20,
            ),
        ),
    ]
