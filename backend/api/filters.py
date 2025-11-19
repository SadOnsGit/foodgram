from django_filters.rest_framework import (
    BooleanFilter,
    CharFilter,
    FilterSet,
    MultipleChoiceFilter,
    NumberFilter,
)
from food.models import Ingredients, Recipe


class RecipeFilter(FilterSet):
    author = NumberFilter(field_name="author__id")
    tags = MultipleChoiceFilter(
        field_name="tags__slug",
        choices=[],
    )
    is_favorited = BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = BooleanFilter(method="filter_is_in_shopping_cart")

    def filter_is_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorited_by__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(shopping_cart_by__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ["author", "tags", "is_favorited", "is_in_shopping_cart"]


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr="icontains")

    class Meta:
        model = Ingredients
        fields = ["name"]
