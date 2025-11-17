from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Count

from .models import IngredientInRecipe, Ingredients, Recipe, Tags

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ('username', 'email')


@admin.register(Ingredients)
class IngredientsAdmin(admin.ModelAdmin):
    search_fields = ('name',)


@admin.register(Tags)
class TagsAdmin(admin.ModelAdmin):
    pass


@admin.register(IngredientInRecipe)
class IngredientInRecipeAdmin(admin.ModelAdmin):
    pass


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    search_fields = ('name', 'author__username', 'author__email')
    list_filter = ('tags',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_favorites_count=Count('in_favorites'))

    def favorites_count(self, obj):
        return obj._favorites_count

    favorites_count.short_description = 'В избранном'
    favorites_count.admin_order_field = '_favorites_count'

    list_display = ('name', 'author', 'favorites_count')
    readonly_fields = ('favorites_count',)
