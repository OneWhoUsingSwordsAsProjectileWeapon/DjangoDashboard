# Generated by Django 5.2.3 on 2025-06-11 02:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('moderation', '0005_alter_usercomplaint_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='listingapproval',
            name='has_verification_video',
            field=models.BooleanField(default=False, verbose_name='Has Verification Video'),
        ),
    ]
