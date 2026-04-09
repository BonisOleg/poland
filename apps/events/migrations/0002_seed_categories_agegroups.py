from django.db import migrations


CATEGORIES = [
    {"slug": "dla-dzieci",    "name_pl": "Dla dzieci",    "name_en": "For children", "sort_order": 1},
    {"slug": "dla-doroslych", "name_pl": "Dla dorosłych", "name_en": "For adults",   "sort_order": 2},
    {"slug": "spektakl",      "name_pl": "Spektakl",      "name_en": "Show",         "sort_order": 3},
    {"slug": "koncert",       "name_pl": "Koncert",       "name_en": "Concert",      "sort_order": 4},
    {"slug": "festiwal",      "name_pl": "Festiwal",      "name_en": "Festival",     "sort_order": 5},
    {"slug": "warsztat",      "name_pl": "Warsztat",      "name_en": "Workshop",     "sort_order": 6},
]

AGE_GROUPS = [
    {"slug": "dla-dzieci",    "name_pl": "Dla dzieci",    "name_en": "For children", "min_age": 0,  "max_age": 12},
    {"slug": "rodzinne",      "name_pl": "Rodzinne",      "name_en": "Family",       "min_age": 0,  "max_age": 99},
    {"slug": "dla-doroslych", "name_pl": "Dla dorosłych", "name_en": "For adults",   "min_age": 18, "max_age": 99},
]


def seed_categories_and_age_groups(apps, schema_editor):
    Category = apps.get_model("events", "Category")
    AgeGroup = apps.get_model("events", "AgeGroup")

    for data in CATEGORIES:
        Category.objects.get_or_create(
            slug=data["slug"],
            defaults={
                "name":      data["name_pl"],
                "name_pl":   data["name_pl"],
                "name_en":   data["name_en"],
                "sort_order": data["sort_order"],
            },
        )

    for data in AGE_GROUPS:
        AgeGroup.objects.get_or_create(
            slug=data["slug"],
            defaults={
                "name":    data["name_pl"],
                "name_pl": data["name_pl"],
                "name_en": data["name_en"],
                "min_age": data["min_age"],
                "max_age": data["max_age"],
            },
        )


def reverse_seed(apps, schema_editor):
    Category = apps.get_model("events", "Category")
    AgeGroup = apps.get_model("events", "AgeGroup")
    Category.objects.filter(slug__in=[d["slug"] for d in CATEGORIES]).delete()
    AgeGroup.objects.filter(slug__in=[d["slug"] for d in AGE_GROUPS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_categories_and_age_groups, reverse_code=reverse_seed),
    ]
