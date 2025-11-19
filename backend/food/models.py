import random
import string

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .constants import SHORT_CODE_URLS_MAX_LENGTH

User = get_user_model()


class Tags(models.Model):
    name = models.CharField(max_length=32, unique=True, verbose_name="Название тега")
    slug = models.SlugField(max_length=32, unique=True, verbose_name="Слаг")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"


class Ingredients(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название")
    measurement_unit = models.CharField(
        max_length=2,
        verbose_name="Единица измерения",
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "measurement_unit"], name="unique_ingredient_with_unit"
            )
        ]


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recipe",
        verbose_name="Автор",
    )
    name = models.CharField(max_length=256, verbose_name="Название рецепта")
    image = models.ImageField(upload_to="recipe/", verbose_name="Картинка рецепта")
    text = models.TextField(verbose_name="Описание")
    tags = models.ManyToManyField(Tags, verbose_name="Тэг")
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name="Время приготовления (минут)",
        validators=[
            MinValueValidator(1),
            MaxValueValidator(
                1000, message="Время приготовления не может превышать 1000 минут."
            ),
        ],
        help_text="Укажите время в минутах (минимум 1 минута)",
    )
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

    def __str__(self):
        return self.name

    @staticmethod
    def generate_unique_short_code():
        chars = string.ascii_letters + string.digits
        while True:
            code = "".join(random.choices(chars, k=SHORT_CODE_URLS_MAX_LENGTH))
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
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(
                32767, message="Кол-во ингредиентов не может превышать 32767!"
            ),
        ],
    )

    def __str__(self):
        return (
            f"{self.ingredient.name} — {self.amount} {self.ingredient.measurement_unit}"
        )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты в рецепте"


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="favorited_by"
    )

    def __str__(self):
        return f"{self.user.username} - {self.recipe.name}"


class ShoppingListRecipe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="purchases")
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="shopping_cart_by"
    )

    def __str__(self):
        return f"{self.user.username} в корзине: {self.recipe.name}"
