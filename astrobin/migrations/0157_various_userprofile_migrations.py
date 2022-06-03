# Generated by Django 2.2.24 on 2022-06-03 11:50

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('astrobin', '0156_various_location_migrations'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='auto_submit_to_iotd_tp_process',
            field=models.BooleanField(
                default=False,
                help_text='Check this box to automatically submit your images for <a href="https://welcome.astrobin.com/iotd" target="_blank">IOTD/TP</a> consideration when they are published.',
                verbose_name='Automatically submit images for IOTD/TP consideration'
            ),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='default_frontpage_section',
            field=models.CharField(
                choices=[
                    ('global', 'Global stream'),
                    ('personal', 'Personal stream'),
                    ('recent', 'All uploaded images'),
                    ('followed', 'All images uploaded by people you follow')],
                default='global', max_length=16, verbose_name='Default front page view'
            ),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='default_license',
            field=models.CharField(
                choices=[
                    ('ALL_RIGHTS_RESERVED', 'None (All rights reserved)'),
                    ('ATTRIBUTION_NON_COMMERCIAL_SHARE_ALIKE', 'Attribution-NonCommercial-ShareAlike Creative Commons'),
                    ('ATTRIBUTION_NON_COMMERCIAL', 'Attribution-NonCommercial Creative Commons'),
                    ('ATTRIBUTION_NON_COMMERCIAL_NO_DERIVS', 'Attribution-NonCommercial-NoDerivs Creative Commons'),
                    ('ATTRIBUTION', 'Attribution Creative Commons'),
                    ('ATTRIBUTION_SHARE_ALIKE', 'Attribution-ShareAlike Creative Commons'),
                    ('ATTRIBUTION_NO_DERIVS', 'Attribution-NoDerivs Creative Commons')
                ],
                default='ALL_RIGHTS_RESERVED',
                help_text='The license you select here is automatically applied to all your new images.',
                max_length=40,
                verbose_name='Default license'
            ),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='language',
            field=models.CharField(
                blank=True,
                choices=[
                    ('en', 'English (US)'),
                    ('en-GB', 'English (GB)'),
                    ('it', 'Italian'),
                    ('es', 'Spanish'),
                    ('fr', 'French'),
                    ('fi', 'Finnish'),
                    ('de', 'German'),
                    ('nl', 'Dutch'),
                    ('tr', 'Turkish'),
                    ('sq', 'Albanian'),
                    ('pl', 'Polish'),
                    ('pt', 'Portuguese'),
                    ('el', 'Greek'),
                    ('uk', 'Ukrainian'),
                    ('ru', 'Russian'),
                    ('ar', 'Arabic'),
                    ('ja', 'Japanese')
                ],
                max_length=8,
                null=True,
                verbose_name='Language'
            ),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='open_notifications_in_new_tab',
            field=models.NullBooleanField(verbose_name='Open notifications in a new tab'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='show_signatures',
            field=models.BooleanField(blank=True, default=True, verbose_name='Show signatures'),
        ),
    ]
