# Generated by Django 5.1.5 on 2025-02-10 06:47

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0016_profile"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="booking",
            unique_together={("service", "booking_date")},
        ),
    ]
