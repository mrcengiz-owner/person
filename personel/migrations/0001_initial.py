import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Personel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ad_soyad", models.CharField(max_length=120, verbose_name="Ad Soyad")),
                (
                    "maas",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Aylık Maaş",
                    ),
                ),
                (
                    "maas_gunu",
                    models.PositiveSmallIntegerField(
                        default=1,
                        help_text="Her ay maaşın ödeneceği gün (1-28)",
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(28),
                        ],
                        verbose_name="Maaş Günü",
                    ),
                ),
                ("telefon", models.CharField(blank=True, max_length=20, verbose_name="Telefon")),
                ("notlar", models.TextField(blank=True, verbose_name="Notlar")),
                ("aktif", models.BooleanField(default=True, verbose_name="Aktif")),
                ("olusturulma", models.DateTimeField(auto_now_add=True)),
                ("guncellenme", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Personel",
                "verbose_name_plural": "Personeller",
                "ordering": ["ad_soyad"],
            },
        ),
        migrations.CreateModel(
            name="MuhasebeIslem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "tip",
                    models.CharField(
                        choices=[("avans", "Avans"), ("maas", "Maaş Ödemesi")],
                        max_length=10,
                        verbose_name="İşlem Tipi",
                    ),
                ),
                (
                    "tutar",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=12,
                        validators=[django.core.validators.MinValueValidator(0.01)],
                        verbose_name="Tutar",
                    ),
                ),
                ("tarih", models.DateField(verbose_name="Tarih")),
                ("aciklama", models.CharField(blank=True, max_length=255, verbose_name="Açıklama")),
                ("olusturulma", models.DateTimeField(auto_now_add=True)),
                (
                    "personel",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="islemler",
                        to="personel.personel",
                        verbose_name="Personel",
                    ),
                ),
            ],
            options={
                "verbose_name": "Muhasebe İşlemi",
                "verbose_name_plural": "Muhasebe İşlemleri",
                "ordering": ["-tarih", "-olusturulma"],
            },
        ),
    ]
