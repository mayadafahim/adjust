from django.db import models

from django.utils import timezone
from django.core.validators import MaxValueValidator, MinValueValidator
# Create your models here.

class Metric(models.Model):

    channel = models.CharField(max_length=100)
    country = models.CharField(max_length=2)
    date = models.DateTimeField(default=timezone.now)
    os = models.CharField(max_length=100)
    impressions = models.IntegerField()
    clicks = models.IntegerField()
    installs = models.IntegerField()
    spend = models.FloatField()
    revenue = models.FloatField()