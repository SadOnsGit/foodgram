from django.contrib import admin

from .models import Tags, Ingredients, IngredientInRecipe, Recipe


admin.site.register(
    (Tags, IngredientInRecipe, Ingredients, Recipe)
)
