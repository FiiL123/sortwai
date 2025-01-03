# Generated by Django 5.1.4 on 2024-12-08 16:37

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("waste", "0003_alter_location_targets"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="document",
            options={"ordering": ["name", "created_at"]},
        ),
        migrations.AddField(
            model_name="document",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
    ]
