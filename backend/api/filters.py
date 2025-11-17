from django_filters.rest_framework import (CharFilter, FilterSet,
                                           MultipleChoiceFilter, NumberFilter,
                                           BooleanFilter)

from food.models import Ingredients, Recipe


class RecipeFilter(FilterSet):
    author = NumberFilter(field_name="author__pk")
    tags = MultipleChoiceFilter(
        field_name="tags__slug",
        choices=[],
    )
    is_favorited = BooleanFilter(method="filter_is_favorited")
    is_in_shopping_cart = BooleanFilter(method="filter_is_in_shopping_cart")

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated or value == "1":
            return queryset.filter(in_favorites=user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_authenticated or value == "1":
            return queryset.filter(in_shopping_list=user)
        return queryset

    class Meta:
        model = Recipe
        fields = ["author", "tags", "is_favorited", "is_in_shopping_cart"]


class IngredientFilter(FilterSet):
    name = CharFilter(lookup_expr="icontains")

    class Meta:
        model = Ingredients
        fields = ["name"]
