# Generated by Django 5.1.4 on 2024-12-08 16:33

import django.db.models.deletion
from django.db import migrations, models

import sortwai.waste.models


class Migration(migrations.Migration):
    dependencies = [
        ("waste", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="category",
            options={"ordering": ["name"]},
        ),
        migrations.AlterModelOptions(
            name="location",
            options={"ordering": ["name"]},
        ),
        migrations.AlterModelOptions(
            name="municipality",
            options={"ordering": ["name"]},
        ),
        migrations.AlterModelOptions(
            name="target",
            options={"ordering": ["name"]},
        ),
        migrations.AddField(
            model_name="location",
            name="municipality",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="waste.municipality",
            ),
        ),
        migrations.AddField(
            model_name="location",
            name="name",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="target",
            name="municipality",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="waste.municipality",
            ),
        ),
        migrations.AlterField(
            model_name="category",
            name="target",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="waste.target",
            ),
        ),
        migrations.AlterField(
            model_name="location",
            name="targets",
            field=models.ManyToManyField(blank=True, null=True, to="waste.target"),
        ),
        migrations.CreateModel(
            name="Document",
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
                (
                    "file",
                    models.FileField(
                        blank=True,
                        upload_to=sortwai.waste.models.document_file_filepath,
                    ),
                ),
                ("text", models.TextField(blank=True)),
                (
                    "municipality",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="waste.municipality",
                    ),
                ),
            ],
        ),
    ]
