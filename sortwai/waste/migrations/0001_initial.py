# Generated by Django 5.1.4 on 2024-12-08 16:03

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Municipality",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=255)),
                ("short_name", models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="Target",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=255)),
                ("color", models.CharField(blank=True, max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name="Location",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("gps_lon", models.FloatField()),
                ("gps_lat", models.FloatField()),
                ("address", models.CharField(blank=True, max_length=255)),
                ("open_hours", models.CharField(blank=True, max_length=255)),
                ("phone_number", models.CharField(blank=True, max_length=255)),
                ("description", models.TextField(blank=True)),
                ("targets", models.ManyToManyField(to="waste.target")),
            ],
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=255)),
                ("image", models.ImageField(blank=True, null=True, upload_to="")),
                ("description", models.TextField(blank=True)),
                (
                    "target",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="waste.target"
                    ),
                ),
            ],
        ),
    ]
