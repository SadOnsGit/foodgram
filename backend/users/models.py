from django.contrib.auth.models import AbstractUser
from django.db import models

from .constants import (
    MAX_EMAIL_LENGTH,
    MAX_FIRST_NAME_LENGTH,
    MAX_LAST_NAME_LENGTH,
    USERNAME_MAX_LENGTH,
)
from .validators import validate_username


class User(AbstractUser):
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]
    username = models.CharField(
        max_length=USERNAME_MAX_LENGTH,
        unique=True,
        validators=[validate_username],
        error_messages={
            "unique": ("Пользователь с таким username уже существует!"),
        },
    )
    first_name = models.CharField(
        max_length=MAX_FIRST_NAME_LENGTH,
    )
    last_name = models.CharField(
        max_length=MAX_LAST_NAME_LENGTH,
    )
    email = models.EmailField(
        max_length=MAX_EMAIL_LENGTH,
        unique=True,
        error_messages={
            "unique": ("Пользователь с таким email уже существует!"),
        },
    )
    avatar = models.ImageField(upload_to="users/", blank=True, null=True)


class Follow(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="following")
    following = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="followers"
    )

    def __str__(self):
        return f"{self.user} подписан на {self.following}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "following"], name="unique_user_following"
            ),
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_prevent_self_follow",
                check=~models.Q(user=models.F("following")),
            ),
        ]
