from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
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
        error_messages={
            "unique": ("Пользователь с таким email уже существует!"),
        },
    )
    avatar = models.ImageField(
        upload_to='users/',
        blank=True,
        null=True
    )


class Follow(models.Model):
    user = models.ForeignKey(
        NewUser,
        on_delete=models.CASCADE,
        related_name='followers'
    )
    following = models.ForeignKey(
        NewUser,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'following'],
                name='unique_user_following'
            ),
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_prevent_self_follow",
                check=~models.Q(user=models.F("following")),
            ),
        ]