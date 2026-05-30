import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("personel", "0002_personel_mesai_saatleri"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="personel",
            name="olusturan",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="olusturdugu_personeller",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Oluşturan",
            ),
        ),
        migrations.AddField(
            model_name="personel",
            name="guncelleyen",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="guncelledigi_personeller",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Son güncelleyen",
            ),
        ),
        migrations.AddField(
            model_name="muhasebeislem",
            name="guncellenme",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="muhasebeislem",
            name="guncelleyen",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="guncelledigi_muhasebe_islemleri",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Son güncelleyen",
            ),
        ),
        migrations.AddField(
            model_name="muhasebeislem",
            name="kaydeden",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="kaydettigi_muhasebe_islemleri",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Kaydeden",
            ),
        ),
    ]
