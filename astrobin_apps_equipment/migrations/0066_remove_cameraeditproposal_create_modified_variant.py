# Generated by Django 2.2.24 on 2022-05-24 07:10

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin_apps_equipment', '0065_add_unique_together_constraint_to_migration_records'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cameraeditproposal',
            name='create_modified_variant',
        ),
    ]
