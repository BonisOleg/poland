from django.db import migrations, models


def reset_v2_to_v1(apps, schema_editor):
    StaticPage = apps.get_model("pages", "StaticPage")
    StaticPage.objects.filter(layout_version="v2").update(layout_version="v1")


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0004_pagemedia"),
    ]

    operations = [
        migrations.RunPython(reset_v2_to_v1, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="staticpage",
            name="layout_version",
            field=models.CharField(
                choices=[("v1", "Класична")],
                default="v1",
                max_length=10,
            ),
        ),
    ]
