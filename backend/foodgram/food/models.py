from django.contrib.auth import get_user_model
from django.db import models

from .constants import SHORT_CODE_URLS_MAX_LENGTH

User = get_user_model()


class Tags(models.Model):
    name = models.CharField(
        max_length=25, unique=True, verbose_name="Название тега"
    )
    slug = models.SlugField(unique=True, verbose_name="Слаг")


class Ingredients(models.Model):
    class UnitMeasurement(models.TextChoices):
        KG = "кг", "Киллограмм"
        MG = "мг", "Миллиграм"
        G = "г", "грамм"

    name = models.CharField(max_length=50, verbose_name="Ингредиенты")
    measurement_unit = models.CharField(
        max_length=2,
        choices=UnitMeasurement.choices,
        default=UnitMeasurement.G,
        verbose_name="Единица измерения",
    )


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipe",
        verbose_name="Автор",
    )
    name = models.CharField(max_length=150, verbose_name="Название рецепта")
    image = models.ImageField(
        upload_to="recipe/", verbose_name="Картинка рецепта"
    )
    text = models.TextField(verbose_name="Описание")
    tags = models.ManyToManyField(Tags, verbose_name="Тэг")
    cooking_time = models.IntegerField()
    short_code = models.CharField(
        max_length=SHORT_CODE_URLS_MAX_LENGTH,
        verbose_name="Короткий код",
        unique=True,
    )


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="recipe_ingredients"
    )
    ingredient = models.ForeignKey(Ingredients, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField()
