# Generated by Django 5.1.5 on 2025-02-21 11:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0020_alter_booking_unique_together"),
    ]

    operations = [
        migrations.AddField(
            model_name="master",
            name="email",
            field=models.EmailField(
                default="default@example.com", max_length=254, unique=True
            ),
        ),
    ]
