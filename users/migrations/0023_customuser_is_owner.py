# Generated by Django 5.1.5 on 2025-02-24 12:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0022_salon_master_role_master_salon"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="is_owner",
            field=models.BooleanField(default=False),
        ),
    ]
