# Generated by Django 5.1.4 on 2024-12-06 12:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0003_choice_requires_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='choice',
            name='description',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]