from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    image = models.ImageField(
        'Аватарка',
        upload_to='users/',
        blank=True,
        null=True,
        help_text='Загрузите аватарку')
    birth_date = models.DateField(
        null=True,
        blank=True)
