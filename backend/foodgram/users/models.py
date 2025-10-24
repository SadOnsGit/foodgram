from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import USERNAME_MAX_LENGTH
from .validators import validate_username


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
