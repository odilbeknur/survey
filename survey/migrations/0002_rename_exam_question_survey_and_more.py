# Generated by Django 5.1.4 on 2025-04-19 20:54

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('survey', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='question',
            old_name='exam',
            new_name='survey',
        ),
        migrations.RenameField(
            model_name='response',
            old_name='exam',
            new_name='survey',
        ),
    ]
