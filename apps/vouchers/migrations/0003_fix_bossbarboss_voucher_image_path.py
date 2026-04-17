from django.db import migrations, models


WRONG = "vouchers/bossbarboss_happy_Slovenian_child_traveler_receives_a_gift_cart_c384b8cb-cb4a-4_c8nxrtw.png"
RIGHT = "vouchers/bossbarboss_happy_Slovenian_child_traveler_receives_a_gift_cart_c384b8cb-cb4a-489c-af5e-75543d361b0a.png"


def forwards(apps, schema_editor):
    Voucher = apps.get_model("vouchers", "Voucher")
    Voucher.objects.filter(image=WRONG).update(image=RIGHT)


def backwards(apps, schema_editor):
    Voucher = apps.get_model("vouchers", "Voucher")
    Voucher.objects.filter(image=RIGHT).update(image=WRONG)


class Migration(migrations.Migration):
    dependencies = [
        ("vouchers", "0002_voucherorder"),
    ]

    operations = [
        migrations.AlterField(
            model_name="voucher",
            name="image",
            field=models.ImageField(
                blank=True,
                max_length=255,
                null=True,
                upload_to="vouchers/",
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
