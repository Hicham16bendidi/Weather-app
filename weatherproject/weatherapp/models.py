from django.db import models
from django.contrib.auth.models import User
# Create your models here.


class UserPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferred_unit = models.CharField(max_length=2, choices=[('C', 'Celsius'), ('F', 'Fahrenheit')])
    favorite_location = models.CharField(max_length=100, blank=True, null=True)
