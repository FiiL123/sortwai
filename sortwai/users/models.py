from django.contrib.auth.models import AbstractUser
from django.db import models

from sortwai.waste.models import Municipality

# Create your models here.


class User(AbstractUser):
    municipality = models.ForeignKey(Municipality, on_delete=models.CASCADE)
