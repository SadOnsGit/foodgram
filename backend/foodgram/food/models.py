from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Tags(models.Model):
    name = models.CharField(
        max_length=25,
        unique=True,
    )
    slug = models.SlugField(
        unique=True,
    )


class Ingredients(models.Model):
    name = models.CharField(
        max_length=50,
    )
    unit = models.TextChoices()


class Receipts(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=150,
        verbose_name='Название рецепта'
    )
    image = models.ImageField(
        upload_to='media/receipts/'
        verbose_name='Картинка рецепта'
    )
    description = models.TextField(
        verbose_name='Описание'
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        verbose_name='Ингредиенты'
    )
    tag = models.ManyToManyField(
        Tags,
        verbose_name='Тэг'
    )