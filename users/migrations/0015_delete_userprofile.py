# Generated by Django 5.1.5 on 2025-01-21 06:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0014_remove_customuser_profile"),
    ]

    operations = [
        migrations.DeleteModel(
            name="UserProfile",
        ),
    ]
