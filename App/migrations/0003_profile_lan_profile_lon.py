# Generated by Django 5.0 on 2025-05-17 02:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('App', '0002_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='lan',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='profile',
            name='lon',
            field=models.IntegerField(default=0),
        ),
    ]
