import os
import secrets

from django.db import models

# Create your models here.


def document_file_filepath(instance: "Document", filename):
    _, ext = os.path.splitext(filename)
    rnd_str = secrets.token_hex(8)
    return f"documents/{instance.municipality_id}/{rnd_str}{ext}"


class Municipality(models.Model):
    name = models.CharField(max_length=255, blank=True)
    short_name = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Target(models.Model):
    name = models.CharField(max_length=255, blank=True)
    color = models.CharField(max_length=255, blank=True)
    municipality = models.ForeignKey(
        Municipality, on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.municipality})"


class Category(models.Model):
    municipality = models.ForeignKey(
        Municipality, on_delete=models.CASCADE, null=True, blank=True
    )
    name = models.CharField(max_length=255, blank=True)
    image = models.ImageField(null=True, blank=True)
    description = models.TextField(blank=True)
    do = models.TextField(blank=True)
    dont = models.TextField(blank=True)
    target = models.ForeignKey(Target, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Location(models.Model):
    name = models.CharField(max_length=255, blank=True)
    gps_lon = models.FloatField()
    gps_lat = models.FloatField()
    address = models.CharField(max_length=255, blank=True)
    open_hours = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    targets = models.ManyToManyField(Target, blank=True)
    municipality = models.ForeignKey(
        Municipality, on_delete=models.CASCADE, null=True, blank=True
    )
    show_on_main = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.gps_lat}-{self.gps_lon}"


class Document(models.Model):
    name = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to=document_file_filepath, blank=True)
    text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    municipality = models.ForeignKey(
        Municipality, on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        ordering = ["name", "created_at"]

    def __str__(self):
        return self.name


class BarCode(models.Model):
    code = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255, blank=True)
    manufacturer = models.CharField(max_length=255, blank=True)
    material = models.CharField(max_length=255, blank=True)
    material_number = models.IntegerField(default=0)
    material_type = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["material_number", "product_name"]

    def __str__(self):
        return self.code
