from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("personel", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="personel",
            name="mesai_giris",
            field=models.TimeField(
                default="09:00",
                help_text="Günlük işe giriş saati",
                verbose_name="Mesai Giriş",
            ),
        ),
        migrations.AddField(
            model_name="personel",
            name="mesai_cikis",
            field=models.TimeField(
                default="18:00",
                help_text="Günlük işten çıkış saati",
                verbose_name="Mesai Çıkış",
            ),
        ),
    ]
