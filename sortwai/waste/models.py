from django.db import models

# Create your models here.


class Municipality(models.Model):
    name = models.CharField(max_length=255, blank=True)
    short_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class Target(models.Model):
    name = models.CharField(max_length=255, blank=True)
    color = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255, blank=True)
    image = models.ImageField(null=True, blank=True)
    description = models.TextField(blank=True)
    target = models.ForeignKey(Target, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Location(models.Model):
    gps_lon = models.FloatField()
    gps_lat = models.FloatField()
    address = models.CharField(max_length=255, blank=True)
    open_hours = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    targets = models.ManyToManyField(Target)

    def __str__(self):
        return f"{self.gps_lat}-{self.gps_lon}"
