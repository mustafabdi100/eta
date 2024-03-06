# Generated by Django 5.0.2 on 2024-02-26 06:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0005_activitylog'),
    ]

    operations = [
        migrations.AddField(
            model_name='activitylog',
            name='deleted_user',
            field=models.CharField(blank=True, help_text='Username of the deleted user, if applicable.', max_length=150, null=True),
        ),
    ]