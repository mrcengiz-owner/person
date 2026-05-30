from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("personel", "0003_kullanici_izleri"),
    ]

    operations = [
        migrations.AddField(
            model_name="muhasebeislem",
            name="alici_adi",
            field=models.CharField(
                blank=True,
                help_text="Personel dışı masraflar için (tedarikçi, kira vb.)",
                max_length=120,
                verbose_name="Alıcı / Firma",
            ),
        ),
        migrations.AlterField(
            model_name="muhasebeislem",
            name="personel",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="islemler",
                to="personel.personel",
                verbose_name="Personel",
            ),
        ),
        migrations.AlterField(
            model_name="muhasebeislem",
            name="tip",
            field=models.CharField(
                choices=[
                    ("masraf", "Masraf"),
                    ("avans", "Avans"),
                    ("maas", "Maaş Ödemesi"),
                ],
                max_length=10,
                verbose_name="İşlem Tipi",
            ),
        ),
    ]
