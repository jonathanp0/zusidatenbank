# Generated by Django 2.2.12 on 2024-03-31 17:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datenbank', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='fahrplanzug',
            name='gnt_aktiv',
            field=models.BooleanField(default=False, verbose_name='GNT Aktiv'),
        ),
    ]
