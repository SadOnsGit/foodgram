from django.db import models
from django.contrib.auth.models import AbstractUser

from .validators import validate_username
from .constants import USERNAME_MAX_LENGTH


class NewUser(AbstractUser):
    username = models.CharField(
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[validate_username],
        error_messages={
            "unique": ("Пользователь с таким username уже существует!"),
        },
    )
    email = models.EmailField(
        unique=True,
    )