from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pages', '0002_staticpage_keywords_staticpage_keywords_en_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='staticpage',
            name='layout_version',
            field=models.CharField(
                choices=[('v1', 'Класична'), ('v2', 'Галерея (нова)')],
                default='v1',
                max_length=10,
            ),
        ),
    ]
