import random
import string
from django.contrib.auth import get_user_model
from django.db import models

from .constants import SHORT_CODE_URLS_MAX_LENGTH

User = get_user_model()


class Tags(models.Model):
    name = models.CharField(
        max_length=25,
        unique=True,
        verbose_name="Название тега"
    )
    slug = models.SlugField(unique=True, verbose_name="Слаг")


class Ingredients(models.Model):
    class UnitMeasurement(models.TextChoices):
        KG = "кг", "Киллограмм"
        MG = "мг", "Миллиграм"
        G = "г", "грамм"

    name = models.CharField(max_length=50, verbose_name="Название")
    measurement_unit = models.CharField(
        max_length=2,
        choices=UnitMeasurement.choices,
        default=UnitMeasurement.G,
        verbose_name="Единица измерения",
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipe",
        verbose_name="Автор",
    )
    name = models.CharField(max_length=150, verbose_name="Название рецепта")
    image = models.ImageField(
        upload_to="recipe/",
        verbose_name="Картинка рецепта"
    )
    text = models.TextField(verbose_name="Описание")
    tags = models.ManyToManyField(Tags, verbose_name="Тэг")
    cooking_time = models.IntegerField()
    short_code = models.CharField(
        max_length=SHORT_CODE_URLS_MAX_LENGTH,
        verbose_name="Короткий код",
        unique=True,
        null=True,
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата публикации",
    )

    def save(self, *args, **kwargs):
        if not self.short_code:
            self.short_code = self.generate_unique_short_code()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_unique_short_code(length):
        chars = string.ascii_letters + string.digits
        while True:
            code = "".join(random.choices(chars, k=length))
            if not Recipe.objects.filter(short_code=code).exists():
                return code

    class Meta:
        ordering = ["-pub_date"]
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="recipe_ingredients"
    )
    ingredient = models.ForeignKey(Ingredients, on_delete=models.CASCADE)
    amount = models.PositiveSmallIntegerField()

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты в рецепте'


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipe_created_by'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='user_recipes'
    )


class ShoppingListRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cart_add_by'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='user_shopping_cart'
    )
