# Generated by Django 2.2.24 on 2022-03-17 09:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('astrobin', '0141_add_deepsky_acuisition_f_number'),
    ]

    operations = [

        migrations.AlterField(
            model_name='solarsystem_acquisition',
            name='exposure_per_frame',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=7, null=True, verbose_name='Exposure per frame (ms)'),
        ),
    ]
