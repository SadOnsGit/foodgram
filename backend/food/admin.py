from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count

from .models import IngredientInRecipe, Ingredients, Recipe, Tags

User = get_user_model()


@admin.register(User)
class UserAdmin(UserAdmin):
    search_fields = ("username", "email")


@admin.register(Ingredients)
class IngredientsAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    pass


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    pass


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    search_fields = ("name", "author__username", "author__email")
    list_filter = ("tags",)
    list_display = ("name", "author", "favorites_count")
    readonly_fields = ("favorites_count",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_favorites_count=Count("favorited_by"))

    @admin.display(description="В избранном", ordering="_favorites_count")
    def favorites_count(self, obj):
        return obj._favorites_count or 0
