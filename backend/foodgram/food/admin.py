from django.contrib import admin

from .models import IngredientInRecipe, Ingredients, Recipe, Tags

admin.site.register((Tags, IngredientInRecipe, Ingredients, Recipe))
